from flask import render_template, flash, redirect, url_for, request
from flaskapp import app, db
from flaskapp.models import BlogPost, IpView, Day
from flaskapp.forms import PostForm
import datetime

import pandas as pd
import json
import plotly
import plotly.express as px

from .models import UkData
import plotly.graph_objs as go



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


# Route to the dashboard page
@app.route('/dashboard')
def dashboard():
    days = Day.query.all()
    df = pd.DataFrame([{'Date': day.id, 'Page views': day.views} for day in days])

    fig = px.bar(df, x='Date', y='Page views')

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('dashboard.html', title='Page views per day', graphJSON=graphJSON)


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

@app.route('/student_engagement')
def student_engagement():
    # Assuming UkData model and necessary imports are defined
    data = UkData.query.with_entities(
        UkData.constituency_name,
        UkData.c11FulltimeStudent,
        UkData.Turnout19
    ).all()

    df = pd.DataFrame(data, columns=['Constituency', 'Percentage of Full-Time Students', 'Voter Turnout 2019'])
    # Create a scatter plot using Plotly with a vibrant, yet elegant color scheme
    fig = px.scatter(df, x='Percentage of Full-Time Students', y='Voter Turnout 2019',
                     hover_data=['Constituency'], title='Impact of Full-Time Student Population on Voter Turnout',
                     color_continuous_scale=px.colors.sequential.Magma)  # Using Viridis color scale

# Customize the appearance
    fig.update_layout(
        xaxis_title="Percentage of Full-Time Students",
        yaxis_title="Voter Turnout (%)",
        plot_bgcolor="white",
        paper_bgcolor="lightgrey"  # Adding a subtle background color to the plot area
    )
    fig.update_traces(marker=dict(size=12,
                                  line=dict(width=2,
                                            color='DarkSlateGrey')),
                      selector=dict(mode='markers'))

    # Convert the figure to JSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Pass the JSON to the HTML template
    return render_template('student_engagement.html', title='Student Engagement Analysis', graphJSON=graphJSON)
@app.route('/student_labour_support')
def student_labour_support():
    # Fetch data
    data = UkData.query.with_entities(
        UkData.constituency_name,
        UkData.c11FulltimeStudent,
        UkData.LabVote19,
        UkData.TotalVote19
    ).all()
    df = pd.DataFrame(data, columns=['Constituency', 'Percentage of Full-Time Students', 'Labour Votes in 2019', 'Total Votes 2019'])
    df['Labour Vote Percentage'] = (df['Labour Votes in 2019'] / df['Total Votes 2019']) * 100

    # Create a scatter plot with manual colors and sizes
    df['Color'] = df['Labour Vote Percentage'].apply(lambda x: 'red' if x > 50 else 'blue')
    df['Size'] = df['Labour Vote Percentage'].apply(lambda x: 20 if x > 50 else 10)

    fig = go.Figure(data=[go.Scatter(
        x=df['Percentage of Full-Time Students'],
        y=df['Labour Vote Percentage'],
        text=df['Constituency'],
        mode='markers',
        marker=dict(
            color=df['Color'],  # Custom colors
            size=df['Size']      # Custom sizes
        )
    )])

    fig.update_layout(
        title='Full-Time Student Percentage vs Labour Vote Percentage in 2019',
        xaxis_title="Percentage of Full-Time Students",
        yaxis_title="Labour Vote Percentage",
        plot_bgcolor="white"
    )

    # Convert the figure to JSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Pass the JSON to the HTML template
    return render_template('student_labour_support.html', title='Custom Student and Labour Support Analysis', graphJSON=graphJSON)