from pyspark.sql import SparkSession
from pyspark.sql.types import StructField, StructType, StringType, IntegerType, TimestampType
import pydeequ
import sys
import time
from pydeequ.profiles import *
from pydeequ.checks import Check, ConstrainableDataTypes, CheckLevel
from pydeequ.verification import *

# spark session
spark = SparkSession.builder\
    .master("spark://spark-master:7077") \
    .appName("finance_data_etl")\
    .config("spark.jars.excludes", pydeequ.f2j_maven_coord) \
    .getOrCreate()


table_name = 'customer'

df = spark.read.format('jdbc').options(
    url="jdbc:mysql://db-mysql:3306/strading",
    driver="com.mysql.cj.jdbc.Driver",
    dbtable=table_name,
    user="root",
    password="1234"
).load()

# 데이터 품질 체크
check = Check(spark, CheckLevel.Warning, "Comprehensive Data Quality Check")
check = (
    check.isComplete("customer_id", hint="No nulls in id")  # id는 null 값이 없어야 함
    .isUnique("customer_id", hint="Unique id")  # id는 유일해야 함
    # id는 정수여야 함
    .hasDataType("customer_id", ConstrainableDataTypes.Integral, hint="id is an integer")

    .isContainedIn("sex", ["남자", "여자"])

    .isComplete("name", hint="No nulls in name")  # name은 null 값이 없어야 함
    # age는 18보다 크고 150보다 작음
    .satisfies("age > 18 and age < 150", constraintName="age is greater than 18")
    .hasDataType("age", ConstrainableDataTypes.Integral, hint="age is an integer")

    .isComplete("budget_id", hint="No nulls in budget_id")
    .isUnique("budget_id", hint="Unique budget_id")  # id는 유일해야 함
    # budget_id는 정수
    .hasDataType("budget_id", ConstrainableDataTypes.Integral, hint="budget_id is an integer")
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
