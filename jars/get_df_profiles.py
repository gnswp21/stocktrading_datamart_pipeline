from pyspark.sql import SparkSession
from pyspark.sql.types import StructField, StructType, StringType, IntegerType, TimestampType
import pydeequ
import sys
import time
from pydeequ.profiles import *

# spark session
spark = SparkSession.builder\
    .master("spark://spark-master:7077") \
    .appName("finance_data_etl")\
    .getOrCreate()


table_names = sys.argv[1:]  # 첫 번째 인자

for table_name in table_names:
    df = spark.read.format('jdbc').options(
        url="jdbc:mysql://db-mysql:3306/strading",
        driver="com.mysql.cj.jdbc.Driver",
        dbtable=table_name,
        user="root",
        password="1234"
    ).load()
    profiles = {}
    result = ColumnProfilerRunner(spark) \
        .onData(df) \
        .run()

    for col, profile in result.profiles.items():
        profiles[col] = {
            "dataType": str(profile.dataType),
            "completeness": profile.completeness,
            "approxDistinctCount": profile.approxDistinctCount,
            "mean": profile.mean,
            "stdDev": profile.stdDev,
            "min": profile.min,
            "max": profile.max,
        }

    profiles_df = spark.createDataFrame(profiles)
    # JSON 파일로 저장
    current_time = datetime.now().strftime("%Y-%m-%d_%H:%M")  # 현재 시간 (y-m-d_h:m 형식)
    output_path = f"output/profile/{table_name}_{current_time}_profile.json"
    profiles_df.coalesce(1).write.mode("overwrite").json(output_path)

    print(f"Column profiles saved to {output_path}")

# SparkSession 종료
spark.sparkContext._gateway.shutdown_callback_server()
spark.stop()
