from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'ai_business_os')

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Collections
users_collection = db['users']
companies_collection = db['companies']
branches_collection = db['branches']
customers_collection = db['customers']
products_collection = db['products']
conversations_collection = db['conversations']
messages_collection = db['messages']
knowledge_base_collection = db['knowledge_base']
workflows_collection = db['workflows']
sales_orders_collection = db['sales_orders']
inventory_collection = db['inventory']
analytics_events_collection = db['analytics_events']