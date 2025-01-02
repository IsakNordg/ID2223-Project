import git
import os
import pandas as pd
from datetime import datetime
import json

# Configuration
REPO_URL = "https://github.com/MaxHalford/bike-sharing-history"
CLONE_DIR = "./bike_data/bike-sharing-history"
OUTPUT_FILE = "bike_availability_8AM.csv"
TARGET_CITY = "Gothenburg"

# Clone the repository
if not os.path.exists(CLONE_DIR):
    print("Cloning repository...")
    git.Repo.clone_from(REPO_URL, CLONE_DIR)
repo = git.Repo(CLONE_DIR)

# Prepare the output DataFrame
results = {}
id_to_station = {}

# populate the results dictionary with the stations
data_file = os.path.join(CLONE_DIR, "data/stations/gothenburg/styr--stall.geojson")
if os.path.exists(data_file):
    with open(data_file, "r") as f:
        data = f.read()
        data = json.loads(data)
        for feature in data["features"]:
            station_id = feature["properties"]["station_id"]
            results[station_id] = []
            id_to_station[station_id] = feature["properties"]["name"]

#check length of commits
print(len(list(repo.iter_commits())))
last_day_and_hour = datetime(1970, 1, 1, 0, 0, 0)

for commit in repo.iter_commits():
    # check if there has been a commit this hour
    day_and_hour = commit.committed_datetime.replace(minute=0, second=0, microsecond=0)
    if day_and_hour == last_day_and_hour:
        print(f"Skipping commit: {commit.hexsha}, {commit.committed_datetime}")
        continue
    last_day_and_hour = day_and_hour
    # not test ^^^

    print(f"Checking commit: {commit.hexsha}, {commit.committed_datetime}")
    repo.git.checkout(commit.hexsha)
    data_file = os.path.join(CLONE_DIR, "data/stations/gothenburg/styr--stall.geojson")
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            data = f.read()
            data = json.loads(data)
            print(data["features"][0]["properties"]["num_bikes_available"])
            print(len(data["features"]))
            for feature in data["features"]:
                results[feature["properties"]["station_id"]].append([feature["properties"]["num_bikes_available"], commit.committed_datetime])
    break

# results format
"""
{
    "station_id": [
        [num_bikes_available, datetime],
        ...
    ],
    ...
}
"""

# Store results in a CSV file

print("Storing results...")
