import os
import datetime
import time
import requests
import pandas as pd
import json
from geopy.geocoders import Nominatim
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator
from matplotlib.dates import DateFormatter
import openmeteo_requests
import requests_cache
from retry_requests import retry
import hopsworks
import hsfs
from pathlib import Path
from matplotlib.dates import AutoDateLocator, DateFormatter
from matplotlib.ticker import MaxNLocator


features = {
    "hourly": ["temperature_2m", "apparent_temperature", "rain", "snowfall", "wind_speed_10m"],
    "daily": ["daylight_duration", "rain_sum"]
}


def get_historical_weather(city, start_date, end_date):
    latitude, longitude = get_city_coordinates(city)

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
    }
    params.update(features)
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_apparent_temperature = hourly.Variables(1).ValuesAsNumpy()
    hourly_rain = hourly.Variables(2).ValuesAsNumpy()
    hourly_snowfall = hourly.Variables(3).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(4).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
    	start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
    	end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
    	freq = pd.Timedelta(seconds = hourly.Interval()),
    	inclusive = "left"
    )}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["apparent_temperature"] = hourly_apparent_temperature
    hourly_data["rain"] = hourly_rain
    hourly_data["snowfall"] = hourly_snowfall
    hourly_data["wind_speed_10m"] = hourly_wind_speed_10m

    hourly_dataframe = pd.DataFrame(data = hourly_data)
    
    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_daylight_duration = daily.Variables(0).ValuesAsNumpy()
    daily_rain_sum = daily.Variables(1).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
    	start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
    	end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
    	freq = pd.Timedelta(seconds = daily.Interval()),
    	inclusive = "left"
    )}
    daily_data["daylight_duration"] = daily_daylight_duration
    daily_data["rain_sum"] = daily_rain_sum

    daily_dataframe = pd.DataFrame(data = daily_data)
    daily_dataframe['city'] = city

    # Extract the date from the 'datetime' column to be able to merge
    hourly_dataframe['date_only'] = hourly_dataframe['date'].dt.strftime('%Y-%m-%d 00:00:00+00:00')
    hourly_dataframe['date_only'] = pd.to_datetime(hourly_dataframe['date_only'])
    df = hourly_dataframe.merge(daily_dataframe, left_on='date_only', right_on='date', how='left')
    return df

def get_city_coordinates(city_name: str):
    """
    Takes city name and returns its latitude and longitude (rounded to 2 digits after dot).
    """
    # Initialize Nominatim API (for getting lat and long of the city)
    geolocator = Nominatim(user_agent="MyApp")
    city = geolocator.geocode(city_name)

    latitude = round(city.latitude, 2)
    longitude = round(city.longitude, 2)

    return latitude, longitude


def secrets_api(project):
    try:
        api_key = os.environ.get('HOPSWORKS_API_KEY')
        if not api_key:
            raise ValueError("API key not found in environment variables.")
    except ValueError:
        load_dotenv()
        api_key = os.environ.get('HOPSWORKS_API_KEY')
    connection = hopsworks.connection(api_key_value=api_key, host="c.app.hopsworks.ai", project=project)
    return connection.get_secrets_api()


def get_hourly_weather_forecast(city):

    latitude, longitude = get_city_coordinates(city)

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/ecmwf"
    params = {
        "latitude": latitude,
        "longitude": longitude,
    }
    params.update(features)
    print("features:", features)
    print("params:", params)
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data. The order of variables needs to be the same as requested.

    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_apparent_temperature = hourly.Variables(1).ValuesAsNumpy()
    hourly_rain = hourly.Variables(2).ValuesAsNumpy()
    hourly_snowfall = hourly.Variables(3).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(4).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
    	start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
    	end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
    	freq = pd.Timedelta(seconds = hourly.Interval()),
    	inclusive = "left"
    )}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["apparent_temperature"] = hourly_apparent_temperature
    hourly_data["rain"] = hourly_rain
    hourly_data["snowfall"] = hourly_snowfall
    hourly_data["wind_speed_10m"] = hourly_wind_speed_10m

    hourly_dataframe = pd.DataFrame(data = hourly_data)
    
    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_daylight_duration = daily.Variables(0).ValuesAsNumpy()
    daily_rain_sum = daily.Variables(1).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
    	start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
    	end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
    	freq = pd.Timedelta(seconds = daily.Interval()),
    	inclusive = "left"
    )}
    daily_data["daylight_duration"] = daily_daylight_duration
    daily_data["rain_sum"] = daily_rain_sum

    daily_dataframe = pd.DataFrame(data = daily_data)
    daily_dataframe['city'] = city

    # Extract the date from the 'datetime' column to be able to merge
    hourly_dataframe['date_only'] = hourly_dataframe['date'].dt.strftime('%Y-%m-%d 00:00:00+00:00')
    hourly_dataframe['date_only'] = pd.to_datetime(hourly_dataframe['date_only'])
    df = hourly_dataframe.merge(daily_dataframe, left_on='date_only', right_on='date', how='left')
    return df
    
def plot_bike_availability_forecast(city: str, station_1: str, station_2: str, df: pd.DataFrame, file_path: str, hindcast=False):
    
    fig, ax = plt.subplots(figsize=(14, 6))

    datetime = pd.to_datetime(df['datetime'])
    # Plot each column separately in matplotlib
    ax.plot(datetime, df['bikes_available_stn_1'], label=f'Predicted number of bikes available at {station_1}', 
            color='red', linewidth=2, marker='o', markersize=5, markerfacecolor='blue')
    ax.plot(datetime, df['bikes_available_stn_2'], label=f'Predicted number of bikes available at {station_2}', 
            color='blue', linewidth=2, marker='o', markersize=5, markerfacecolor='red')

    # Set the y-axis to a linear scale
    ax.set_yticks([0, 10, 20, 30, 40, 50])
    ax.get_yaxis().set_major_formatter(plt.ScalarFormatter())
    ax.set_ylim(bottom=1)

    # Set the labels and title
    ax.set_xlabel('Date and Time')
    ax.set_title(f"Predicted number of bikes available for {city}, {station_1} and {station_2}")
    ax.set_ylabel('Number of bikes available')

    # Use AutoDateLocator and MaxNLocator for denser labels
    locator = AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=20))  # Increase the number of ticks

    ax.xaxis.set_major_formatter(DateFormatter('%d %b %H:%M'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')  # Rotate for readability

    if hindcast:
        ax.plot(datetime, df['num_bikes_available'], label='Actual number of bikes available', 
                color='black', linewidth=2, marker='^', markersize=5, markerfacecolor='grey')
        ax.legend(loc='upper left', fontsize='x-small')

    # Ensure everything is laid out neatly
    plt.tight_layout()

    # Save the figure
    plt.savefig(file_path)
    return plt