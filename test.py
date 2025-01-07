import hopsworks
# from hopsworks import SecretsApi
from functions import utils
import os
import json

from dotenv import load_dotenv
load_dotenv()
HOPSWORKS_API_KEY = os.getenv("HOPSWORKS_API_KEY")
os.environ["HOPSWORKS_API_KEY"] = HOPSWORKS_API_KEY

project = hopsworks.login(api_key_value=HOPSWORKS_API_KEY)
fs = project.get_feature_store() 

connection = hopsworks.connection(api_key_value=HOPSWORKS_API_KEY, host="c.app.hopsworks.ai")
secrets_api = connection.get_secrets_api()

json_data = json.loads(secrets_api.get_secret("time_secrets").value)

