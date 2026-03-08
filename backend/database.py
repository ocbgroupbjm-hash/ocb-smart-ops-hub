from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'ocb_ai_database')

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Collections - AI Business OS + OCB AI
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

# OCB AI Specific Collections
db.products = products_collection
db.transactions = db['transactions']
db.attendance = db['attendance']
db.kpi_tasks = db['kpi_tasks']
db.kpi_targets = db['kpi_targets']
db.whatsapp_integrations = db['whatsapp_integrations']
db.whatsapp_messages = db['whatsapp_messages']
db.whatsapp_logs = db['whatsapp_logs']
db.whatsapp_templates = db['whatsapp_templates']
db.users = users_collection
db.branches = branches_collection
db.customers = customers_collection
db.knowledge_base = knowledge_base_collection
db.conversations = conversations_collection
db.messages = messages_collection