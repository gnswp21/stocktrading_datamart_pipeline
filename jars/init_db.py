from pyspark.sql import SparkSession
from pyspark.sql.types import StructField, StructType, StringType, IntegerType, TimestampType
import pydeequ

# spark session
spark = SparkSession.builder\
    .master("spark://spark-master:7077") \
    .appName("finance_data_etl")\
    .getOrCreate()

# get data
# budget data
budget_schema = StructType([
    StructField('budget_id', IntegerType(), nullable=False),
    StructField('budget', IntegerType(), nullable=False)]
)

df_budget = spark.read.format('csv')\
    .option('header', 'true')\
    .schema(budget_schema) \
    .load('input/budget.csv') \
    .withColumnRenamed("계좌id", "budget_id") \
    .withColumnRenamed("예산", "budget")

df_budget.show(5)

# customer data
customer_schema = StructType([
    StructField('customer_id', IntegerType(), nullable=False),
    StructField('name', StringType(), nullable=False),
    StructField('sex', StringType(), nullable=True),
    StructField('age', IntegerType(), nullable=True),
    StructField('budget_id', IntegerType(), nullable=True),]
)

df_customer = spark.read.format('csv')\
    .option('header', 'true')\
    .schema(customer_schema) \
    .load('input/customer.csv')


# trade data
trade_schema = StructType([
    StructField('order_id', IntegerType(), nullable=False),      # 주문 ID
    StructField('customer_id', IntegerType(), nullable=False),   # 고객 ID
    StructField('stock_id', IntegerType(), nullable=False),          # 주식
    StructField('trade_type', StringType(), nullable=False),     # 거래 종류
    StructField('quantity', IntegerType(), nullable=False),      # 주문량
    StructField('order_datetime', TimestampType(), nullable=False)  # 주문 일시
])
df_trade = spark.read.format('csv')\
    .option('header', 'true')\
    .schema(trade_schema) \
    .load('input/trade.csv')


# save data

df_budget.write.format("jdbc").options(
    url="jdbc:mysql://db-mysql:3306/strading",
    driver="com.mysql.cj.jdbc.Driver",
    dbtable="budget",
    user="root",
    password="1234"
).mode("overwrite").save()


df_customer.write.format("jdbc").options(
    url="jdbc:mysql://db-mysql:3306/strading",
    driver="com.mysql.cj.jdbc.Driver",
    dbtable="customer",
    user="root",
    password="1234"
).mode("overwrite").save()

df_trade.write.format("jdbc").options(
    url="jdbc:mysql://db-mysql:3306/strading",
    driver="com.mysql.cj.jdbc.Driver",
    dbtable="trade",
    user="root",
    password="1234"
).mode("overwrite").save()


# stock
# stocks
# MSFT
df_stocks = spark.read.format('csv')\
    .option('header', 'true')\
    .option('inferschema', 'true')\
    .load('input/stocks.csv')\
    .drop('_c0')

df_stocks.write.format("jdbc").options(
    url="jdbc:mysql://db-mysql:3306/strading",
    driver="com.mysql.cj.jdbc.Driver",
    dbtable="stocks",
    user="root",
    password="1234"
).mode("overwrite").save()


# AAPL
df_stock_AAPL = spark.read.format('csv')\
    .option('header', 'true')\
    .option('inferschema', 'true')\
    .load('input/stock/AAPL_data.csv')\
    .drop('_c0')

df_stock_AAPL.write.format("jdbc").options(
    url="jdbc:mysql://db-mysql:3306/strading",
    driver="com.mysql.cj.jdbc.Driver",
    dbtable="stock_AAPL",
    user="root",
    password="1234"
).mode("overwrite").save()

# AMZN
df_stock_AMZN = spark.read.format('csv')\
    .option('header', 'true')\
    .option('inferschema', 'true')\
    .load('input/stock/AMZN_data.csv')\
    .drop('_c0')

df_stock_AMZN.write.format("jdbc").options(
    url="jdbc:mysql://db-mysql:3306/strading",
    driver="com.mysql.cj.jdbc.Driver",
    dbtable="stock_AMZN",
    user="root",
    password="1234"
).mode("overwrite").save()


# GOOGL
df_stock_GOOGL = spark.read.format('csv')\
    .option('header', 'true')\
    .option('inferschema', 'true')\
    .load('input/stock/GOOGL_data.csv')\
    .drop('_c0')

df_stock_GOOGL.write.format("jdbc").options(
    url="jdbc:mysql://db-mysql:3306/strading",
    driver="com.mysql.cj.jdbc.Driver",
    dbtable="stock_GOOGL",
    user="root",
    password="1234"
).mode("overwrite").save()


# META
df_stock_META = spark.read.format('csv')\
    .option('header', 'true')\
    .option('inferschema', 'true')\
    .load('input/stock/META_data.csv')\
    .drop('_c0')

df_stock_META.write.format("jdbc").options(
    url="jdbc:mysql://db-mysql:3306/strading",
    driver="com.mysql.cj.jdbc.Driver",
    dbtable="stock_META",
    user="root",
    password="1234"
).mode("overwrite").save()

# MSFT
df_stock_MSFT = spark.read.format('csv')\
    .option('header', 'true')\
    .option('inferschema', 'true')\
    .load('input/stock/MSFT_data.csv')\
    .drop('_c0')

df_stock_MSFT.write.format("jdbc").options(
    url="jdbc:mysql://db-mysql:3306/strading",
    driver="com.mysql.cj.jdbc.Driver",
    dbtable="stock_MSFT",
    user="root",
    password="1234"
).mode("overwrite").save()

spark.stop()