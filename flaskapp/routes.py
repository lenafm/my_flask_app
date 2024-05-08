from flask import render_template, flash, redirect, url_for, request
from flaskapp import app, db
from flaskapp.models import BlogPost, IpView, Day, UkData
from flaskapp.forms import PostForm
import datetime
import numpy as np
import pandas as pd
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go


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


def safe_divide(numerator, denominator):
    """Safely divide two numbers, handling None values."""
    if numerator is None or denominator is None or denominator == 0:
        return 0
    else:
        return numerator / denominator * 100

@app.route('/correlation_heatmap')
def correlation_heatmap():
    # Query data from the database
    data = UkData.query.all()
    df = pd.DataFrame([{
        'Conservative_Vote%': (entry.ConVote19 / entry.TotalVote19 * 100) if entry.TotalVote19 and entry.ConVote19 is not None else 0,
        'Turnout': entry.Turnout19 if entry.Turnout19 is not None else 0,
        'Population_Density': entry.c11PopulationDensity if entry.c11PopulationDensity is not None else 0,
        'Percentage_Retired': entry.c11Retired if entry.c11Retired is not None else 0,
        'Female%': entry.c11Female if entry.c11Female is not None else 0,
        'Fulltime_Student%': entry.c11FulltimeStudent if entry.c11FulltimeStudent is not None else 0,
        'Retired%': entry.c11Retired if entry.c11Retired is not None else 0,
        'House_Owned%': entry.c11HouseOwned if entry.c11HouseOwned is not None else 0,
        'Household_Married%': entry.c11HouseholdMarried if entry.c11HouseholdMarried is not None else 0
    } for entry in data])

    # Data cleaning
    df['Turnout'] = pd.to_numeric(df['Turnout'], errors='coerce')
    df.dropna(inplace=True)

    corr_matrix = df.corr()

    # Create a heatmap
    fig = px.imshow(corr_matrix, text_auto=True, labels=dict(color="Correlation Coefficient"),
                    title="Correlation Matrix of Census Data and Conservative Vote Share Data",)
    
    fig.update_layout(
        xaxis=dict(tickangle=-45),
        yaxis=dict(tickmode='linear'),
        coloraxis_colorbar=dict(title="Correlation Coefficient"),
        margin=dict(l=10, r=10, t=50, b=20)
    )
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('plot.html', title='Correlation Heatmap', graphJSON=graphJSON)




@app.route('/conservative_vs_retired_scatter')
def conservative_vs_retired_scatter():
    # Query data from the database
    data = UkData.query.all()
    df = pd.DataFrame([{
        'Region': entry.region,
        'ConstituencyName': entry.constituency_name,
        'ConVotePct': (entry.ConVote19 / entry.TotalVote19 * 100) if entry.TotalVote19 and entry.ConVote19 is not None else 0,
        'PercentageRetired': entry.c11Retired if entry.c11Retired is not None else 0
    } for entry in data])

    # Create a scatter plot
    fig = px.scatter(df, x='PercentageRetired', y='ConVotePct',
                     labels={
                         'ConVotePct': 'Conservative Vote Share (%)',
                         'PercentageRetired': 'Percentage of Retired People (%)'
                     },
                     title='Conservative Vote Share vs. Percentage of Retired People',
                     hover_data=['ConstituencyName'],  
                     color= 'Region')
    

    fig.update_layout(
        xaxis_title="Percentage of Retired People (%)",
        yaxis_title="Conservative Vote Share (%)",
        height=600
    )

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('plot.html', title='Scatter Plot: Vote Share vs. Retired Percentage', graphJSON=graphJSON)


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
