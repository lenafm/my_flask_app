from flask import render_template, flash, redirect, url_for, request
from flaskapp import app, db
from flaskapp.models import BlogPost, IpView, Day, UkData
from flaskapp.forms import PostForm
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import json
import plotly
import plotly.express as px
import numpy as np



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


@app.route('/student-labour-votes-scatter')
def student_labour_votes_scatter():
    data = UkData.query.with_entities(UkData.constituency_name, UkData.c11FulltimeStudent, UkData.LabVote19).all()
    df = pd.DataFrame(data, columns=['Constituency', 'Full-time Student (%)', 'Labour Party Votes'])
    fig = px.scatter(df, x='Full-time Student (%)', y='Labour Party Votes', title='Percentage of Full-time Students vs. Labour Party Votes in UK Constituencies', color='Labour Party Votes', color_continuous_scale='RdYlBu')
    fig.update_xaxes(title='Percentage of Full-time Students', tickfont=dict(size=14), title_font=dict(size=18))
    fig.update_yaxes(title='Labour Party Votes', tickfont=dict(size=14), title_font=dict(size=18))
    fig.update_layout(
        margin=dict(l=50, r=50, t=100, b=100),
        autosize=False,
        width=1500,
        height=800,
        plot_bgcolor='rgba(240, 240, 240, 0.9)',
        paper_bgcolor='rgba(240, 240, 240, 0.9)',
        font=dict(size=16),
    )
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('student_labour_votes_scatter.html', title='Percentage of Full-time Students vs. Labour Party Votes', graphJSON=graphJSON)


@app.route('/heatmap_voting_patterns/<country>')
def heatmap_voting_patterns(country):

    data = UkData.query.filter_by(country=country).all()

    df = pd.DataFrame([{
        'Constituency': d.constituency_name,
        'Region': d.region,
        'Turnout 2019': d.Turnout19,
        'Conservative Votes': d.ConVote19,
        'Labour Votes': d.LabVote19,
        'Lib Dem Votes': d.LDVote19,
        'SNP Votes': d.SNPVote19,
        'Plaid Cymru Votes': d.PCVote19,
        'UKIP Votes': d.UKIPVote19,
        'Green Votes': d.GreenVote19,
        'Brexit Votes': d.BrexitVote19,
        'Population Density': d.c11PopulationDensity,
        'Percentage Retired': d.c11Retired
    } for d in data])

    numeric_df = df.select_dtypes(include=[np.number])  # This filters out non-numeric columns
    correlation_matrix = numeric_df.corr()
    fig = px.imshow(correlation_matrix,
                    labels=dict(x="Variable", y="Variable", color="Correlation"),
                    x=correlation_matrix.columns,
                    y=correlation_matrix.columns,
                    title=f"Correlation Heatmap of Voting Patterns and Demographics in {country}")


    fig.update_xaxes(side="bottom")
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('heatmap_voting_patterns.html',
                           title=f'Correlation Heatmap of Voting Patterns and Demographics in {country}',
                           graphJSON=graphJSON)