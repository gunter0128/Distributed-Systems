from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
import secrets
import pymysql

# 註冊 PyMySQL 作為 MySQLdb
pymysql.install_as_MySQLdb()

# 載入環境變量
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # 數據庫配置
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    
    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
        print("錯誤: 缺少必要的數據庫配置。請檢查 .env 文件。")
        return None, None
    
    # 構建 MySQL 連接 URL
    # MySQL連接格式：mysql://username:password@host:port/database_name
    database_url = f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # 設置 Flask-SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 設置安全密鑰
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
    
    # 初始化 SQLAlchemy
    db = SQLAlchemy(app)
    
    return app, db

# 使用示例
if __name__ == '__main__':
    app, db = create_app()
    if app:
        app.run(debug=True)
    else:
        print("應用程序初始化失敗")