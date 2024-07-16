from dotenv import load_dotenv
import os

load_dotenv()

DB_CONNECTION_STRING = (
    f"DRIVER={os.getenv('DB_DRIVER')};"
    f"SERVER={os.getenv('SERVER')};"
    f"DATABASE={os.getenv('DATABASE')};"
    f"UID={os.getenv('USERLOGIN')};"
    f"PWD={os.getenv('PASSWORD')}"
)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
BOT_API_TOKEN = os.getenv('BOT_API_TOKEN')
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
PHONE = os.getenv('PHONE')