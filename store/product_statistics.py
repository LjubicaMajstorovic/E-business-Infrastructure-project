from pyspark.sql import SparkSession
from pyspark.sql.functions import sum as spark_sum, when
import json

builder = SparkSession.builder.appName("Product Statistics")


spark = builder.getOrCreate()


products = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://storedb:3306/store") \
    .option("dbtable", "store.products") \
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

order_products = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://storedb:3306/store") \
    .option("dbtable", "store.order_product") \
    .option("user", "root") \
    .option("password", "root") \
    .load()


product_statistics = order_products.join(products, order_products["productId"] == products["id"]).join(orders, order_products["orderId"] == orders["id"])\
    .groupBy(products["name"].alias("name")).agg(
        spark_sum(when(orders["status"] == 'COMPLETE', order_products["quantity"]).otherwise(0)).alias('sold'),
        spark_sum(when((orders["status"] == 'CREATED') | (orders["status"] == 'PENDING'), order_products["quantity"]).otherwise(
            0)).alias('waiting')
    ).collect()


result = {
    "statistics": [
        {
            "name": row["name"],
            "sold": int(row["sold"]),
            "waiting": int(row["waiting"])
        } for row in product_statistics
    ]
}

with open("/app/store/product_statistics.txt", "w") as file:
    file.write(json.dumps(result))

spark.stop()
