from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def roleCheck(role):
    def innerRole(function):
        @wraps(function)
        def decorator(*arguments, **keywordArguments):
            verify_jwt_in_request()
            claims = get_jwt()
            if "user_type" not in claims or claims["user_type"] != role:
                return {"msg": "Missing Authorization Header"}, 401
            else:
                return function(*arguments, **keywordArguments)
        return decorator
    return innerRole