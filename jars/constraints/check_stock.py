from pyspark.sql import SparkSession
from pyspark.sql.types import StructField, StructType, StringType, IntegerType, TimestampType
import pydeequ
import sys
import time
from pydeequ.profiles import *
from pydeequ.profiles import *
from pydeequ.checks import Check, ConstrainableDataTypes, CheckLevel
from pydeequ.verification import *

# spark session
spark = SparkSession.builder\
    .master("spark://spark-master:7077") \
    .appName("finance_data_etl")\
    .config("spark.jars.excludes", pydeequ.f2j_maven_coord) \
    .getOrCreate()


for table in sys.argv[1:]:
    table_name = table

    df = spark.read.format('jdbc').options(
        url="jdbc:mysql://db-mysql:3306/strading",
        driver="com.mysql.cj.jdbc.Driver",
        dbtable=table_name,
        user="root",
        password="1234"
    ).load()

    # 데이터 품질 체크
    check = Check(spark, CheckLevel.Warning,
                  "Comprehensive Data Quality Check")
    check = (
        # Datetime
        # Datetime에 null 값이 없어야 함
        check.isComplete("Datetime", hint="Datetime is complete")
        # Datetime은 문자열이어야 함
        .hasDataType("Datetime", ConstrainableDataTypes.String, hint="Datetime is a string")

        # Close
        .isComplete("Close", hint="Close is complete")  # Close에 null 값이 없어야 함
        # Close는 실수여야 함
        .hasDataType("Close", ConstrainableDataTypes.Fractional, hint="Close is a decimal")
        # Close는 Low와 High 사이여야 함
        .satisfies("Close >= Low AND Close <= High", constraintName="Close is within High and Low")

        # High
        .isComplete("High", hint="High is complete")  # High에 null 값이 없어야 함
        # High는 실수여야 함
        .hasDataType("High", ConstrainableDataTypes.Fractional, hint="High is a decimal")
        # High는 Low보다 크거나 같아야 함
        .satisfies("High >= Low", constraintName="High is greater than or equal to Low")

        # Low
        .isComplete("Low", hint="Low is complete")  # Low에 null 값이 없어야 함
        # Low는 실수여야 함
        .hasDataType("Low", ConstrainableDataTypes.Fractional, hint="Low is a decimal")

        # Open
        .isComplete("Open", hint="Open is complete")  # Open에 null 값이 없어야 함
        # Open은 실수여야 함
        .hasDataType("Open", ConstrainableDataTypes.Fractional, hint="Open is a decimal")

        # Volume
        # Volume에 null 값이 없어야 함
        .isComplete("Volume", hint="Volume is complete")
        # Volume은 음수가 아니어야 함
        .isNonNegative("Volume", hint="Volume is non-negative")
        # Volume은 정수여야 함
        .hasDataType("Volume", ConstrainableDataTypes.Integral, hint="Volume is an integer")

        # Company
        # Company에 null 값이 없어야 함
        .isComplete("Company", hint="Company is complete")

        # Ticker
        # Ticker에 null 값이 없어야 함
        .isComplete("Ticker", hint="Ticker is complete")
    )

    # 품질 검증 실행
    result = VerificationSuite(spark).onData(df).addCheck(check).run()
    checkResult_df = VerificationResult.checkResultsAsDataFrame(spark, result)
    checkResult_df.show()

    # save data to bigquery
    spark.conf.set("parentProject", "spark2big")
    spark.conf.set("credentialsFile", "myjars/spark2big-992917168560.json")
    checkResult_df.write.format("bigquery")\
        .option("writeMethod", "direct") \
        .mode('overwrite') \
        .save("mydataset.verifcation_" + table_name)


# SparkSession 종료
spark.sparkContext._gateway.shutdown_callback_server()
spark.stop()
