from flask import Flask
import os
from app.config import TestingConfig, Config
from app.extensions import db
from app.routes.user_routes import user_bp

def create_app(isTest = False):
    app = Flask(__name__)

    # Load the configuration
    app.config.from_object(TestingConfig if isTest else Config)

    # Initialize the database
    db.init_app(app)

    # Register the blueprints
    app.register_blueprint(user_bp, url_prefix='/users')
    # app.register_blueprint(chat_bp, url_prefix='/chats')

    return app
