from dotenv import load_dotenv
import os




class Config:
    load_dotenv('.env', override=True)
    SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI')
    DB_CONNECTION=os.getenv('DB_CONNECTION')
    DB_CONNECTION_GLOBAL=os.getenv('DB_CONNECTION_GLOBAL')
    IMAGE_ICONS_GLOBAL_URL=os.getenv('IMAGE_ICONS_GLOBAL_URL')
    SECRET=os.getenv('SECRET')
    JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY')
    IMAGE_ICONS_URL=os.getenv('IMAGE_ICONS_URL')
    UPLOAD_FOLDER=os.getenv('UPLOAD_FOLDER')
    POSTGRES_DB=os.getenv('POSTGRES_DB')
    POSTGRES_USER=os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD=os.getenv('POSTGRES_PASSWORD')
    POSTGRES_HOST=os.getenv('POSTGRES_HOST')
    POSTGRES_PORT=os.getenv('POSTGRES_PORT')