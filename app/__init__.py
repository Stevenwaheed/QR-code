
# from app.blueprints.auth.services import User
from flask import Flask
from config.config import Config
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from flask_cors import CORS
from db.database import db


def create_app():
    
    app = Flask(__name__)
    # app.secret_key = Config.SECRET
    # app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
    # app.config['SQLALCHEMY_DATABASE_URI'] = Config.DB_CONNECTION_GLOBAL
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.DB_CONNECTION
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 48 * 60 * 60
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 30 * 24 * 60 * 60
    app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY

    JWTManager(app)
    app.config['SWAGGER'] = {
        'title': 'QR Code Generation API',
        'uiversion': 3,
        'securityDefinitions': {
            'bearerAuth': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': 'Enter your Bearer token in the format: Bearer <token>'
            }
        },
        'security': [
            {
                'bearerAuth': []
            }
        ]
    }
 
    Swagger(app)
    
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "allow_headers": [
                "Content-Type", 
                "Authorization", 
                "Access-Control-Allow-Credentials"
            ],
            "supports_credentials": True,
            "methods": ["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"]
        }
    })


    from .blueprints import register_routes
    register_routes(app)

    
    db.init_app(app)
    Migrate(app, db)

    return app
