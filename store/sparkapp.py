from flask import Flask
from flask import request, jsonify
import os
import subprocess
import json

application = Flask(__name__)


@application.route("/product_statistics", methods=["GET"])
def product_statistics():
    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/store/product_statistics.py"
    os.environ["SPARK_SUBMIT_ARGS"] = "--driver-class-path /app/store/mysql-connector-j-8.0.33.jar --jars /app/store/mysql-connector-j-8.0.33.jar"

    subprocess.check_output(["/template.sh"])
    with open("/app/store/product_statistics.txt", "r") as file:
        result = file.read()

    return result


@application.route("/category_statistics", methods=["GET"])
def category_statistics():
    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/store/category_statistics.py"
    os.environ[
        "SPARK_SUBMIT_ARGS"] = "--driver-class-path /app/store/mysql-connector-j-8.0.33.jar --jars /app/store/mysql-connector-j-8.0.33.jar"

    subprocess.check_output(["/template.sh"])
    with open("/app/store/category_statistics.txt", "r") as file:
        result = file.read()

    return result




if (__name__ == "__main__"):
    application.run(host="0.0.0.0", port=5004)
