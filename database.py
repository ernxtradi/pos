from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["pos_system"]
inventory_collection = db["inventory"]
orders_collection = db["orders"]
transactions_collection = db["transactions"]