import os
import re
import json
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from dotenv import load_dotenv

# environment variables
load_dotenv()
CHROME_DRIVER = os.getenv("chrome_driver_url")
ZIP_CODE_BASE = os.getenv("zipcode_base_url")
ZIP_CODE_SUFFIX = os.getenv("zipcode_suffix_url")


def parse_neighborhoods(borough):
    column_name = borough.split(".")[0].replace("-", " ").title()
    filename = "./boroughs/" + borough
    borough_df = pd.read_csv(filename, sep='\n')
    return [borough_df, column_name]


def get_aliases():
    aliases = dict()
    aliases["Garment District"] = "Fashion District"
    aliases["West Chelsea"] = "Chelsea"
    aliases["Midtown Center"] = "Midtown"
    aliases["Midtown South Central"] = "Midtown South"
    aliases["Gramercy Park"] = "Gramercy"
    aliases["Clinton"] = "Hells Kitchen"
    aliases["Stuyvesant"] = "Stuyvesant Heights"
    aliases["Flatiron"] = "Flatiron District"
    aliases["Greenwood"] = "Greenwood Heights"
    aliases["14th Street Union Square"] = "14th Street"
    return aliases


def find_unknown_zip_codes():
    unknown_codes = dict()
    unknown_codes["flatiron"] = ["10010", "10011", "10012"]
    unknown_codes["fort george"] = ["10040"]
    unknown_codes["koreatown"] = ["10001", "10018"]
    unknown_codes["lincoln square"] = ["10023"]
    unknown_codes["nomad"] = ["10010"]
    unknown_codes["midtown manhattan"] = ["10017", "10018", "10022", "10036"]
    unknown_codes["midtown south"] = ["10001"]
    unknown_codes["times square"] = ["10108", "10109"]
    unknown_codes["14th street union square"] = ["10003", "10009", "10011", "10014"]
    return unknown_codes


def google_search(search, search_definition,  driver):
    driver.get(f"https://www.google.com/search?q={search + search_definition}")
    page_soup = BeautifulSoup(driver.page_source, "html.parser")
    city_links = page_soup.find_all("a", href=re.compile(r"(city-data)"))
    city_link = city_links[0].attrs["href"]
    city_list = re.split(r"&|\?q=|\?sa=", city_link)
    parsed_city_link = [link for link in city_list if link.startswith("http")][0]
    return parsed_city_link


def get_city_data_details(search, driver):
    """
    Data retrieved from city-data website: https://www.city-data.com/

    :param search: Formatted search query term for neighborhood
    :param driver: Webdriver from Selenium
    :return: List -> All zip codes for specified neighborhood
    """

    city_data = " city data nyc"
    aliases = get_aliases()
    if search in list(aliases.keys()):
        search = aliases[search]

    # Conducts a google search with specified search term to find website link in results
    city_link = google_search(search, city_data, driver)

    driver.get(city_link)
    page_source = BeautifulSoup(driver.page_source, "html.parser")
    zip_code = page_source.find_all("a", href=re.compile(r"\/zips\/"))
    all_codes = set([code.text for code in zip_code])
    return list(all_codes)


def call_selenium_drivers(url, search):
    driver = webdriver.Chrome(CHROME_DRIVER)
    driver.implicitly_wait(5)
    driver.get(ZIP_CODE_BASE + url + ZIP_CODE_SUFFIX)

    page_source = BeautifulSoup(driver.page_source, 'html.parser')
    zip_code = page_source.find_all("a", href=re.compile(r"^/zip/"))
    all_zip_codes = []

    if len(zip_code) > 0:
        for code in zip_code:
            all_zip_codes.append(code.text.strip())
    else:
        all_zip_codes = get_city_data_details(search, driver)
        if len(all_zip_codes) <= 0:
            unknown_codes = find_unknown_zip_codes()
            if search in list(unknown_codes.keys()):
                all_zip_codes = unknown_codes[str(search)]

    print(search, all_zip_codes)
    driver.quit()
    return all_zip_codes


def get_zip_codes(dataframes):
    """
    :param dataframes: Two dataframes
          (1) - base borough dataframe
          (2) - borough name
    :return: Dataframe -> Structured and formatted dataframe
    """
    borough_data, column_name = dataframes

    borough_data["url_names"] = borough_data[column_name].str.replace(" ", "-")
    borough_data["search_names"] = borough_data[column_name].str.lower()
    borough_data["zipCodes"] = borough_data.apply(lambda row: call_selenium_drivers(row["url_names"], row["search_names"]), axis=1)
    borough_data["neighborhood"] = borough_data[column_name]

    borough_data.drop([column_name, 'url_names', 'search_names'], axis=1)
    return borough_data


def convert_borough_data(borough, borough_name):
    with open('../scraped_data/borough_schema/' + borough_name + ".json", 'w', encoding='utf-8') as json_file:
        borough_json = borough.to_json(orient="records")
        parsed_json = json.loads(borough_json)
        borough_dict = {borough_name: list(parsed_json)}
        json.dump(borough_dict, json_file, ensure_ascii=False, indent=4)


def borough_parse(parse, borough, borough_name):
    if parse != "skip":
        df_arr = parse_neighborhoods(borough)
        borough_data = get_zip_codes(df_arr)
        convert_to_json = input("Convert " + borough_name + " data to json format? (yes/no) => ")
        if convert_to_json == "yes":
            print("Writing to file ...")
            convert_borough_data(borough_data, borough_name.lower())
        else:
            print("Will not convert data json ...")
    else:
        print("Skipping borough: " + borough_name + " ... ")


def main():
    borough_files = os.listdir("./boroughs")
    for borough in borough_files:
        name = borough.split(".")[0].replace("-", " ").title()
        parse_borough = input(name + " => ")
        borough_parse(parse_borough, borough, name)


if __name__ == '__main__':
    main()

