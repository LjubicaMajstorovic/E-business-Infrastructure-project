from datetime import timedelta
import os


class Configuration:
    DATABASE_URL = os.environ["DATABASE_URL"] if "DATABASE_URL" in os.environ else "localhost"
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{DATABASE_URL}/authentication"

    JWT_SECRET_KEY = "JWT_SECRET_DEV_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
