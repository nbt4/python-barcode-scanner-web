import os
from dotenv import load_dotenv

load_dotenv()

print("Environment Variables:")
print(f"MYSQL_HOST={os.getenv('MYSQL_HOST')}")
print(f"MYSQL_DATABASE={os.getenv('MYSQL_DATABASE')}")
print(f"MYSQL_USER={os.getenv('MYSQL_USER')}")
