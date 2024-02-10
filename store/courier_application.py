from flask import Flask, request
from configuration import Configuration, web3, owner, bytecode, abi
from models import database, Order
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from web3.exceptions import ContractLogicError
from decorator import roleCheck


application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


@application.route("/orders_to_deliver", methods=["GET"])
@roleCheck("courier")
@jwt_required()
def update():
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
@roleCheck("courier")
@jwt_required()
def pick_up_order():
    if "id" not in request.json:
        return {"message": "Missing order id."}, 400
    if type(request.json["id"]) is not int:
        return {"message": "Invalid order id."}, 400
    order = Order.query.filter(Order.id == request.json["id"]).first()
    if int(request.json["id"]) <= 0 or order is None or (order is not None and order.status != "CREATED"):
        return {"message": "Invalid order id."}, 400

    if 'address' not in request.json or request.json['address'] == '':
        return {'message': 'Missing address.'}, 400

    if not web3.is_address(request.json['address']):
        return {'message': 'Invalid address.'}, 400

    try:
        contract = web3.eth.contract(address=order.contract, abi=abi, bytecode=bytecode)
        hash_transaction = contract.functions.addCourier(request.json['address']).transact({
            "from": owner
        })
        receipt = web3.eth.wait_for_transaction_receipt(hash_transaction)
    except ContractLogicError as error:
        error = str(error)
        error = error[error.find("revert ") + 7:]
        return {"message": error}, 400

    order.status = "PENDING"
    database.session.commit()

    return {}, 200


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5003)