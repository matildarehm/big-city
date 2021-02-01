import os
import json
import pymongo
from dotenv import load_dotenv

# environment variables
load_dotenv()
NYC_PASS = os.getenv("nyc_villager_password")
NYC_USR = os.getenv("nyc_villager_user")
CLUSTER_NAME  = os.getenv("nyc_cluster_name")


def parse_boroughs(borough):
    column_name = borough.split(".")[0].replace("-", " ").title()
    return column_name


def load_borough_schema(borough):
    with open('../scraped_data/borough_schema/' + borough + ".json") as f:
        file_data = json.load(f)
        all_data = file_data[borough.lower()]
        return all_data


def load_neighborhood_schema(borough):
    with open('../scraped_data/neighborhood_schema/' + borough + ".json") as f:
        file_data = json.load(f)
        all_data = file_data[borough.lower()]
        return all_data


def borough_parse(db, parse, borough_name):
    if parse != "skip":
        borough_collection = load_borough_schema(borough_name)
        print(borough_collection)
        db.borough.insert_many(borough_collection)
        neighborhood_collection = load_neighborhood_schema(borough_name)
        print(neighborhood_collection)
        db.neighborhood.insert_many(neighborhood_collection)
    else:
        print("Skipping borough: " + borough_name + " ... ")


def main():
    client = pymongo.MongoClient("mongodb+srv://" + NYC_USR + ":" + NYC_PASS + "@" + CLUSTER_NAME + ".uj5zr.mongodb.net")
    db = client.get_database("village-nyc")
    borough_files = os.listdir("./boroughs")
    for borough in borough_files:
        name = borough.split(".")[0].replace("-", " ").lower()
        parse_borough = input(name + " => ")
        borough_parse(db, parse_borough, name)


if __name__ == '__main__':
    main()
