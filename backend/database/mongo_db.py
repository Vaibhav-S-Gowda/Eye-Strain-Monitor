from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client["eye_health_logs"]

collection = db["monitoring_data"]


def save_log(data):

    collection.insert_one(data)


def get_latest():

    return collection.find().sort("_id",-1).limit(1)[0]