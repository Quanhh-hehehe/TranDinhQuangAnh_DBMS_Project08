import os
from dotenv import load_dotenv

load_dotenv() 

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""), # Mật khẩu sẽ được kéo từ .env ra
    "database": os.getenv("DB_NAME", "CinemaManagement")
}