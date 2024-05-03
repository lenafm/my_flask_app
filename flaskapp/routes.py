from flask import render_template, flash, redirect, url_for, request, jsonify, request, abort
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


@app.route('/cluster_analysis', methods=['GET'])
def cluster_analysis():
    country = request.args.get('country', default='All')
    x_axis = request.args.get('x_axis', 'Population Density')

    query = UkData.query
    if country != 'All':
        query = query.filter_by(country=country)
        
    all_columns = [
        'id', 'constituency_name', 'country', 'region', 'Turnout19', 
        'ConVote19', 'LabVote19', 'LDVote19', 'SNPVote19', 'PCVote19', 
        'UKIPVote19', 'GreenVote19', 'BrexitVote19', 'TotalVote19', 
        'c11PopulationDensity', 'c11Female', 'c11FulltimeStudent', 
        'c11Retired', 'c11HouseOwned', 'c11HouseholdMarried'
    ]

    df = pd.DataFrame([
        {
            'House Ownership': item.c11HouseOwned, 
            'Country': item.country, 
            'Turnout': item.Turnout19,
            'Conservative': item.ConVote19,
            'Labour': item.LabVote19,
            'Lib Dem': item.LDVote19,
            'SNP': item.SNPVote19,
            'Plaid Cymru': item.PCVote19,
            'UKIP': item.UKIPVote19,
            'Green': item.GreenVote19,
            'Brexit Party': item.BrexitVote19,
            'Total Vote': item.TotalVote19,
            'Population Density': item.c11PopulationDensity,
            'Female Pop %': item.c11Female,
            'Student Pop %': item.c11FulltimeStudent,
            'Retired Pop %': item.c11Retired,
            'Married Pop %': item.c11HouseholdMarried
        } for item in query.all()
    ])


    # Imputation and standardization
    numeric_cols = df.select_dtypes(include=['number']).columns
    df[numeric_cols] = SimpleImputer(strategy='median').fit_transform(df[numeric_cols])
    df[numeric_cols] = StandardScaler().fit_transform(df[numeric_cols])

    # Clustering
    kmeans = KMeans(n_clusters=5, random_state=0)
    clusters = kmeans.fit_predict(df[numeric_cols])
    df['Cluster'] = clusters

    # Compute dominant party
    party_votes = df[['Conservative', 'Labour', 'Lib Dem', 'SNP', 'Plaid Cymru', 'UKIP', 'Green', 'Brexit Party']]
    df['Dominant Party'] = party_votes.idxmax(axis=1)

    # Define party colors
    party_colors = {
        'Conservative': 'blue',
        'Labour': 'red',
        'Lib Dem': 'yellow',
        'SNP': 'purple',
        'Plaid Cymru': 'black',
        'UKIP': 'purple',
        'Green': 'green',
        'Brexit Party': 'grey'
    }

    # First plot
    fig1 = px.strip(df, x=x_axis, y='Dominant Party', color='Cluster', 
                labels={"Cluster": "Cluster"},
                title="Voter Distribution by " + x_axis + " and Dominant Party",
                hover_data=[x_axis, 'Dominant Party'],
                orientation='h',  
                stripmode='overlay') 

    # Second plot
    fig2 = px.strip(df, x=x_axis, y='Cluster', color='Dominant Party',
                color_discrete_map=party_colors,
                labels={"Dominant Party": "Dominant Party"},
                title="Cluster Distribution by " + x_axis,
                hover_data=[x_axis, 'Cluster'],
                orientation='h',
                stripmode='overlay')

    # Convert plots to JSON
    graphJSON1 = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('cluster.html', graphJSON1=graphJSON1, graphJSON2=graphJSON2, current_x_axis=x_axis, current_country=country)







# route to choropleth
@app.route('/choropleth')
def choropleth():
    return render_template('choropleth.html')

@app.route('/choropleth/data', methods=['GET'])
def get_choropleth_data():
    try:
        country = request.args.get('country', default=None)
        data_type = request.args.get('type', default='vote')

        # Base query
        query = UkData.query

        if country:
            query = query.filter_by(country=country)
        
        if not query.first():  # check if  query returned any data
            abort(404, description="No data available for the given country.")

        if data_type == 'vote':
            data = []
            for item in query.all():
                # dict of party and votes
                vote_counts = {
                    'Conservative': (item.ConVote19 or 0),
                    'Labour': (item.LabVote19 or 0),
                    'Liberal Democrat': (item.LDVote19 or 0),
                    'SNP': (item.SNPVote19 or 0),
                    'Plaid Cymru': (item.PCVote19 or 0),
                    'UKIP': (item.UKIPVote19 or 0),
                    'Green': (item.GreenVote19 or 0),
                    'Brexit': (item.BrexitVote19 or 0)
                }
                
                # compute party w/ maximum votes
                dominant_party = max(vote_counts, key=vote_counts.get)
                dominant_votes = vote_counts[dominant_party]

                # add to data
                data.append({
                    'id': item.id,
                    'name': item.constituency_name,
                    'dominant_party': dominant_party,
                    'value': dominant_votes
                })
        else:
            attribute_map = {
                'density': 'c11PopulationDensity',
                'retired': 'c11Retired',
                'home_ownership': 'c11HouseOwned',
                'female': 'c11Female',
            }
            attribute = attribute_map.get(data_type)
            if attribute is None:
                abort(400, description="Invalid data type provided.")
            
            data = [{
                'id': item.id,
                'name': item.constituency_name,
                'value': getattr(item, attribute)
            } for item in query.all()]

        return jsonify(data)

    except Exception as e:
        app.logger.error('Failed to fetch data: {}'.format(str(e)))
        response = jsonify({'error': 'Internal server error', 'message': str(e)})
        response.status_code = 500
        return response


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
