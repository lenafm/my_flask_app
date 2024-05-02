from flask import render_template, flash, redirect, url_for, request
from flaskapp import app, db
from flaskapp.models import BlogPost, IpView, Day
from flaskapp.forms import PostForm
import datetime

import pandas as pd
import json
import plotly
import plotly.express as px

# Import the UkData model from models.py
from flaskapp.models import UkData


# Route for the home page, which is where the blog posts will be shown
@app.route("/")
@app.route("/home")
def home():
    # Querying all blog posts from the database
    posts = BlogPost.query.all()
    return render_template('home.html', posts=posts)


# Route for the about page
@app.route("/about")
def about():
    return render_template('about.html', title='About page')


# Route to where users add posts (needs to accept get and post requests)
@app.route("/post/new", methods=['GET', 'POST'])
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = BlogPost(title=form.title.data, content=form.content.data, user_id=1)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form)


@app.route('/dashboard')
def dashboard():
    days = Day.query.all()
    df = pd.DataFrame([{'Date': day.id, 'Page views': day.views} for day in days])
    fig = px.bar(df, x='Date', y='Page views')
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('dashboard.html', title='Page views per day', graphJSON=graphJSON)


@app.route("/first_chart")
def first_chart():
    # Query the UK parliamentary data from the database
    data = UkData.query.all()

    # Create a DataFrame from the queried data
    df = pd.DataFrame([{
        'Constituency': row.constituency_name,
        'Turnout19': row.Turnout19,
        'ConVote19': row.ConVote19,
    } for row in data])
    
    # Create a scatter plot using Plotly Express
    fig = px.scatter(df, x='Turnout19', y='ConVote19',
                     hover_name='Constituency',
                     labels={'Turnout19': 'Turnout Rate (%)', 'ConVote19': 'Conservative Votes'})

    # Add title and axis labels
    fig.update_layout(title='Turnout Rate vs. Conservative Votes',
                      xaxis_title='Turnout Rate (%)',
                      yaxis_title='Conservative Votes')
    print(fig)
    # Convert the visualization to JSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Render the template with the visualization
    return render_template('first_chart.html', graphJSON=graphJSON)



# Route for the second chart
@app.route("/second_chart")
def second_chart():
    # Query the UK parliamentary data from the database
    data = UkData.query.all()

    # Create a DataFrame from the queried data
    df = pd.DataFrame([{
        'Region': row.region,
        'TotalVote19': row.TotalVote19,
    } for row in data])
    # Create a bar chart using Plotly Express
    fig = px.bar(df, x='Region', y='TotalVote19',
                labels={'Region': 'Region', 'TotalVote19': 'Total Votes'},
                title='Total Votes by Region')
    print(fig)

    # Convert the visualization to JSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Render the template with the visualization
    return render_template('second_chart.html', graphJSON=graphJSON)


@app.before_request
def before_request_func():
    day_id = datetime.date.today()  # get our day_id
    client_ip = request.remote_addr  # get the ip address of where the client request came from

    query = Day.query.filter_by(id=day_id)  # try to get the row associated to the current day
    if query.count() > 0:
        # the current day is already in table, simply increment its views
        current_day = query.first()
        current_day.views += 1
    else:
        # the current day does not exist, it's the first view for the day.
        current_day = Day(id=day_id, views=1)
        db.session.add(current_day)  # insert a new day into the day table

    query = IpView.query.filter_by(ip=client_ip, date_id=day_id)
    if query.count() == 0:  # check if it's the first time a viewer from this ip address is viewing the website
        ip_view = IpView(ip=client_ip, date_id=day_id)
        db.session.add(ip_view)  # insert into the ip_view table

    db.session.commit()  # commit all the changes to the database

