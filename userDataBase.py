from flask import Flask, request, render_template, redirect, url_for, session
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

@app.route('/')
def home():
    token_info = get_token()

    if (not token_info):
        return redirect(url_for('login'))
    
    sp = spotipy.Spotify(auth=token_info['access_token'])

    user_profile = sp.current_user()

    return render_template('index.html', user=user_profile)

@app.route('/login', methods=['GET', 'POST'])
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)    

@app.route('/logout')
def logout():

    session.pop('token_info', None)
    session.clear()

    session.modified = True

    return redirect(url_for('home'))

@app.route('/callback')
def callback():
    code = request.args.get('code')

    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info

    return redirect(url_for('home'))

def get_token():
    token_info = session.get('token_info', None)

    if (not token_info):
        return None
    
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info

    return token_info

if __name__ == '__main__':
    app.run(debug=True)