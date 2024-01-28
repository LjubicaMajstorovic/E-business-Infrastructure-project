from flask import Flask, request, Response
from configuration import Configuration
from models import database, Product, Category, CategoryProduct, OrderProduct, Order
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import and_

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


@application.route("/orders_to_deliver", methods=["GET"])
@jwt_required()
def update():
    claims = get_jwt()
    if "user_type" not in claims or claims["user_type"] != "courier":
        return {"msg": "Missing Authorization Header"}, 401
    orders = Order.query.filter(Order.status == "CREATED").all()
    return {
        "orders": [
            {
                "id": order.id,
                "email": order.email
            }
        for order in orders]
    }, 200


@application.route("/pick_up_order", methods=["POST"])
@jwt_required()
def pick_up_order():
    claims = get_jwt()
    if "user_type" not in claims or claims["user_type"] != "courier":
        return {"msg": "Missing Authorization Header"}, 401
    if "id" not in request.json:
        return {"message": "Missing order id."}, 400
    if type(request.json["id"]) is not int:
        return {"message": "Invalid order id."}, 400
    order = Order.query.filter(Order.id == request.json["id"]).first()
    if int(request.json["id"]) <= 0 or order is None or (order is not None and order.status != "CREATED"):
        return {"message": "Invalid order id."}, 400

    order.status = "PENDING"
    database.session.commit()

    return {}, 200


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5003)