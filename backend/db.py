import os

from pymongo import ASCENDING, MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.environ.get("MONGO_DB_NAME", "upplands_leads")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users_col = db["users"]
companies_col = db["companies"]
settings_col = db["settings"]
campaigns_col = db["campaigns"]
email_sends_col = db["email_sends"]


def ensure_indexes():
    users_col.create_index("username", unique=True)
    companies_col.create_index("orgnr", unique=True, sparse=True)
    companies_col.create_index([("status", ASCENDING)])
    companies_col.create_index([("county", ASCENDING)])
    companies_col.create_index([("industryCode", ASCENDING)])
    companies_col.create_index([("sniCode", ASCENDING)])
    email_sends_col.create_index([("campaignId", ASCENDING)])
    email_sends_col.create_index([("companyId", ASCENDING)])
    email_sends_col.create_index([("status", ASCENDING)])
