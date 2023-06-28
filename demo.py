import mysql.connector
import yaml

# Configure db
with open('db.yaml', 'r') as file:
    db = yaml.load(file, Loader=yaml.FullLoader)
conn = mysql.connector.connect(
    host = db['mysql_host'],
    user = db['mysql_user'],
    password = db['mysql_password'],
    database = db['mysql_db']
)

if conn.is_connected():
    print('Connected to MySQL database')
