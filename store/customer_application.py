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


@application.route('/order', methods=['POST'])
@jwt_required()
def order():
    claims = get_jwt()
    if "user_type" not in claims or claims["user_type"] != "customer":
        return {"msg": "Missing Authorization Header"}, 401
    if "requests" not in request.json:
        return {"message": "Field requests is missing."}, 400
    requests = request.json["requests"]
    num = 0
    price = 0
    for r in requests:
        if "id" not in r:
            return {"message": f"Product id is missing for request number {num}."}, 400
        if "quantity" not in r:
            return {"message": f"Product quantity is missing for request number {num}."}, 400
        if type(r["id"]) is not int:
            return {"message": f"Invalid product id for request number {num}."}, 400
        if r["id"] <= 0:
            return {"message": f"Invalid product id for request number {num}."}, 400
        if type(r["quantity"]) is not int:
            return {"message": f"Invalid product quantity for request number {num}."}, 400
        if r["quantity"] <= 0:
            return {"message": f"Invalid product quantity for request number {num}."}, 400
        product = Product.query.filter(Product.id == r["id"]).first()
        if product is None:
            return {"message": f"Invalid product for request number {num}."}, 400
        price += r["quantity"]*product.price
        num += 1

    price = 0
    products = list()
    order = Order(email=get_jwt_identity(), price=price, status="created")
    database.session.add(order)
    database.session.commit()
    for r in requests:
        ordPro = OrderProduct(productId=r["id"], orderId=order.id, quantity=r["quantity"])
        database.session.add(ordPro)
    database.session.commit()

    return {"id": order.id}, 200







if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5002)
