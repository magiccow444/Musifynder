from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import sqlite3
import bcrypt
import spotipy
import requests
from spotipy.oauth2 import SpotifyOAuth

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

    return render_template('profile.html', user=user_profile)

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

if __name__ == '__main__':
    app.run(debug=True)