from flask_sqlalchemy import SQLAlchemy
import datetime

database = SQLAlchemy()


class CategoryProduct(database.Model):
    __tablename__ = "category_product"
    id = database.Column(database.Integer, primary_key=True)
    product = database.Column(database.Integer, database.ForeignKey("products.id"), nullable=False)
    category = database.Column(database.Integer, database.ForeignKey("categories.id"), nullable=False)
    




class Category(database.Model):
    __tablename__ = "categories"
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(25), unique=True, nullable=False)
    products = database.relationship("Product", secondary=CategoryProduct.__table__, back_populates="categories")




class OrderProduct(database.Model):
    __tablename__ = "order_product"
    id = database.Column(database.Integer, primary_key=True)
    quantity = database.Column(database.Integer, nullable=False)
    productId = database.Column(database.Integer, database.ForeignKey("products.id"), nullable=False)
    orderId = database.Column(database.Integer, database.ForeignKey("orders.id"), nullable=False)


class Product(database.Model):
    __tablename__ = "products"
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(45), unique=True, nullable=False)
    price = database.Column(database.Float, nullable=False)
    categories = database.relationship("Category", secondary=CategoryProduct.__table__, back_populates="products")
    orders = database.relationship("Order", secondary=OrderProduct.__table__, back_populates="products")


class Order(database.Model):
    __tablename__ = "orders"
    id = database.Column(database.Integer, primary_key=True)
    status = database.Column(database.String(15), nullable=False)
    price = database.Column(database.Float, nullable=False)
    time = database.Column(database.DateTime, nullable=False, default=datetime.datetime.utcnow)
    email = database.Column(database.String(256), nullable=False)

    products = database.relationship("Product", secondary=OrderProduct.__table__, back_populates="orders")
