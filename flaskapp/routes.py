from flask import render_template, flash, redirect, url_for, request
from flaskapp import app, db
from flaskapp.models import BlogPost, IpView, Day, UkData
from flaskapp.forms import PostForm
import datetime

import pandas as pd
import json
import plotly
import plotly.express as px


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


@app.route('/uk-data-viz')
@app.route('/uk-data-viz/<country_name>')
def uk_data_viz(country_name = None):
    if country_name:
        test = UkData.query.filter_by(country = country_name)
        title = f'Demographics and Vote Share of Labor in {country_name}'
    else:
        title = 'Demographics and Vote Share of Labor'
        test = UkData.query.all()
    df = pd.DataFrame([{'TotalVotes': row.TotalVote19,
                        'PopDensity': row.c11PopulationDensity,
                        'LaborVotes': row.LabVote19,
                        'PercentStudent': row.c11FulltimeStudent,
                        'PercentTurnout': row.Turnout19}
                        for row in test])
    df['PercentLabor'] = df['LaborVotes'] / df['TotalVotes']
    df['PercentStudent'] = df['PercentStudent'] / 100
    fig1 = px.scatter(df, x='PopDensity', y='PercentLabor',
                      title = 'Labor Support is Positively Correlated with Population Density',
                      labels = {'PopDensity': 'Population Density',
                                'PercentLabor': 'Vote Share of Labor'})
    fig1.update_yaxes(range=[0, 1])
    fig1.update_yaxes(tickformat=".0%")
    fig1.update_layout({
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'white',
        'xaxis': {
            'showgrid': True,            
            'gridcolor': 'lightgrey',
            'gridwidth': 1,           
            'zerolinecolor': 'lightgrey',
            'linecolor': 'black', 
        },
        'yaxis': {
            'showgrid': True,
            'gridcolor': 'lightgrey',
            'gridwidth': 1,
            'zerolinecolor': 'lightgrey',
            'linecolor': 'black',
        }
    })
    graph1JSON = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)
    fig2 = px.scatter(df, x='PercentStudent', y='PercentLabor',
                      title = 'Labor Support is Positively Correlated with Student Status',
                      labels = {'PercentStudent': 'Percent of Full-Time Students in Constituency',
                                'PercentLabor': 'Vote Share of Labor'})
    fig2.update_xaxes(range=[0, 0.5])
    fig2.update_xaxes(tickformat=".0%")
    fig2.update_yaxes(range=[0, 1])
    fig2.update_yaxes(tickformat=".0%")
    fig2.update_layout({
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'white',
        'xaxis': {
            'showgrid': True,            
            'gridcolor': 'lightgrey',
            'gridwidth': 1,           
            'zerolinecolor': 'lightgrey',
            'linecolor': 'black', 
        },
        'yaxis': {
            'showgrid': True,
            'gridcolor': 'lightgrey',
            'gridwidth': 1,
            'zerolinecolor': 'lightgrey',
            'linecolor': 'black',
        }
    })
    graph2JSON = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('uk-viz.html', title=title, graph1JSON=graph1JSON, graph2JSON=graph2JSON)