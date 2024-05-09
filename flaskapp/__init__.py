from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, Response
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from flask_sqlalchemy import SQLAlchemy


# Creating your flaskapp instance
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')

# Configuring the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

# Creating a SQLAlchemy database instance
db = SQLAlchemy(app)
app.app_context().push()

from flaskapp import routes
