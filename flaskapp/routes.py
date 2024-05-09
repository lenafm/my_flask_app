# Standard library imports
import datetime
import json

# Third-party imports
from flask import Flask, render_template, flash, redirect, url_for, request
from markupsafe import Markup
import pandas as pd
import plotly as plotly
import plotly.express as px
import plotly.io as pio
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
import plotly.graph_objects as go 

# Local application imports
from flaskapp import app, db
from flaskapp.models import BlogPost, IpView, Day, UkData
from flaskapp.forms import PostForm
import datetime
from flaskapp.plotting import create_demographic_plot

import pandas as pd
import json
import plotly
import plotly.express as px
import json


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


@app.route('/turnout')
def turnout():
    # Fetch the data from the database
    data = UkData.query.all()

    # Define a mapping between the original column names and new desired names
    party_rename_map = {
        'ConVote19': 'Conservative',
        'LabVote19': 'Labour',
        'LDVote19': 'Liberal Democrats',
        'SNPVote19': 'Scottish National Party',
        'PCVote19': 'Plaid Cymru',
        'UKIPVote19': 'UKIP',
        'GreenVote19': 'Green',
        'BrexitVote19': 'Brexit Vote',
        'TotalVote19': 'Total Votes'
    }
    
    # Prepare the data for plotting using the new names
    data_list = []
    for record in data:
        for original_party, new_party in party_rename_map.items():
            data_list.append({
                'Region': record.region,
                'Party': new_party,
                'Votes': getattr(record, original_party)
            })

    # Create a DataFrame
    df = pd.DataFrame(data_list)

    # Create a grouped bar chart
    fig = px.bar(
        df, x='Region', y='Votes', color='Party', barmode='group',
        labels={'Region': 'Region', 'Votes': 'Votes'},
        title='Interactive Chart - Select or Deselect Parties'
    )

    # Convert the Plotly chart to JSON to pass to the template
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('turnout.html', graphJSON=Markup(graphJSON))


@app.route('/demographics/<region>')
def demographics(region):
    # Capitalizes the first letter of each word, suitable for multi-word region names.
    region = region.replace('-', ' ').title()
    data = UkData.query.filter_by(region=region).all()
    if not data:
        abort(404, description=f"Data for {region} not found")

    data_list = [{col.name: getattr(d, col.name) for col in UkData.__table__.columns} for d in data]
    df = pd.DataFrame(data_list)

    demographic_columns = df.columns[-5:]
    category_names = {
        'c11Female': 'Female - no/yes',
        'c11FulltimeStudent': 'Student - no/yes',
        'c11Retired': 'Retired - no/yes',
        'c11HouseOwned': 'Houseowner - no/yes',
        'c11HouseholdMarried':'Married - no/yes'
        # Add more as needed
    }

    fig = go.Figure()

    for col in demographic_columns:
        value = round(df[col].iloc[0], 1)
        complement = round(100 - value, 1)
        friendly_name = category_names.get(col, col)

        fig.add_trace(go.Bar(
            y=[friendly_name],
            x=[-complement / 2], 
            name='Other',
            orientation='h',
            text=[f"{complement}%"],
            textposition='inside',
            marker=dict(color='green')
        ))

        fig.add_trace(go.Bar(
            y=[friendly_name],
            x=[value / 2], 
            name='Reported',
            orientation='h',
            text=[f"{value}%"],
            textposition='inside',
            marker=dict(color='blue')
        ))

    fig.update_layout(
        title=f'Demographic Profile for {region}',
        xaxis=dict(
            title='Percentage',
            range=[-50, 50],
            tickvals=[-50, 0, 50],
            ticktext=['100%', '0%', '100%']  # Adjusted to reflect actual values on the scale.
        ),
        yaxis=dict(title='Category'),
        barmode='overlay',
        plot_bgcolor='white',
        showlegend=False
    )

    graphJSON = plotly.io.to_json(fig)
    return render_template('demographics.html', graphJSON=Markup(graphJSON))


