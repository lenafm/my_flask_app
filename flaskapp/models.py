from flaskapp import db
from datetime import datetime


# Defining a model for users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    posts = db.relationship('BlogPost', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.name}', '{self.id}'')"


# Defining a model for blog posts ('models' are used to represent tables in your database).
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    # author = db.Column(db.String(50), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"BlogPost('{self.title}', '{self.date_posted}')"