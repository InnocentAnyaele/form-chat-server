from dotenv import load_dotenv
load_dotenv()
import os

class Config():
    BEARER_TOKEN = os.getenv('BEARER_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    HARDCODED_INDEX_KEY = '36b47640-809f-11ee-9d47-20c19bff2da4'

    
class DevelopmentConfig(Config):
    DEBUG = True
