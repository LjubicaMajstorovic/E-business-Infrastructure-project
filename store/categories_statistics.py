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


result_df = categories \
    .join(category_products, categories['id'] == category_products['category'], 'left_outer') \
    .join(products, products['id'] == category_products['product'], 'left_outer') \
    .join(order_products, products['id'] == order_products['productId'], 'left_outer') \
    .join(orders, orders['id'] == order_products['orderId'], 'left_outer') \
    .groupBy(categories['name']) \
    .agg(
        F.sum(
            F.when(orders['status'] == 'COMPLETE', order_products['quantity']).otherwise(0)
        ).alias('sold')
    ) \
    .orderBy(F.desc('sold'), categories['name']).collect()


result = {
    "statistics": [row["name"] for row in result_df]
}



with open("/app/store/category_statistics.txt", "w") as file:
    file.write(json.dumps(result))

spark.stop()