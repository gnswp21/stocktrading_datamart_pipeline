# spark session
from pyspark.sql import SparkSession
import sys
import pydeequ

spark = SparkSession.builder\
    .master("spark://spark-master:7077") \
    .config("spark.jars.excludes", pydeequ.f2j_maven_coord) \
    .appName("transfer_to_bigquery")\
    .getOrCreate()

spark.conf.set("parentProject", "spark2big")
spark.conf.set("credentialsFile", "myjars/spark2big-992917168560.json")

df_list = sys.argv[1:]
if df_list[0] == 'all':
    df_list = ['budget', 'trade', 'customer', 'stocks', 'stock_AAPL',
               'stock_AMZN', 'stock_GOOGL', 'stock_META', 'stock_MSFT']

for df_name in df_list:
    # load data from mysql
    df = spark.read.format('jdbc').options(
        url="jdbc:mysql://db-mysql:3306/strading",
        driver="com.mysql.cj.jdbc.Driver",
        dbtable=df_name,
        user="root",
        password="1234"
    ).load()

    # save data to bigquery
    df.write.format("bigquery")\
        .option("writeMethod", "direct") \
        .mode('overwrite') \
        .save("mydataset." + df_name)
