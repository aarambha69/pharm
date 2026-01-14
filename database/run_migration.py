import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables from backend directory
load_dotenv('../backend/.env')

# Connect to database
db = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASS', ''),
    database=os.getenv('DB_NAME', 'Pharmacy_Management')
)

cursor = db.cursor()

# Read and execute the SQL file
with open('fix_profile_pic.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()
    
# Split by semicolons and execute each statement
statements = sql_script.split(';')
for statement in statements:
    statement = statement.strip()
    if statement:
        try:
            cursor.execute(statement)
            print(f"✓ Executed: {statement[:60]}...")
        except Exception as e:
            print(f"✗ Error: {e}")
            print(f"  Statement: {statement[:100]}...")

db.commit()
cursor.close()
db.close()

print("\n✅ Database schema updated successfully!")
