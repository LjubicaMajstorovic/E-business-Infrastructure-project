import csv
from flask import Flask, request, Response
from configuration import Configuration
from models import database, Product, Category, OrderProduct, Order, CategoryProduct
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import and_, or_

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)




@application.route('/search', methods=['GET'])
@jwt_required()
def search():
    claims = get_jwt()
    if "user_type" not in claims or claims["user_type"] != "customer":
        return {"msg": "Missing Authorization Header"}, 401

    products = Product.query
    categories = Category.query

    if "name" in request.args:
        categories = categories.join(
            CategoryProduct, Category.id == CategoryProduct.category
        ).join(
            Product, CategoryProduct.product == Product.id
        ).filter(Product.name.like(f"%{request.args['name']}%"))

        products = products.filter(Product.name.like(f"%{request.args['name']}%"))
    if "category" in request.args:

        products = products.join(
            CategoryProduct, Product.id == CategoryProduct.product
        ).join(
            Category, CategoryProduct.category == Category.id
        ).filter(Category.name.like(f"%{request.args['category']}%"))

        categories = categories.filter(Category.name.like(f"%{request.args['category']}%"))

    products = products.all()
    categories = categories.all()

    return {"categories": [category.name for category in categories],
            "products": [{
                "categories": [category.name for category in product.categories],
                "id": product.id,
                "name": product.name,
                "price": product.price
            } for product in products]}, 200





if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5002)
