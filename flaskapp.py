from flask import Flask, render_template
app = Flask(__name__)

posts = [
    {
        'id': 1,
        'author': 'Your name',
        'title': 'Blog Post 1',
        'content': 'First post content',
        'date_posted': '4 March 2024'
    },
    {
        'id': 2,
        'author': 'Your name',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': '5 March 2024'
    }
]


# Route for the home page, which is where the blog posts will be shown
@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', posts=posts)


# Route for the about page
@app.route("/about")
def about():
    return render_template('about.html', title='About page')