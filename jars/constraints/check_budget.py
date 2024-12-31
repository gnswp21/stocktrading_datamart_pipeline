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


table_name = 'budget'

df = spark.read.format('jdbc').options(
    url="jdbc:mysql://db-mysql:3306/strading",
    driver="com.mysql.cj.jdbc.Driver",
    dbtable=table_name,
    user="root",
    password="1234"
).load()

df.show(5)
# 데이터 품질 체크
check = Check(spark, CheckLevel.Warning, "Comprehensive Data Quality Check")
check = (
    check.isComplete("budget_id", "No nulls in budget_id")
    .isComplete("budget", "No nulls in budget")
    .isUnique("budget_id", "Unique budget_id")
    .isNonNegative("budget", hint="Non-negative budget")
    .hasDataType("budget_id", ConstrainableDataTypes.Integral, hint="budget_id is an integer")
    .hasDataType("budget", ConstrainableDataTypes.Integral, hint="budget is an integer")
    .satisfies("budget < 100000000", "Valid budget range")
)

# 품질 검증 실행
result = VerificationSuite(spark).onData(df).addCheck(check).run()
checkResult_df = VerificationResult.checkResultsAsDataFrame(spark, result)
checkResult_df.show()

# save data to bigquery
spark.conf.set("parentProject", "spark2big")
spark.conf.set("credentialsFile", "myjars/spark2big-323e6547b0e3.json")
checkResult_df.write.format("bigquery")\
    .option("writeMethod", "direct") \
    .mode('overwrite') \
    .save("mydataset.verifcation_" + table_name)


# SparkSession 종료
spark.sparkContext._gateway.shutdown_callback_server()
spark.stop()
