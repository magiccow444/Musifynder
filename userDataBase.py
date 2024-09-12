from flask import Flask, request, render_template
import sqlite3
import bcrypt

conn = sqlite3.connect('user.db')

c = conn.cursor()

c.execute('''
          CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT NOT NULL UNIQUE,
          password TEXT NOT NULL
          )
          ''')

conn.commit()
conn.close()

def createUser(username, password):
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    
    hashedPassword = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        c.execute('''
                  INSERT INTO users (username, password)
                  VALUES (?, ?)
                  ''', (username, hashedPassword))
        
        conn.commit()
        print("User created successfully!")
    except:
        print("ERROR username already exists!")
    
    conn.close()

def verifyUser(username, password):
    conn = sqlite3.connect('user.db')
    c = conn.cursor()

    c.execute('''
              SELECT password FROM users WHERE username = ?
              ''', (username,))
    
    result = c.fetchone()

    conn.close()

    if result is None:
        print("ERROR user not found!")
        return False

    storedPassword = result[0]

    if (bcrypt.checkpw(password.encode('utf-8'), storedPassword)):
        print("User verified!")
        return True
    else:
        print("ERROR wrong password!")
        return False
    
app = Flask(__name__)

@app.route('/register' , methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        createUser(username, password)
        return render_template('index.html')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verifyUser(username, password):
            return render_template('index.html')
        else:
            return "Login failed!"
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)