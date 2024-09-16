from flask import Flask, request, render_template, redirect, url_for, session
import os
import sqlite3
import bcrypt
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_API_KEY')
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'

SPOTIPY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:5000/callback'

sp_oauth = SpotifyOAuth(client_id = SPOTIPY_CLIENT_ID,
                        client_secret = SPOTIPY_CLIENT_SECRET,
                        redirect_uri = SPOTIPY_REDIRECT_URI,
                        scope = 'user-library-read user-top-read')

# ***ALL THE COMMENTS ARE database stuff if we wanted personalized profiles***
# conn = sqlite3.connect('user.db')

# c = conn.cursor()

# c.execute('''
#           CREATE TABLE IF NOT EXISTS users (
#           id INTEGER PRIMARY KEY AUTOINCREMENT,
#           username TEXT NOT NULL UNIQUE,
#           password TEXT NOT NULL
#           )
#           ''')

# conn.commit()
# conn.close()

# def createUser(username, password):
#     conn = sqlite3.connect('user.db')
#     c = conn.cursor()
#     returnVal = ""
    
#     hashedPassword = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

#     try:
#         c.execute('''
#                   INSERT INTO users (username, password)
#                   VALUES (?, ?)
#                   ''', (username, hashedPassword))
        
#         conn.commit()
#         returnVal = "User created successfully!"
#     except:
#         returnVal = "ERROR username already exists!"
    
#     conn.close()
#     return returnVal

# def verifyUser(username, password):
#     conn = sqlite3.connect('user.db')
#     c = conn.cursor()

#     c.execute('''
#               SELECT password FROM users WHERE username = ?
#               ''', (username,))
    
#     result = c.fetchone()

#     conn.close()

#     if result is None:
#         print("ERROR user not found!")
#         return False

#     storedPassword = result[0]

#     if (bcrypt.checkpw(password.encode('utf-8'), storedPassword)):
#         print("User verified!")
#         return True
#     else:
#         print("ERROR wrong password!")
#         return False

@app.route('/')
def home():
    token_info = get_token()

    if (not token_info):
        return redirect(url_for('login'))
    
    sp = spotipy.Spotify(auth=token_info['access_token'])

    user_profile = sp.current_user()

    return render_template('index.html', user=user_profile)

# @app.route('/register' , methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         return createUser(username, password)
#     return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)    

    # if request.method == 'POST':
    #     username = request.form['username']
    #     password = request.form['password']
    #     if verifyUser(username, password):
    #         return "Login succesful!"
    #     else:
    #         return "Login failed!"
    # return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('token_info', None)
    return redirect(url_for('home'))

@app.route('/callback')
def callback():
    code = request.args.get('code')
    tokenInfo = sp_oauth.get_access_token(code)
    session['token_info'] = tokenInfo

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