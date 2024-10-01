from flask import Flask, request, render_template, redirect, url_for, session
from models import User, Track, Group, db
from spotipy.oauth2 import SpotifyOAuth
from sqlalchemy.exc import IntegrityError

import os
import sqlite3
import bcrypt
import spotipy
import requests
import random

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_API_KEY')
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session' 

app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'

SPOTIPY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:5000/callback'

sp_oauth = SpotifyOAuth(client_id = SPOTIPY_CLIENT_ID,
                        client_secret = SPOTIPY_CLIENT_SECRET,
                        redirect_uri = SPOTIPY_REDIRECT_URI,
                        scope = 'user-library-read user-top-read user-read-email user-read-private')

# ********** DATABASE **********

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///userDataBase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

def add_user_tracks(user_id, user_top_tracks):
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")
    
    for track in user_top_tracks['items']:
        track_name = track['name']
        artist_name = track['artists'][0]['name']

        existing_track = Track.query.filter_by(name=track_name, artist=artist_name, user_id=user_id).first()
        if not existing_track:
            new_track = Track(name=track_name, artist=artist_name, user_id=user_id)
            db.session.add(new_track)

    db.session.commit()

# ********** ROUTES **********

def is_token_valid():
    token_info = session.get('token_info', None)

    if (not token_info):
        return False
    
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
        
    return True

@app.route('/')
def home(): 
    return render_template('index.html')

@app.route('/profile')
def profile():
    if (not is_token_valid):
        return redirect(url_for('login'))   
    
    sp = spotipy.Spotify(auth=session.get('token_info')['access_token'])

    user_profile = sp.current_user()

    new_user = User(username=user_profile['display_name'], email=user_profile['email'])

    try:
        db.session.add(new_user)
        db.session.commit()
        print('User added')
    except IntegrityError:
        db.session.rollback()
        print('User already exists')    

    top_tracks_data = sp.current_user_top_tracks(limit=3, time_range='short_term')

    user = User.query.filter_by(username=user_profile['display_name']).first()

    add_user_tracks(user.id, top_tracks_data)

    group = Group.query.get(user.group_id)

    return render_template('profile.html', user=user_profile, group=group)

@app.route('/login')
def login():
    if (is_token_valid()):
        return redirect(url_for('profile'))

    else:
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)    

@app.route('/logout')
def logout():

    # session.pop('token_info', None)
    session.clear()

    session.modified = True

    return redirect(url_for('home'))

@app.route('/callback')
def callback():
    code = request.args.get('code')

    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info

    return redirect(url_for('home'))

@app.route('/top-tracks')
def top_tracks():
    if (not is_token_valid()):
        return redirect(url_for('login'))
    
    sp = spotipy.Spotify(auth=session.get('token_info')['access_token'])

    time_range = request.args.get('time_range', 'short_term')

    top_tracks_data = sp.current_user_top_tracks(limit=5, time_range=time_range)

    top_tracks = []
    for track in top_tracks_data['items']:
        track_info = {
            'name': track['name'],
            'artists': [artist['name'] for artist in track['artists']]
        }
        top_tracks.append(track_info)
    
    return render_template('topTracks.html', top_tracks=enumerate(top_tracks), time_range=time_range)

@app.route('/group-top-songs')
def group_top_songs():
    all_users = User.query.all()
    all_tracks = Track.query.all()

    random.shuffle(all_tracks)

    return render_template('groupTopSongs.html', tracks=all_tracks, users=all_users)

@app.route('/submit_guesses', methods=['POST']) 
def submit_guesses():
    correctGuesses = 0
    totalGuesses = 0

    for track_id, guesses_user_id in request.form.items():
        track = Track.query.get(int(track_id))

        if (track.user_id == int(guesses_user_id)):
            correctGuesses += 1
        totalGuesses += 1

    return f"You got {correctGuesses} out of {totalGuesses} correct!"

@app.route('/create_group', methods=['POST', 'GET'])
def create_group():
    if request.method == 'POST':
        group_name = request.form['group_name']
        new_group = Group(name=group_name)
        db.session.add(new_group)
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('createGroup.html')

@app.route('/join_group', methods=['POST', 'GET'])
def join_group():
    if request.method == 'POST':
        sp = spotipy.Spotify(auth=session.get('token_info')['access_token'])
        user_profile = sp.current_user()
        user = User.query.filter_by(username=user_profile['display_name']).first()

        group_id = request.form['group_id']
        user.group_id = group_id
        db.session.commit()
        return redirect(url_for('profile'))
    
    groups = Group.query.all()
    return render_template('joinGroup.html', groups=groups)

if __name__ == '__main__':
    app.run(debug=True)