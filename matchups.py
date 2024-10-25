from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Match, Session, Player
from app import db

matchups_bp = Blueprint('matchups_bp', __name__)

@matchups_bp.route("/create_matchups", methods=['GET', 'POST'])
@login_required
def create_matchups():
    if request.method == 'POST':
        # Your matchups logic goes here
        flash('Matchups created successfully!', 'success')
        return redirect(url_for('dashboard'))
    players = Player.query.filter_by(user_id=current_user.id).all()
    return render_template('create_matchups.html', players=players)
