
import requests
import google.oauth2.service_account
import google.auth.transport.requests
import pandas as pd
import datetime
import os
from google.cloud import storage
import time

# file_path = '/tmp/test'
# os.makedirs(os.path.dirname(file_path), exist_ok=True)
# time.sleep(5)
# now = datetime.datetime.now().strftime("%H:%M:%S")
# today = datetime.date.today()

# loading list of GCP projects
project_df = pd.read_csv("projectID_list.csv")
projects_list = project_df['project_name'].tolist()
# projects_list = ["it-services-group-svc-poc"]

# Specify the list of locations
locations = ["asia-south1-a", "asia-south1-b", "asia-south1-c" ]

# Set the path to your service account credentials JSON file
credentials_file = "./it-services-group-svc-poc-dd27e47f8d35.json"

# Define the required scopes for the API you want to access
scopes = ['https://www.googleapis.com/auth/cloud-platform']

# Load the service account credentials
credentials = google.oauth2.service_account.Credentials.from_service_account_file(credentials_file, scopes=scopes)

# Create a request object for token generation
request = google.auth.transport.requests.Request()

# Generate the token
credentials.refresh(request)

# Get the access token
access_token = credentials.token

payload = {}
headers = {
    'Authorization': f'Bearer {access_token}'
}

data_frames = []  # Store response data frames for each project
recommender = "google.compute.disk.IdleResourceRecommender"

#Iterate over projects and locations

for gcp_project_id in projects_list:
        for location in locations:
            url = f"https://recommender.googleapis.com/v1/projects/{gcp_project_id}/locations/{location}/recommenders/{recommender}/recommendations"
            # print(url)
            response = requests.request("GET", url, headers=headers, data=payload)
            print(response.json())
            print(f"project {gcp_project_id} response {response.text}")


recommender2 = "google.compute.image.IdleResourceRecommender"

# # Iterate over projects and locations
# for gcp_project_id in projects_list:
#     for location in locations:
#         url2 = f"https://recommender.googleapis.com/v1/projects/{gcp_project_id}/locations/{location}/recommenders/{recommender2}/recommendations"
#         # print(url2)
#         response2 = requests.request("GET", url2, headers=headers, data=payload)
#         print(response2.json())