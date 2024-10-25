from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import Player
from app import db

players_bp = Blueprint('players_bp', __name__)

@players_bp.route("/players", methods=['GET', 'POST'])
@login_required
def manage_players():
    players = Player.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        name = request.form['name']
        elo = request.form.get('elo', 1500)
        player = Player(name=name, elo_rating=elo, user_id=current_user.id)
        db.session.add(player)
        db.session.commit()
        flash('Player added successfully!', 'success')
        return redirect(url_for('players_bp.manage_players'))
    return render_template('manage_players.html', players=players)
