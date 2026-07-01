from functools import wraps

import jwt
from flask import current_app, jsonify, request


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({"message": "Token malformado"})
        if not token:
            return jsonify({"error": "Token não encontrado"})

        try:
            data = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms="HS256"
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token Expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401

        return f(data, *args, **kwargs)

    return decorated
