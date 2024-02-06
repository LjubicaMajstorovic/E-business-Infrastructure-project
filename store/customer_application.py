import csv
from flask import Flask, request, Response
from configuration import Configuration, web3, owner, paymentContract, abi, bytecode
from models import database, Product, Category, OrderProduct, Order, CategoryProduct
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
import json
from web3.exceptions import ContractLogicError
from web3 import Account
from math import ceil

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

    if 'address' not in request.json or request.json['address'] == '':
        return {'message': 'Field address is missing.'}, 400

    if not web3.is_address(request.json['address']):
        return {'message': 'Invalid address.'}, 400

    transaction_hash = paymentContract.constructor(request.json['address'], ceil(price)).transact({
        "from": owner,
    })
    receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)

    order = Order(email=get_jwt_identity(), price=price, status="CREATED", contract=receipt.contractAddress)
    database.session.add(order)
    database.session.commit()
    for r in requests:
        ordPro = OrderProduct(productId=r["id"], orderId=order.id, quantity=r["quantity"])
        database.session.add(ordPro)
    database.session.commit()

    return {"id": order.id}, 200

@application.route('/status', methods=['GET'])
@jwt_required()
def status():
    claims = get_jwt()
    if "user_type" not in claims or claims["user_type"] != "customer":
        return {"msg": "Missing Authorization Header"}, 401

    #orders = Order.query.join(OrderProduct, OrderProduct.orderId == Order.id). \
    #    join(Product, Product.id == OrderProduct.productId).filter(Order.email == get_jwt_identity()).all()

    orders = Order.query.filter(Order.email == get_jwt_identity()).all()
    return {"orders": [{
        "products": [
            {
                "categories": [cat.name for cat in product.categories],
                "name": product.name,
                "price": product.price,
                "quantity": OrderProduct.query.filter(OrderProduct.orderId == order.id, OrderProduct.productId == product.id).first().quantity
            } for product in order.products],
        "price": order.price,
        "status": order.status,
        "timestamp": order.time.isoformat()
    } for order in orders]}, 200


@application.route('/delivered', methods=['POST'])
@jwt_required()
def delivered():
    claims = get_jwt()
    if "user_type" not in claims or claims["user_type"] != "customer":
        return {"msg": "Missing Authorization Header"}, 401
    if "id" not in request.json:
        return {"message": "Missing order id."}, 400
    if type(request.json["id"]) is not int:
        return {"message": "Invalid order id."}, 400
    order = Order.query.filter(Order.id == request.json["id"]).first()
    if int(request.json["id"]) <= 0 or order is None or (order is not None and order.status != "PENDING"):
        return {"message": "Invalid order id."}, 400
    if 'keys' not in request.json or request.json['keys'] == '':
        return {"message": "Missing keys."}, 400

    if 'passphrase' not in request.json or request.json['passphrase'] == '':
        return {"message": "Missing passphrase."}, 400

    keys = json.loads(request.json["keys"].replace("'", '"'))
    passphrase = request.json["passphrase"]

    try:
        address = web3.to_checksum_address(keys["address"])
        private_key = Account.decrypt(keys, passphrase).hex()
        contract = web3.eth.contract(address=order.contract, abi=abi, bytecode=bytecode)
        try:
            transaction = contract.functions.deliveryDone().build_transaction({
                "from": address,
                "nonce": web3.eth.get_transaction_count(address),
                "gasPrice": web3.eth.gas_price
            })
            signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
            transaction_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)
        except ContractLogicError as error:
            error = str(error)
            error = error[error.find("revert ") + 7:]
            return {"message": error}, 400
    except ValueError:
        return {"message": "Invalid credentials."}, 400


    order.status = "COMPLETE"
    database.session.commit()
    return {}, 200


@application.route('/pay', methods=['POST'])
@jwt_required()
def pay():
    claims = get_jwt()
    if "user_type" not in claims or claims["user_type"] != "customer":
        return {"msg": "Missing Authorization Header"}, 401
    if 'id' not in request.json:
        return {"message": "Missing order id."}, 400
    if type(request.json["id"]) is not int:
        return {"message": "Invalid order id."}, 400
    if request.json['id'] <= 0:
        return {"message": "Invalid order id."}, 400
    order = Order.query.filter(Order.id == request.json['id']).first()
    if not order:
        return {"message": "Invalid order id."}, 400

    if 'keys' not in request.json or request.json['keys'] == '':
        return {"message": "Missing keys."}, 400

    if 'passphrase' not in request.json or request.json['passphrase'] == '':
        return {"message": "Missing passphrase."}, 400

    keys = json.loads(request.json["keys"].replace("'", '"'))
    passphrase = request.json["passphrase"]

    try:
        address = web3.to_checksum_address(keys["address"])
        private_key = Account.decrypt(keys, passphrase).hex()
        contract = web3.eth.contract(address=order.contract, abi=abi, bytecode=bytecode)

        try:
            transaction = contract.functions.pay().build_transaction({
                "from": address,
                "value": ceil(order.price),
                "nonce": web3.eth.get_transaction_count(address),
                "gasPrice": web3.eth.gas_price
            })
            signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
            transaction_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)
        except ContractLogicError as error:
            if "Transfer already complete." not in str(error):
                return {"message": f"Insufficient funds."}, 400
            else:
                error = str(error)
                error = error[error.find("revert ") + 7:]
                return {"message": error}, 400

    except ValueError:
        return {"message": "Invalid credentials."}, 400
    return {}, 200



if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5002)
