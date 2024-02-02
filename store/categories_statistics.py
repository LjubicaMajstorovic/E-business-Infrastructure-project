from pyspark.sql import SparkSession
from pyspark.sql.functions import sum as spark_sum, when
from pyspark.sql import functions as F
import os, json

builder = SparkSession.builder.appName("Category Statistics")


spark = builder.getOrCreate()


products = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://storedb:3306/store") \
    .option("dbtable", "store.products") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

categories = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://storedb:3306/store") \
    .option("dbtable", "store.categories") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

category_products = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://storedb:3306/store") \
    .option("dbtable", "store.category_product") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

order_products = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://storedb:3306/store") \
    .option("dbtable", "store.order_product") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

orders = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://storedb:3306/store") \
    .option("dbtable", "store.orders") \
    .option("user", "root") \
    .option("password", "root") \
    .load()


joined_df = (
    categories
    .join(category_products, categories["id"] == category_products["category"])
    .join(products, products["id"] == category_products["product"])
    .join(order_products, order_products["productId"] == products["id"])
    .join(orders, orders["id"] == order_products["orderId"])
)

# Define conditions for filtering and aggregation
conditions = (F.col("Order.status") == "COMPLETE")
quantity_sold = F.sum(F.when(conditions, order_products["quantity"]).otherwise(0)).alias("sold")

# Perform aggregation and group by Category.name
result_df = (
    joined_df
    .groupBy("Category.name")
    .agg(quantity_sold)
    .orderBy(quantity_sold.desc(), "Category.name")
)

# Collect results and convert to Python dictionary
result = {
    "statistics": [row["name"] for row in result_df.collect()]
}


with open("/app/store/product_statistics.txt", "w") as file:
    file.write(json.dumps(result))

spark.stop()
