import mysql.connector
import yaml
import json

# Configure db
with open('db.yaml', 'r') as file:
    db = yaml.load(file, Loader=yaml.FullLoader)

costPerDisk = dict()

conn = mysql.connector.connect(
    host = db['mysql_host'],
    user = db['mysql_user'],
    password = db['mysql_password'],
    database = db['mysql_db']
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

with open('AP1-Data.json', 'r') as file:
    API1_Object = json.load(file)

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

#For Dummy data
# Load the JSON data from the file, 
# CHANGE THIS
json_data = None
arrObject = None
with open('dummyData.json', 'r') as file:
    arrObject = json.load(file)

if 'insights' in arrObject:
    print('existent') 

    # Execute a SELECT query to retrieve data from the table
    table_name = 'unused_disks'  # Replace with the actual table name
    #query = f"SELECT * FROM {table_name}"   #The {table_name} expression inside the f-string is replaced with the value stored in the table_name variable. So the resulting query string will be "SELECT * FROM bu_names" if table_name is set to 'bu_names'.
    # insertInUnusedDisksQuery = f"INSERT INTO unused_disks (disk_name, description, Cloud_id, BU_id, Project_name, Last_Refresh_Time, Last_Use_Time, isBlank) VALUES ({json_data['description'].split(' ')[1][1:-1]}, {json_data['description']}, 1, 0, 'Get from API', {json_data['content']['diskLastUseTime'][0:10]}, {json_data['lastRefreshTime'][0:10]}, {json_data['content']['isBlank']})"
    for json_data in arrObject['insights']:
        insertInUnusedDisksQuery = "INSERT INTO unused_disks (disk_name, description, Cloud_id, BU_id, Project_name, Last_Refresh_Time, Last_Use_Time, isBlank, Cost_Saved) VALUES (%s, %s, 1, 18, 'Get from API', %s, %s, %s, %s)"

        values = (
            json_data['description'].split(' ')[1][1:-1],
            json_data['description'],
            json_data['content']['diskLastUseTime'][0:10],
            json_data['lastRefreshTime'][0:10],
            json_data['content']['isBlank'],
            costPerDisk[json_data['description'].split(' ')[1][1:-1]]
        )

        cursor.execute(insertInUnusedDisksQuery, values)
        conn.commit()

    #execute() method of the cursor object is used to execute a SQL query, and the fetchall() method retrieves all rows from the result set.
    # Close the cursor and connection Closing the cursor is necessary to release any resources held by the cursor and to free up the database server resources.
    cursor.close()
else:
    print('non-existent') 

conn.close()