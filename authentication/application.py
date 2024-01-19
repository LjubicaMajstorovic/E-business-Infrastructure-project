import re
from flask import Flask, request, Response
from configuration import Configuration
from models import database, User
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from sqlalchemy import and_

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)

valid_email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'


def register_user(userType):
    if "forename" not in request.json or request.json["forename"] == "":
        return {"message": f"Field forename is missing."}, 400
    if "surname" not in request.json or request.json["surname"] == "":
        return {"message": f"Field surname is missing."}, 400
    if "email" not in request.json or request.json["email"] == "":
        return {"message": f"Field email is missing."}, 400
    if "password" not in request.json or request.json["password"] == "":
        return {"message": f"Field password is missing."}, 400

    if len(request.json["email"]) > 256 or not re.match(valid_email_regex, request.json["email"]):
        return {"message": "Invalid email."}, 400

    if len(request.json["password"]) > 256 or len(request.json["password"]) < 8:
        return {"message": "Invalid password."}, 400

    userInSystem = User.query.filter(User.email == request.json["email"]).first()
    if userInSystem:
        return {"message": "Email already exists."}, 400

    newUser = User(
        email=request.json["email"],
        password=request.json["password"],
        forename=request.json["forename"],
        surname=request.json["surname"],
        user_type=userType
    )

    database.session.add(newUser)
    database.session.commit()

    return Response(status=200)


@application.route("/register_customer", methods=["POST"])
def register_customer():
    return register_user("customer")


@application.route("/register_courier", methods=["POST"])
def register_courier():
    return register_user("courier")


@application.route("/login", methods=["POST"])
def login():
    if "email" not in request.json or request.json["email"] == "":
        return {"message": f"Field email is missing."}, 400
    if "password" not in request.json or request.json["password"] == "":
        return {"message": f"Field password is missing."}, 400

    if len(request.json["email"]) > 256 or not re.match(valid_email_regex, request.json["email"]):
        return {"message": f"Invalid email."}, 400

    user = User.query.filter(and_(User.email == request.json["email"], User.password == request.json["password"])).first()
    if not user:
        return {"message": f"Invalid credentials."}, 400

    additionalClaims = {
        "email": user.email,
        "user_type": user.user_type,
        "forename": user.forename,
        "surname": user.surname,
        "roles": [user.user_type]
    }

    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims)

    return {"accessToken": accessToken}, 200


@application.route("/delete", methods=["POST"])
@jwt_required()
def delete():
    email = get_jwt_identity()

    user = User.query.filter(User.email == email).first()
    if not user:
        return {"message": "Unknown user."}, 400

    database.session.delete(user)
    database.session.commit()

    return {}, 200




if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5000)
