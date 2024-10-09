from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable = True)

    group = db.relationship('Group', backref=db.backref('members', lazy=True))

    correctGuesses = db.Column(db.Integer, unique=False, nullable=True)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)

    def __repr__ (self):
        return f"<Group {self.name}>"

class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable = False)
    artist = db.Column(db.String(120), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

    user = db.relationship('User', backref=db.backref('tracks', lazy=True))

    def __repr__(self):
        return f"<Track {self.name} by {self.artist}>"
    
