from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

db = client["archviz"]
users = db["users"]
sessions = db["sessions"]