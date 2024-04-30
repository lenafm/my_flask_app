from flask import render_template, flash, redirect, url_for, request, jsonify, request
from flaskapp import app, db
from flaskapp.models import BlogPost, IpView, Day, UkData
from flaskapp.forms import PostForm
import datetime
from sqlalchemy import inspect
import pandas as pd
import json
import plotly
import plotly.express as px
import matplotlib as plt
from io import BytesIO
import base64
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.cluster import KMeans
import seaborn as sns



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


# route to db just to see what's in there
@app.route('/data')
def data():
    data = UkData.query.limit(20).all()  
    mapper = inspect(UkData)
    var_name = [column.key for column in mapper.columns]
    return render_template('data_table.html', data=data)


@app.route('/chart_1')
def chart_1():
    query_results = UkData.query.all()
    df = pd.DataFrame([{
        'House Ownership': item.c11HouseOwned, 
        'Country': item.country, 
        'Turnout': item.Turnout19
        } for item in query_results])

    fig = px.scatter(df, x='House Ownership', color = 'Country', labels={
        "Turnout": "Turnout 2019",
        "House Ownership": "House Ownership (%)"
        }, title='Far-Right/Anti-System Thinking vs Age and Wealth Across Countries')

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template('chart_1.html', title='Far-Right/Anti-System Thinking vs Age and Wealth Across Countries', graphJSON=graphJSON)


@app.route('/cluster_analysis')
def cluster_analysis():
    query_results = UkData.query.all()
    df = pd.DataFrame([
        {
            'House Ownership': item.c11HouseOwned, 
            'Country': item.country, 
            'Turnout': item.Turnout19,
            'ConVote19': item.ConVote19,
            'LabVote19': item.LabVote19,
            'LDVote19': item.LDVote19,
            'SNPVote19': item.SNPVote19,
            'PCVote19': item.PCVote19,
            'UKIPVote19': item.UKIPVote19,
            'GreenVote19': item.GreenVote19,
            'BrexitVote19': item.BrexitVote19,
            'TotalVote19': item.TotalVote19,
            'c11PopulationDensity': item.c11PopulationDensity,
            'c11Female': item.c11Female,
            'c11FulltimeStudent': item.c11FulltimeStudent,
            'c11Retired': item.c11Retired,
            'c11HouseholdMarried': item.c11HouseholdMarried
        } for item in query_results
    ])
    

    # Separate numeric and categorical columns
    numeric_cols = df.select_dtypes(include=['number']).columns
    categorical_cols = df.select_dtypes(exclude=['number']).columns

    # Impute numeric columns using median
    numeric_imputer = SimpleImputer(strategy='median')
    df[numeric_cols] = numeric_imputer.fit_transform(df[numeric_cols])

    # Impute categorical columns using the most frequent value
    categorical_imputer = SimpleImputer(strategy='most_frequent')
    df[categorical_cols] = categorical_imputer.fit_transform(df[categorical_cols])

    # Standardize the numeric data
    scaler = StandardScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

    # Perform K-means clustering
    kmeans = KMeans(n_clusters=5, random_state=0)
    clusters = kmeans.fit_predict(df[numeric_cols])  # Only cluster on numeric data

    df['Cluster'] = clusters
    
    # Create a Plotly figure
    fig = px.scatter(df, x='c11PopulationDensity', y='Turnout', color='Cluster', 
                     labels={"color": "Cluster"},
                     title="Cluster Visualization by Population Density and Voter Turnout")
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('cluster.html', graphJSON=graphJSON)








# route to choropleth
@app.route('/choropleth')
def choropleth():
    return render_template('choropleth.html')

# route to choroplet data for JSON data for dynamic map updates
@app.route('/choropleth/data', methods=['GET']) 
def get_choropleth_data(): # I THINK THIS IS WRONG?????
    country = request.args.get('country', default=None)
    data_type = request.args.get('type', default='vote')  # 'vote', 'density', 'retired', etc.

    # base query
    query = UkData.query

    if country:
        query = query.filter_by(country=country)

    if data_type == 'vote':
        # Example of complex calculation for dominant party (simplified here)
        data = [{
            'id': item.id,
            'name': item.constituency_name,
            'dominant_party': 'Conservative' if item.ConVote19 > item.LabVote19 else 'Labour',  # Simplified logic
            'value': max(item.ConVote19, item.LabVote19)  # Example calculation
        } for item in query.all()]
    else:
        # Different data types for demographic data
        attribute_map = {
            'density': 'c11PopulationDensity',
            'retired': 'c11Retired',
            'home_ownership': 'c11HouseOwned',
            'female': 'c11Female',
        }
        attribute = attribute_map.get(data_type)
        data = [{
            'id': item.id,
            'name': item.constituency_name,
            'value': getattr(item, attribute)
        } for item in query.all()]

    return jsonify(data)

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
