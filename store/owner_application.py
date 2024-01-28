import csv, io
from flask import Flask, request, Response
from configuration import Configuration
from models import database, Product, Category, CategoryProduct
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import and_

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)




@application.route("/update", methods=["POST"])
@jwt_required()
def update():
    claims = get_jwt()
    email = get_jwt_identity()
    if "user_type" not in claims or claims["user_type"] != "owner":
        return {"msg": "Missing Authorization Header"}, 401

    if "file" not in request.files:
        return {"message": "Field file is missing."}, 400

    file = request.files["file"].stream.read().decode()
    reader = file.split("\n")
    i = 0
    products = Product.query.all()
    products = [product.name for product in products]
    for row in reader:
        row = row.split(",")
        if len(row) != 3:
            return {"message": f"Incorrect number of values on line {i}."}, 400
        try:
            if float(row[2]) <= 0:
                return {"message": f"Incorrect price on line {i}."}, 400
        except ValueError:
            return {"message": f"Incorrect price on line {i}."}, 400
        if row[1] in products:
            return {"message": f"Product {row[1]} already exists."}, 400
        else:
            products.append(row[1])
        i += 1

    all_categories = Category.query.all()
    all_categories = [category.name for category in all_categories]

    for row in reader:
        row = row.split(",")
        category_names = row[0].split('|')
        categoriesProducts = list()

        for category in category_names:

            if category not in all_categories:
                all_categories.append(category)
                category_ready = Category(name=category)
                database.session.add(category_ready)
                database.session.commit()
            else:
                category_ready = Category.query.filter(Category.name.like(category)).first()

            catPro = CategoryProduct(category=category_ready.id)
            categoriesProducts.append(catPro)

        product = Product(name=row[1], price=row[2])
        database.session.add(product)
        database.session.commit()
        for i in range(len(categoriesProducts)):
            categoriesProducts[i].product = product.id

        database.session.add_all(categoriesProducts)
    database.session.commit()



    return {}, 200


@application.route("/product_statistics", methods=["GET"])
@jwt_required()
def product_statistics():
    claims = get_jwt_identity()
    if claims["user_type"] != "owner":
        return {"msg": "Missing Authorization Header"}, 401
    return {}, 200






if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5001)
