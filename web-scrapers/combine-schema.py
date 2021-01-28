import os
import json


def combine_schema(borough_name):
    borough_name = borough_name.lower()
    neighborhood_data = ""
    with open('../scraped_data/borough_schema/' + borough_name + ".json", 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        for zipCodes in data[borough_name]:
            with open('../scraped_data/neighborhood_schema/' + borough_name + ".json", 'r+', encoding='utf-8') as zipcode_file:
                neighborhood_data = json.load(zipcode_file)
                for neighborhood in neighborhood_data[borough_name]:
                    neighborhood["zipCodes"] = zipCodes["zipCodes"]
    with open('../scraped_data/neighborhood_schema/' + borough_name + ".json", 'w', encoding='utf-8') as combined_file:
        json.dump(neighborhood_data, combined_file, sort_keys=True, indent='\t', separators=(',', ': '))


def main():
    borough_files = os.listdir("./boroughs")
    for borough in borough_files:
        name = borough.split(".")[0].replace("-", " ").title()
        parse_borough = input(name + " => ")
        if parse_borough != "skip":
            convert_to_json = input("Convert " + name + " data to json format? (yes/no) => ")
            if convert_to_json == "yes":
                print("Writing to file ...")
                combine_schema(name)
            else:
                print("Will not convert data json ...")
        else:
            print("Skipping borough: " + name + " ... ")


if __name__ == '__main__':
    main()