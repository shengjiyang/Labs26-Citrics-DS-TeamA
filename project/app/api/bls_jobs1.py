from fastapi import APIRouter, HTTPException
from app.sql_query_function import fetch_query

import pandas as pd

router = APIRouter()


@router.get('/bls_jobs/{city}_{statecode}')
async def bls(city: str, statecode: str):
    """
    Most prevelant job industry (city-level) per "Location Quotient" from
    [Burea of Labor Statistics](https://www.bls.gov/oes/tables.htm) 📈

    ## Response
    JSON string of most prevelant job industry for more than 350
    U.S. cities.
    """

    query = """
    SELECT DISTINCT ON (j.city) j.*
    FROM bls_jobs j
    ORDER BY j.city, j.loc_quotient DESC
    """

    columns = [
        "city",
        "state",
        "occ_title",
        "jobs_1000",
        "loc_quotient",
        "hourly_wage",
        "annual_wage"]

    df = pd.read_json(fetch_query(query, columns))

    # Input sanitization
    city = city.title()
    statecode = statecode.lower().upper()

    # Handle Edge Cases:
    # saint
    if city[0:5] == "Saint":
        city = city.replace("Saint", "St.")

    elif city[0:3] == "St ":
        city = city.replace("St", "St.")

    # fort
    elif city[0:3] == "Ft ":
        city = city.replace("Ft", "Fort")

    elif city[0:3] == "Ft.":
        city = city.replace("Ft.", "Fort")

    # Find matching metro-area in database
    match = df.loc[(df.city.str.contains(city)) &
                   (df.state.str.contains(statecode))]

    # Raise HTTPException for unknown inputs
    if len(match) < 1:
        raise HTTPException(
            statuscode=404,
            detail=f'{city}, {state} not found!')

    # DF to dictionary
    pairs = match.to_json(orient='records')

    return pairs
