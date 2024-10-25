from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Match, Session, Player
from app import db
from datetime import datetime
import random

matchups_bp = Blueprint('matchups_bp', __name__)

# ELO rating calculation functions
def calculate_expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def get_k_factor(matches_played):
    return 40 if matches_played < 30 else 20

def update_elo(player_a, player_b, score_a, score_b):
    k_a = get_k_factor(player_a.matches_played)
    k_b = get_k_factor(player_b.matches_played)

    expected_a = calculate_expected_score(player_a.elo_rating, player_b.elo_rating)
    expected_b = 1 - expected_a

    if score_a > score_b:
        outcome_a, outcome_b = 1, 0
    elif score_b > score_a:
        outcome_a, outcome_b = 0, 1
    else:
        outcome_a, outcome_b = 0.5, 0.5  # Draw

    player_a.elo_rating += k_a * (outcome_a - expected_a)
    player_b.elo_rating += k_b * (outcome_b - expected_b)

    player_a.matches_played += 1
    player_b.matches_played += 1

    db.session.commit()

# Helper function to split players into tiers
def create_tiers(players, num_tiers):
    players = sorted(players, key=lambda x: x.elo_rating)
    tier_size = len(players) // num_tiers
    remainder = len(players) % num_tiers

    tiers = []
    start = 0
    for i in range(num_tiers):
        end = start + tier_size + (1 if i < remainder else 0)
        tiers.append(players[start:end])
        start = end

    return tiers

@matchups_bp.route("/create", methods=['GET', 'POST'])
@login_required
def create_matchups():
    if request.method == 'POST':
        match_type = request.form.get('match_type')
        num_fields = int(request.form.get('fields', 4))
        players = Player.query.filter_by(user_id=current_user.id).order_by(Player.elo_rating.desc()).all()
        
        # Create a new session
        session = Session(name=f"Session {datetime.now().strftime('%Y-%m-%d')}", date=datetime.utcnow())
        db.session.add(session)
        db.session.commit()

        # Split players into tiers
        num_tiers = random.randint(2, 4)
        tiers = create_tiers(players, num_tiers)

        matches = []
        matched_players = set()
        bench_players = []

        # Generate matches within each tier
        for tier in tiers:
            random.shuffle(tier)
            tier_matches = []

            if match_type == 'doubles':
                # Create doubles teams
                for i in range(0, len(tier) - 1, 2):
                    if i + 1 < len(tier):
                        team_a, team_b = tier[i], tier[i + 1]
                        tier_matches.append((team_a, team_b))
                        matched_players.update([team_a, team_b])
                    else:
                        # If odd number of players, add last to the next tier or bench
                        bench_players.append(tier[i])

            else:  # Singles matches
                for i in range(0, len(tier) - 1, 2):
                    if i + 1 < len(tier):
                        player_a, player_b = tier[i], tier[i + 1]
                        tier_matches.append((player_a, player_b))
                        matched_players.update([player_a, player_b])
                    else:
                        bench_players.append(tier[i])

            matches.extend(tier_matches)

        # Assign matches to fields
        fields = min(num_fields, len(matches))
        field_number = 1
        for match in matches[:fields]:
            if match_type == 'doubles' and len(match) == 2:
                team_a, team_b = match
                match_record = Match(
                    date=datetime.utcnow(),
                    session_id=session.id,
                    player_a1_id=team_a.id,
                    player_b1_id=team_b.id,
                    score_a=0, score_b=0
                )
            else:  # Singles match
                player_a, player_b = match
                match_record = Match(
                    date=datetime.utcnow(),
                    session_id=session.id,
                    player_a1_id=player_a.id,
                    player_b1_id=player_b.id,
                    score_a=0, score_b=0
                )
            db.session.add(match_record)
            field_number += 1

        # Commit all matches to the session
        db.session.commit()

        # Handle any remaining players as bench players
        if bench_players:
            bench_message = "Players on the bench:\n• " + "\n• ".join(player.name for player in bench_players)
            flash(bench_message, 'info')

        flash('Matchups created successfully!', 'success')
        return redirect(url_for('matchups_bp.view_matchups'))

    # If GET request, render the create matchups form
    return render_template('create_matchups.html', players=Player.query.filter_by(user_id=current_user.id).all())

@matchups_bp.route("/view")
@login_required
def view_matchups():
    sessions = Session.query.filter_by(user_id=current_user.id).all()
    return render_template('view_matchups.html', sessions=sessions)

@matchups_bp.route("/submit_scores", methods=['POST'])
@login_required
def submit_scores():
    session_id = request.form.get('session_id')
    session = Session.query.get(session_id)

    if not session:
        flash("Session not found.", "danger")
        return redirect(url_for('matchups_bp.view_matchups'))

    # Loop over submitted scores
    for match in session.matches:
        score_a = int(request.form.get(f"score_a_{match.id}", 0))
        score_b = int(request.form.get(f"score_b_{match.id}", 0))
        match.score_a, match.score_b = score_a, score_b

        # Determine and update winner
        if score_a > score_b:
            match.winner_id = match.player_a1_id
        elif score_b > score_a:
            match.winner_id = match.player_b1_id
        else:
            match.winner_id = None  # Handle draw if needed

        # Update ELO ratings
        player_a = Player.query.get(match.player_a1_id)
        player_b = Player.query.get(match.player_b1_id)
        update_elo(player_a, player_b, score_a, score_b)

    db.session.commit()
    flash("Scores submitted and ELO ratings updated successfully.", "success")
    return redirect(url_for('matchups_bp.view_matchups'))
