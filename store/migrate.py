from configuration import Configuration
from flask_migrate import Migrate, init, migrate, upgrade
from models import database
from sqlalchemy_utils import create_database, database_exists
from flask import Flask

application = Flask(__name__)
application.config.from_object(Configuration)

if not database_exists(application.config["SQLALCHEMY_DATABASE_URI"]):
    create_database(application.config["SQLALCHEMY_DATABASE_URI"])

database.init_app(application)
migration = Migrate(application, database)
with application.app_context() as context:
    init()
    migrate(message="Inicijalna migracija.")
    upgrade()
