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


table_name = 'trade'

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
    # 주문 ID는 null 값이 없어야 함
    check.isComplete("order_id", hint="No nulls in order_id")
    .isUnique("order_id", hint="Unique order_id")  # 주문 ID는 유일해야 함
    # 주문 ID는 정수여야 함
    .hasDataType("order_id", ConstrainableDataTypes.Integral, hint="order_id is an integer")

    # 고객 ID는 null 값이 없어야 함
    .isComplete("customer_id", hint="No nulls in customer_id")
    # 고객 ID는 정수여야 함
    .hasDataType("customer_id", ConstrainableDataTypes.Integral, hint="customer_id is an integer")

    # 주식 ID는 null 값이 없어야 함
    .isComplete("stock_id", hint="No nulls in stock_id")
    # 주식 ID는 정수여야 함
    .hasDataType("stock_id", ConstrainableDataTypes.Integral, hint="stock_id is an integer")

    # 거래 종류는 null 값이 없어야 함
    .isComplete("trade_type", hint="No nulls in transaction_type")
    .isContainedIn("trade_type", ["매수", "매도"])

    .isComplete("quantity", hint="No nulls in quantity")  # 주문량은 null 값이 없어야 함
    # 주문량은 음수가 아니어야 함
    .isNonNegative("quantity", hint="quantity is non-negative")
    # 주문량은 정수여야 함
    .hasDataType("quantity", ConstrainableDataTypes.Integral, hint="quantity is an integer")
    # 주문량은 0보다 커야 함
    .satisfies("quantity > 0", constraintName="quantity is greater than 0")

    # 주문 일시는 문자열이어야 함
    .hasDataType("order_datetime", ConstrainableDataTypes.String, hint="order_datetime is a string")
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
