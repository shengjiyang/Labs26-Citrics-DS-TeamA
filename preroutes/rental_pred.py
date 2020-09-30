from dotenv import load_dotenv
import os
import psycopg2
import warnings
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import numpy as np
import plotly.express as px

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "Invalid DB_NAME value")
DB_USER = os.getenv("DB_USER", "Invalid DB_USER value")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Invalid DB_PASSWORD value")
DB_HOST = os.getenv("DB_HOST", "Invalid DB_HOST value")

connection = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST
    )

cur = connection.cursor()

def rental_predictions(city, state):
    warnings.filterwarnings("ignore", message="After 0.13 initialization must be handled at model creation")
    query = """
    SELECT "month", "Studio", "onebr", "twobr", "threebr", "fourbr"
    FROM rental
    WHERE "city"='{city}' and "state"='{state}';
    """.format(city=city, state=state)

    cur.execute(query)

    df =  pd.DataFrame.from_records(cur.fetchall(), columns=["month", "Studio", "onebr", "twobr", "threebr", "fourbr"])
    df.set_index("month", inplace=True)
    df.index = pd.to_datetime(df.index)
    df.index.freq = "MS"
    
    series = []

    for col in df.columns:
        s = ExponentialSmoothing(df["2014-06-01":][col].astype(float), trend="add", seasonal="add", seasonal_periods=12).fit().forecast(12)
        s.name = col
        series.append(s)

    return pd.concat(series, axis=1).to_json(indent=2)

# Visualization Function
# w/o reconnecting to the API
def viz(city, state):
    df = pd.read_json(rental_predictions(city, state))
    df.columns = [
        "Studio",
        "One Bedroom",
        "Two Bedroom",
        "Three Bedroom",
        "Four Bedroom"
    ]
    fig = px.line(df, x=df.index, y=df.columns, title="Rental Price - Predicted",
    labels=dict(index="Month", value="Price in USD"),
    range_y=[0, df["Four Bedroom"].max()]
    )
    return fig.show()
    # return px.line(df, x=df.index, y=df.columns).to_json()