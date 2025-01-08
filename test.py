import hopsworks

# connect with Hopsworks
project = hopsworks.login()

# get Hopsworks Model Registry
mr = project.get_model_registry()

# get model object
model = mr.get_model("bike_availability_xgboost_model_1", version=1)

model.delete()