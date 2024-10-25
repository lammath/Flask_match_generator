from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Use your Heroku Postgres URL later
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Import blueprints from other modules
from auth import auth_bp
from players import players_bp
from matchups import matchups_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(players_bp)
app.register_blueprint(matchups_bp)

if __name__ == "__main__":
    app.run(debug=True)
