import mysql.connector
import yaml
import json
import requests
import google.oauth2.service_account
import google.auth.transport.requests
import pandas as pd
import datetime
import os
from google.cloud import storage
import time

#OLD
# mysql_host: 'localhost'
# mysql_user: 'root'
# mysql_password: 'root'
# mysql_db: 'adanidb'

# Configure db
with open('db.yaml', 'r') as file:
    db_config = yaml.load(file, Loader=yaml.FullLoader)['db']

# Connect to the MySQL database
conn = mysql.connector.connect(
    host=db_config['host'],
    port=db_config['port'],
    user=db_config['user'],
    password='',
    database=db_config['database']
)


if conn.is_connected():
    print('Connected to MySQL database')
    print()

# Create a cursor object to execute SQL queries
#a cursor is an object that allows you to retrieve and manipulate data in a database.
cursor = conn.cursor()
clearTable = 'DELETE FROM unused_disks'
cursor.execute(clearTable)      #this will first empty the table in database
conn.commit()

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


#it group and corp are ael, and have the same id
#natural and naturalrs have the same id - represented by natural
#21 will be other. those that dont have specified bu, will be put here
business_units = {'adl':1, 'aeml':2, 'agel': 3, 'airport': 4, 'anil': 5, 'apac': 6, 'apsez': 7, 'atgl': 8, 'bunkering': 9, 'capital': 10, 'it': 11, 'group':11, 'corp': 11, 'defense': 12, 'howe':13, 'mpl':14, 'mspvl': 15, 'natural': 16, 'naturalrs':16, 'power':17, 'realty':18, 'transmission': 19, 'systemgsuite': 20, 'other': 21}

payload = {}
headers = {
    'Authorization': f'Bearer {access_token}'
}

data_frames = []  # Store response data frames for each project

json_data = None
arrObject = None

zipped_data = [("google.compute.disk.IdleResourceRecommender", "google.compute.disk.IdleResourceInsight",'unused_disks'), ("google.compute.image.IdleResourceRecommender", "google.compute.image.IdleResourceInsight", 'unused_images'), ( "google.compute.address.IdleResourceRecommender", "google.compute.address.IdleResourceInsight", 'unused_ip')]
#Iterate over projects and locations

for gcp_project_id in projects_list:
        
        business_unit = gcp_project_id.split('-')[0]
        for location in locations:
            for recommender, insight_type, table in zipped_data:
                costPerDisk = dict()
                url = f"https://recommender.googleapis.com/v1/projects/{gcp_project_id}/locations/{location}/recommenders/{recommender}/recommendations"
                # print(url)
                response = requests.request("GET", url, headers=headers, data=payload)
                API1_Object = response.json()
                print(API1_Object)
                print(f"project {gcp_project_id} response {response.text}")

                if 'recommendations' in API1_Object:

                    for obj in API1_Object['recommendations']:
                        nanos = -1 * obj['primaryImpact']['costProjection']['cost']['nanos']
                        units = 0
                        if 'units' in obj['primaryImpact']['costProjection']['cost']:
                            units = obj['primaryImpact']['costProjection']['cost']['units']
                        if units == 0:
                            moneyPerMonth = nanos / 1000000000
                        else:
                            moneyPerMonth = int(units[1:]) + (nanos / 1000000000)
                        costPerDisk[obj['content']['overview']['resourceName']] = moneyPerMonth

                print(costPerDisk)

                url = f"https://recommender.googleapis.com/v1beta1/projects/{gcp_project_id}/locations/{location}/insightTypes/{insight_type}/insights"
                # print(url)
                response = requests.request("GET", url, headers=headers, data=payload)
                arrObject = response.json()
                if 'insights' in arrObject:
                    print('existent') 

                    # Execute a SELECT query to retrieve data from the table
                    table_name = 'unused_disks'  # Replace with the actual table name
                    #query = f"SELECT * FROM {table_name}"   #The {table_name} expression inside the f-string is replaced with the value stored in the table_name variable. So the resulting query string will be "SELECT * FROM bu_names" if table_name is set to 'bu_names'.
                    # insertInUnusedDisksQuery = f"INSERT INTO unused_disks (disk_name, description, Cloud_id, BU_id, Project_name, Last_Refresh_Time, Last_Use_Time, isBlank) VALUES ({json_data['description'].split(' ')[1][1:-1]}, {json_data['description']}, 1, 0, 'Get from API', {json_data['content']['diskLastUseTime'][0:10]}, {json_data['lastRefreshTime'][0:10]}, {json_data['content']['isBlank']})"
                    for json_data in arrObject['insights']:
                        insertInUnusedDisksQuery = f"INSERT INTO {table} (name, description, Cloud_id, BU_id, Project_name, Last_Refresh_Time, Last_Use_Time, isBlank, Cost_Saved) VALUES (%s, %s, 1, %s, %s, %s, %s, %s, %s)"

                        values = (
                            json_data['description'].split(' ')[1][1:-1],
                            json_data['description'],
                            business_units[business_unit] if business_unit in business_units else business_units['other'],
                            gcp_project_id,
                            json_data['content']['diskLastUseTime'][0:10],
                            json_data['lastRefreshTime'][0:10],
                            json_data['content']['isBlank'],
                            costPerDisk[json_data['description'].split(' ')[1][1:-1]] if json_data['description'].split(' ')[1][1:-1] in costPerDisk else 0
                        )

                        cursor.execute(insertInUnusedDisksQuery, values)
                        conn.commit()

                    #execute() method of the cursor object is used to execute a SQL query, and the fetchall() method retrieves all rows from the result set.
                    # Close the cursor and connection Closing the cursor is necessary to release any resources held by the cursor and to free up the database server resources.
                    
                else:
                    print('non-existent') 

            

cursor.close()
conn.close()


























# import mysql.connector
# import yaml
# import json

# #OLD
# # mysql_host: 'localhost'
# # mysql_user: 'root'
# # mysql_password: 'root'
# # mysql_db: 'adanidb'

# # Configure db
# with open('db.yaml', 'r') as file:
#     db_config = yaml.load(file, Loader=yaml.FullLoader)['db']

# # Connect to the MySQL database
# conn = mysql.connector.connect(
#     host=db_config['host'],
#     port=db_config['port'],
#     user=db_config['user'],
#     password='',
#     database=db_config['database']
# )

# costPerDisk = dict()
# if conn.is_connected():
#     print('Connected to MySQL database')
#     print()

# # Create a cursor object to execute SQL queries
# #a cursor is an object that allows you to retrieve and manipulate data in a database.
# cursor = conn.cursor()
# clearTable = 'DELETE FROM unused_disks'
# cursor.execute(clearTable)      #this will first empty the table in database
# conn.commit()

# #for dummy object in local file
# with open('AP1-Data.json', 'r') as file:
#     API1_Object = json.load(file)

# ################################################
# #when using this comment out the code on line 34 and 35
# ## Make the API call and receive the JSON response

# #response = make_api_call()  # Replace with your API call and response handling

# # Parse the JSON response
# #json_data = json.loads(response)
# #####################################################

# if 'recommendations' in API1_Object:

#     for obj in API1_Object['recommendations']:
#         nanos = -1 * obj['primaryImpact']['costProjection']['cost']['nanos']
#         units = 0
#         if 'units' in obj['primaryImpact']['costProjection']['cost']:
#             units = obj['primaryImpact']['costProjection']['cost']['units']
#         if units == 0:
#             moneyPerMonth = nanos / 1000000000
#         else:
#             moneyPerMonth = int(units[1:]) + (nanos / 1000000000)
#         costPerDisk[obj['content']['overview']['resourceName']] = moneyPerMonth

# print(costPerDisk)

# #For Dummy data
# # Load the JSON data from the file, 
# # CHANGE THIS
# json_data = None
# arrObject = None
# with open('dummyData.json', 'r') as file:
#     arrObject = json.load(file)

# if 'insights' in arrObject:
#     print('existent') 

#     # Execute a SELECT query to retrieve data from the table
#     table_name = 'unused_disks'  # Replace with the actual table name
#     #query = f"SELECT * FROM {table_name}"   #The {table_name} expression inside the f-string is replaced with the value stored in the table_name variable. So the resulting query string will be "SELECT * FROM bu_names" if table_name is set to 'bu_names'.
#     # insertInUnusedDisksQuery = f"INSERT INTO unused_disks (disk_name, description, Cloud_id, BU_id, Project_name, Last_Refresh_Time, Last_Use_Time, isBlank) VALUES ({json_data['description'].split(' ')[1][1:-1]}, {json_data['description']}, 1, 0, 'Get from API', {json_data['content']['diskLastUseTime'][0:10]}, {json_data['lastRefreshTime'][0:10]}, {json_data['content']['isBlank']})"
#     for json_data in arrObject['insights']:
#         insertInUnusedDisksQuery = "INSERT INTO unused_disks (disk_name, description, Cloud_id, BU_id, Project_name, Last_Refresh_Time, Last_Use_Time, isBlank, Cost_Saved) VALUES (%s, %s, 1, 2, 'Get from API', %s, %s, %s, %s)"

#         values = (
#             json_data['description'].split(' ')[1][1:-1],
#             json_data['description'],
#             json_data['content']['diskLastUseTime'][0:10],
#             json_data['lastRefreshTime'][0:10],
#             json_data['content']['isBlank'],
#             costPerDisk[json_data['description'].split(' ')[1][1:-1]]
#         )

#         cursor.execute(insertInUnusedDisksQuery, values)
#         conn.commit()

#     #execute() method of the cursor object is used to execute a SQL query, and the fetchall() method retrieves all rows from the result set.
#     # Close the cursor and connection Closing the cursor is necessary to release any resources held by the cursor and to free up the database server resources.
#     cursor.close()
# else:
#     print('non-existent') 

# conn.close()