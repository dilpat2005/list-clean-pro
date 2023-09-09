from flask import Flask
from flask_login import LoginManager
from config import config

app = Flask(__name__)
app.secret_key = 'your_secret_key'

db_params = config()

login_manager = LoginManager(app)
