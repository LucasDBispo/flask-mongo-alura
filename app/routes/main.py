import csv
import io
from datetime import datetime, timedelta, timezone

import jwt
from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from app import db
from app.decorators import token_required
from app.models.products import Product, ProductDBModel, UpdateProduct
from app.models.sales import Sale
from app.models.users import LoginPayload

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
def create_product(token):
    try:
        product = Product(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    result = db.products.insert_one(product.model_dump())
    # Lógica para criar o produto no banco de dados
    return jsonify(
        {"message": "Produto criado com sucesso!", "id": str(result.inserted_id)}
    ), 201


# RF4: O sistema deve permitir a visualização dos detalhes de um único produto
@main_bp.route("/products/<string:product_id>", methods=["GET"])
@token_required
def get_product_by_id(token, product_id):
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
@main_bp.route("/products/<string:product_id>", methods=["PUT"])
@token_required
def update_product(token, product_id):
    try:
        oid = ObjectId(product_id)
        update_data = UpdateProduct(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    update_result = db.products.update_one(
        {"_id": oid}, {"$set": update_data.model_dump(exclude_unset=True)}
    )

    if update_result.modified_count == 0:
        return jsonify({"error": "Produto com o id: {product_id} não encontrado"}), 404

    updated_product = db.products.find_one({"_id": oid})
    return jsonify(
        ProductDBModel(**updated_product).model_dump(by_alias=True, exclude_none=True)
    )


# RF6: O sistema deve permitir a exclusão de um único produto e produto existente
@main_bp.route("/products/<string:product_id>", methods=["DELETE"])
@token_required
def delete_product(token, product_id):
    try:
        oid = ObjectId(product_id)
    except Exception as e:
        return jsonify({"error": f"Erro ao consultar dados do produto: {e}"})

    delete_product = db.products.delete_one({"_id": oid})

    if delete_product.deleted_count == 0:
        return jsonify({"error": "Produto com o id: {product_id} não encontrado"}), 404

    return jsonify({"message": "Produto excluído com sucesso!"})


# RF7: O sistema deve permitir a importação de vendas através de um arquivo
@main_bp.route("/sales/upload", methods=["POST"])
@token_required
def upload_sales(token):
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400

    if file and file.filename.endswith(".csv"):
        csv_stream = io.StringIO(file.stream.read().decode("utf-8"), newline=None)
        csv_reader = csv.DictReader(csv_stream)

        sales_to_insert = []
        error = []

        for row_num, row in enumerate(csv_reader, start=1):
            try:
                sale_data = Sale(**row)

                sales_to_insert.append(sale_data.model_dump(mode="json"))
            except ValidationError as e:
                error.append(
                    f"Linha {row_num} com dados inválidos. Erros: {e.errors()}"
                )
            except Exception as e:
                error.append(f"Linha {row_num} com erro inesperado: {str(e)}")

        if sales_to_insert:
            try:
                db.sales.insert_many(sales_to_insert)
            except Exception as e:
                return jsonify(
                    {"error": f"Erro ao inserir vendas no banco de dados: {str(e)}"}
                ), 500
    return jsonify(
        {
            "message": "Upload realizado com sucesso",
            "vendas_importadas": len(sales_to_insert),
            "erros_encontrados": error,
        }
    ), 200


@main_bp.route("/")
def index():
    return jsonify({"message": "Bem vindo ao StyleSync!"})
