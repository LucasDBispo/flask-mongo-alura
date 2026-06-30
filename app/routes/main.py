from datetime import datetime, timedelta, timezone

import jwt
from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from app import db
from app.decorators import token_required
from app.models.products import ProductDBModel
from app.models.user import LoginPayload

# o blueprint organiza as rotas, o jsonify converte os dicts para json


main_bp = Blueprint("main_bp", __name__)


# RF1: O sistema deve permitir que um usuário se autentique para obter um token
@main_bp.route("/login", methods=["POST"])
def login():
    try:
        raw_data = request.get_json()
        user_data = LoginPayload(**raw_data)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    except Exception:
        return jsonify({"error": "Erro durante requisição dos dados"}), 500

    if user_data.username == "admin" and user_data.password == "supersecret":
        token = jwt.encode(
            {
                "user_id": user_data.username,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        return jsonify({"access_token": token}), 200

    return jsonify({"error": "Credenciais Inválidas"}), 401


# RF2: O sistema deve permitir listagem de todos os produtos
@main_bp.route("/products", methods=["GET"])
def get_products():
    products_cursor = db.products.find({})
    products_list = [
        ProductDBModel(**product).model_dump(by_alias=True, exclude_none=True)
        for product in products_cursor
    ]
    for products in products_cursor:
        products["_id"] = str(products["_id"])
        products_list.append(products)
    return jsonify(products_list)


# RF3: O sistema deve permitir a criação de um novo produto
@main_bp.route("/products", methods=["POST"])
@token_required
def create_product():
    return jsonify({"message": "Esta é a rota de criação de produto"})


# RF4: O sistema deve permitir a visualização dos detalhes de um único produto
@main_bp.route("/products/<string:product_id>", methods=["GET"])
def get_product_by_id(product_id):
    try:
        oid = ObjectId(product_id)
    except Exception as e:
        return jsonify({"error": f"Erro ao consultar dados do produto: {e}"})

    product = db.products.find_one({"_id": oid})

    if product:
        product["_id"] = str(product["_id"])
        return jsonify(product)
    else:
        return jsonify({"error": "Produto com o id: {product_id} não encontrado"})


# RF5: O sistema deve permitr a atualização de um único produto e produto existente
@main_bp.route("/products/<int:product_id>", methods=["PUT"])
def update_product():
    return jsonify(
        {"message": "Esta é a rota de atualização do produto de id {product_id}"}
    )


# RF6: O sistema deve permitir a exclusão de um único produto e produto existente
@main_bp.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product():
    return jsonify(
        {"message": "Esta é a rota de exclusão do produto de id {product_id}"}
    )


# RF7: O sistema deve permitir a importação de vendas através de um arquivo
@main_bp.route("/sales/upload", methods=["POST"])
def upload_sales():
    return jsonify({"message": "Esta é a rota de upload de um arquivo de vendas"})


@main_bp.route("/")
def index():
    return jsonify({"message": "Bem vindo ao StyleSync!"})
