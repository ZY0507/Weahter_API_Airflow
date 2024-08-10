# Import necessary modules from Airflow
from airflow import DAG
from datetime import timedelta, datetime
from airflow.providers.http.sensors.http import HttpSensor
from airflow.operators.python import PythonOperator

# Import necessary external libraries
import pandas as pd  # For handling CSV files and dataframes
import requests  # For making HTTP requests to the weather API

# Function to fetch weather data for a specific city from the Weather API
def fetch_city_weather(city, api_key):
    # Create the API URL with the provided city and API key
    api_link = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}"
    
    # Send a GET request to the API
    response = requests.get(api_link)
    
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Return the JSON data from the response and no error
        return response.json(), None
    else:
        # Return no data and an error dictionary containing the city and the status code
        return None, {'City': city, 'StatusCode': response.status_code}

# Function to transform the raw weather data into a structured format
def transform_city_weather_data(city, data):
    # Extract relevant sections from the JSON data
    location = data.get('location', {})
    current = data.get('current', {})
    condition = current.get('condition', {})

    # Return a dictionary containing the structured weather data
    return {
        'City': location.get('name'),
        'Region': location.get('region'),
        'Country': location.get('country'),
        'Latitude': location.get('lat'),
        'Longitude': location.get('lon'),
        'TimeZone': location.get('tz_id'),
        'LocalTimeEpoch': location.get('localtime_epoch'),
        'LocalTime': location.get('localtime'),
        'LastUpdatedEpoch': current.get('last_updated_epoch'),
        'LastUpdated': current.get('last_updated'),
        'Temperature_C': current.get('temp_c'),
        'Temperature_F': current.get('temp_f'),
        'IsDay': current.get('is_day'),
        'ConditionText': condition.get('text'),
        'ConditionIcon': condition.get('icon'),
        'WindMPH': current.get('wind_mph'),
        'WindKPH': current.get('wind_kph'),
        'WindDegree': current.get('wind_degree'),
        'WindDir': current.get('wind_dir'),
        'PressureMB': current.get('pressure_mb'),
        'PressureIn': current.get('pressure_in'),
        'PrecipMM': current.get('precip_mm'),
        'PrecipIn': current.get('precip_in'),
        'Humidity': current.get('humidity'),
        'Cloud': current.get('cloud'),
        'FeelsLike_C': current.get('feelslike_c'),
        'FeelsLike_F': current.get('feelslike_f'),
        'VisibilityKM': current.get('vis_km'),
        'VisibilityMiles': current.get('vis_miles'),
        'UV': current.get('uv'),
        'GustMPH': current.get('gust_mph'),
        'GustKPH': current.get('gust_kph')
    }

# Function to read a list of cities from a CSV file
def read_cities_from_csv(file_path):
    # Read the CSV file into a pandas DataFrame, with ';' as the delimiter
    df = pd.read_csv(file_path, delimiter=';')
    
    # Return the list of cities (assumed to be in a column named 'city_acsii')
    return df['city_acsii'].tolist()

# Function to extract weather data for a list of cities
def extract_weather_data(cities, api_key):
    all_data = []  # List to store successful data
    error_data = []  # List to store any errors

    # Loop through each city in the list
    for city in cities:
        # Fetch the weather data for the city
        data, error = fetch_city_weather(city, api_key)
        
        # If data was successfully retrieved, transform and store it
        if data:
            transformed_data = transform_city_weather_data(city, data)
            all_data.append(transformed_data)
        
        # If there was an error, store the error information
        if error:
            error_data.append(error)
    
    # Return the collected data and errors
    return all_data, error_data

# Function to transform lists of data into pandas DataFrames
def transform_data(all_data, error_data):
    df_data = pd.DataFrame(all_data)  # Create a DataFrame from the successful data
    df_errors = pd.DataFrame(error_data)  # Create a DataFrame from the errors
    return df_data, df_errors  # Return both DataFrames

# Function to upload the data to an S3 bucket
def upload_to_s3(df_data, df_errors, s3_bucket):
    # AWS credentials to access S3 (you should handle these securely)
    aws_credentials = {
        'key': 'uvwsyz', 
        'secret': 'abcdefghigklmnopqrst', 
        "token": '1234567890asdfghjkl'}

    # Generate filenames for the data and error CSVs
    now = datetime.now().strftime('%Y%m%d%H%M%S')  # Get the current timestamp
    
    weather_filename = f's3://{s3_bucket}/{now}_weather_data_sweden.csv'
    errors_filename = f's3://{s3_bucket}/{now}_error_data_sweden.csv'
    
    # Upload the data DataFrame to S3
    df_data.to_csv(weather_filename, index=False, storage_options=aws_credentials)
    
    # Upload the errors DataFrame to S3
    df_errors.to_csv(errors_filename, index=False, storage_options=aws_credentials)

# Default arguments for the DAG, controlling its behavior
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 8),
    'email': ['sample@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2)
}

# API key for the Weather API (replace with your actual key)
# You can get your own API Key By signing up on this page: https://www.weatherapi.com/
api_key = '8888888888888888888888'

# Path to the CSV file containing the cities
cities_file_path = '/home/ubuntu/airflow/dags/city_sweden.csv'  # Update this path to your CSV file location

# Name of the S3 bucket to upload the data
s3_bucket = 'weather-api-airflow-zy'  # Update with your S3 bucket name

# Define the DAG
with DAG('weather_dag',
         default_args=default_args,
         schedule_interval='@daily',  # Run daily
         catchup=False) as dag:

    # Task to check if the Weather API is ready (responding)
    is_weather_api_ready = HttpSensor(
        task_id='is_weather_api_ready',
        http_conn_id='Weather_API',  # Connection ID for the Weather API
        endpoint=f'/v1/current.json?key={api_key}&q=Stockholm'  # Sample request to check API readiness
    )

    # Python task to extract weather data
    def extract_task(**kwargs):
        cities = read_cities_from_csv(cities_file_path)  # Read the list of cities from the CSV file
        all_data, error_data = extract_weather_data(cities, api_key)  # Extract weather data for each city
        
        # Push the extracted data and errors to XCom (for use by other tasks)
        kwargs['ti'].xcom_push(key='all_data', value=all_data)
        kwargs['ti'].xcom_push(key='error_data', value=error_data)

    extract_weather_data_task = PythonOperator(
        task_id='extract_weather_data',
        python_callable=extract_task,
        provide_context=True  # Allow passing context (e.g., XCom) to the task
    )

    # Python task to transform the data into a structured format
    def transform_task(**kwargs):
        # Pull the extracted data and errors from XCom
        all_data = kwargs['ti'].xcom_pull(key='all_data', task_ids='extract_weather_data')
        error_data = kwargs['ti'].xcom_pull(key='error_data', task_ids='extract_weather_data')
        
        # Transform the data and errors into DataFrames
        df_data, df_errors = transform_data(all_data, error_data)
        
        # Push the transformed data to XCom
        kwargs['ti'].xcom_push(key='df_data', value=df_data)
        kwargs['ti'].xcom_push(key='df_errors', value=df_errors)

    transform_data_task = PythonOperator(
        task_id='transform_data',
        python_callable=transform_task,
        provide_context=True  # Allow passing context (e.g., XCom) to the task
    )

    # Python task to upload the transformed data to an S3 bucket
    def upload_task(**kwargs):
        # Pull the transformed data and errors from XCom
        df_data = kwargs['ti'].xcom_pull(key='df_data', task_ids='transform_data')
        df_errors = kwargs['ti'].xcom_pull(key='df_errors', task_ids='transform_data')
        
        # Upload the data to the specified S3 bucket
        upload_to_s3(df_data, df_errors, s3_bucket)

    upload_to_s3_task = PythonOperator(
        task_id='upload_to_s3',
        python_callable=upload_task,
        provide_context=True  # Allow passing context (e.g., XCom) to the task
    )

    # Define the order of tasks (dependencies)
    is_weather_api_ready >> extract_weather_data_task >> transform_data_task >> upload_to_s3_task
