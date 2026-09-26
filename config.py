import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-mude-em-producao'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///trello.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False