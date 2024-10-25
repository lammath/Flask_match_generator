from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# Register blueprints
from auth import auth_bp
from players import players_bp
from matchups import matchups_bp
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(players_bp, url_prefix='/players')
app.register_blueprint(matchups_bp, url_prefix='/matchups')

if __name__ == "__main__":
    app.run(debug=True)
