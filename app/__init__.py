from flask import Flask

from pymongo import MongoClient

db = None

def create_app():
    app = Flask(__name__)
   
    app.config.from_object('config.Config')
    global db 

    try:
        uri = app.config['MONGO_URI']
        client = MongoClient(uri)
        db = client.get_database()
    except Exception as e:
        print(f'Erro ao realizar a conexao com o banco de dados: {e}')

    from .routes.main import main_bp
    
    app.register_blueprint(main_bp)

    return app

