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


@app.route('/cluster_analysis_1', methods=['GET'])
def cluster_analysis_1():
    country = request.args.get('country', default='All')
    party_filter = request.args.get('party', default='All')

    query = UkData.query
    if country != 'All':
        query = query.filter_by(country=country)

    data = query.all()
    df = pd.DataFrame([{
        'constituency': item.constituency_name,
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
    } for item in data])

    # Imputation and standardization
    numeric_cols = df.select_dtypes(include=['number']).columns
    df[numeric_cols] = SimpleImputer(strategy='median').fit_transform(df[numeric_cols])
    df[numeric_cols] = StandardScaler().fit_transform(df[numeric_cols])

    # Clustering
    kmeans = KMeans(n_clusters=5, random_state=0)
    clusters = kmeans.fit_predict(df[numeric_cols])
    cluster_labels = {
        0: 'Older, rural',
        1: 'Urban, young',
        2: 'Suburban families',
        3: 'Specialized (uni / industrial)',
        4: 'Mixed with distinct features'
    }
    df['Cluster'] = clusters
    df['Cluster'] = df['Cluster'].map(cluster_labels)

    # Compute dominant party
    party_votes = df[['Conservative', 'Labour', 'Lib Dem', 'SNP', 'Plaid Cymru', 'UKIP', 'Green', 'Brexit Party']]
    party_votes = party_votes.apply(pd.to_numeric, errors='coerce')
    df['Dominant Party'] = party_votes.idxmax(axis=1)
    df['Runner Up Party'] = party_votes.apply(lambda x: x.nlargest(2).idxmin(), axis=1)
    df['Margin of Contestation'] = party_votes.max(axis=1) - party_votes.apply(lambda x: x.nlargest(2).iloc[-1], axis=1)

    # Define party colors
    party_colors = {
        'Conservative': 'blue',
        'Labour': 'red',
        'Lib Dem': 'yellow',
        'SNP': 'purple',
        'Plaid Cymru': 'black',
        'UKIP': 'Orange',
        'Green': 'green',
        'Brexit Party': 'pink'
    }

    # fig 1 heatmap
    #fig1_heatmap = px.imshow(df.pivot_table(index='Party', columns='Cluster', values='Total Vote', aggfunc='mean'),
    #                        labels=dict(x="Cluster", y="Party", color="Mean Total Vote"),
    #                        title="Cluster to Party Correlation Heat Map")

    
    # fig 2 cluster size
    cluster_sizes = df['Cluster'].value_counts().reset_index()
    cluster_sizes.columns = ['Cluster', 'Number of Constituencies']

    fig2_cluster_size = px.bar(cluster_sizes, x='Cluster', y='Number of Constituencies', 
                               title=f'Number of Constituencies in {country} Characterised by a Given Sub-Population, as Won by the {party_filter} Party')
    fig2_cluster_size.update_layout(xaxis_title='Cluster', yaxis_title='Number of Constituencies')
    
    #fig 3 list of contested seats    
    # Filter data based on party if the filter is not 'All'
    if party_filter != 'All':
        df = df[(df['Dominant Party'] == party_filter) | (df['Runner Up Party'] == party_filter)]

    # Convert DataFrame to HTML table only displaying relevant rows
    contested_df = df[['constituency', 'Margin of Contestation', 'Dominant Party', 'Runner Up Party', 'Cluster']]
    table3_html = contested_df.to_html(index=False, classes='table table-striped')
    

    # Convert plots to JSON
    graphJSON2_cluster_size = json.dumps(fig2_cluster_size, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('cluster1.html', 
                           graphJSON2_cluster_size=graphJSON2_cluster_size, 
                           table3_html=table3_html, 
                           current_country=country,
                           current_party=party_filter)










@app.route('/cluster_analysis_2', methods=['GET'])
def cluster_analysis_2():
    country = request.args.get('country', default='All')
    x_axis = request.args.get('x_axis', default='Population Density')

    query = UkData.query
    if country != 'All':
        query = query.filter_by(country=country)

    data = query.all()
    df = pd.DataFrame([{
        'constituency': item.constituency_name,
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
    } for item in data])

    # Imputation and standardization
    numeric_cols = df.select_dtypes(include=['number']).columns
    df[numeric_cols] = SimpleImputer(strategy='median').fit_transform(df[numeric_cols])
    df[numeric_cols] = StandardScaler().fit_transform(df[numeric_cols])

    # Clustering
    kmeans = KMeans(n_clusters=5, random_state=0)
    clusters = kmeans.fit_predict(df[numeric_cols])
    cluster_labels = {
        0: 'Older, rural',
        1: 'Urban, young',
        2: 'Suburban families',
        3: 'Specialized (uni / industrial)',
        4: 'Mixed with distinct features'
    }
    df['Cluster'] = clusters
    df['Cluster'] = df['Cluster'].map(cluster_labels)

    # Compute dominant party
    party_votes = df[['Conservative', 'Labour', 'Lib Dem', 'SNP', 'Plaid Cymru', 'UKIP', 'Green', 'Brexit Party']]
    party_votes = party_votes.apply(pd.to_numeric, errors='coerce')
    df['Dominant Party'] = party_votes.idxmax(axis=1)
    df['Runner Up Party'] = party_votes.apply(lambda x: x.nlargest(2).idxmin(), axis=1)
    df['Margin of Contestation'] = party_votes.max(axis=1) - party_votes.apply(lambda x: x.nlargest(2).iloc[-1], axis=1)
    

    # fig4
    fig4_histogram = px.histogram(df, x=x_axis, color='Cluster',
                    labels={"Cluster": "Cluster", "Count": "Density of Cluster Membership"},
                    title=" Distribution of Cluster Membership by " + x_axis,
                    hover_data=[x_axis, 'Cluster'],
                    marginal='rug',
                    histnorm='probability density',
                    barmode='overlay',  # Ensure bars are overlaid on one another
                    nbins=30,  # Optionally adjust number of bins for smoother appearance
                    histfunc='avg'  # Average to smooth out the distribution
    )

    # Update the trace to adjust opacity and line properties
    fig4_histogram.update_traces(opacity=0.75, marker_line_width=0.5, marker_line_color='white')
    fig4_histogram.update_layout(
        bargap=0.1,  # Adjust the gap between bars for a smoother appearance
        plot_bgcolor="rgba(0,0,0,0)"  # Makes the background transparent
    )

    
    #fig5 scatter plot
    fig5_scatter = px.strip(df, x=x_axis, y='Dominant Party', color='Cluster', 
            labels={"Cluster": "Cluster"},
            title="Constituency Distribution by " + x_axis + " and Dominant Party",
            hover_data=[x_axis, 'Dominant Party'],
            orientation='h',  
            stripmode='group') 

    # Convert plots to JSON
    graphJSON4_histogram = json.dumps(fig4_histogram, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON5_scatter = json.dumps(fig5_scatter, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('cluster2.html', 
                           graphJSON4_histogram=graphJSON4_histogram, 
                           graphJSON5_scatter=graphJSON5_scatter,
                           current_x_axis=x_axis, 
                           current_country=country)    
    
    




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
