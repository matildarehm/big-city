from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import re
import pandas as pd
import requests
import numpy as np
from tabulate import tabulate
import os
from dotenv import load_dotenv

# environment variables
load_dotenv()
CHROME_DRIVER = os.getenv("chrome_driver_url")
NEARBY_BASE_URL = os.getenv("nearby_base_url")


def parse_neighborhoods(boroughs):
    dataframes = []
    columns = []
    for file in boroughs:
        column_name = file.split(".")[0].replace("-", " ").title()
        columns.append(column_name)
        filename = "./boroughs/" + file
        borough_df = pd.read_csv(filename, sep='\n')
        dataframes.append(borough_df)
    return dataframes, columns


def get_compass_details(driver, url):
    driver.get(NEARBY_BASE_URL + url)
    page_source = BeautifulSoup(driver.page_source, "html.parser")
    subway_stations = page_source.find_all("img", alt=re.compile(r"^[a-z0-9]( transit)$"))
    nearby_neighborhoods = page_source.find_all("div", {"class": "neighborhoodGuides-locationDetailsBoundary"})
    nearby = []
    if len(subway_stations) > 0:
        all_nearby = re.split(r" and the |,|Nearby Neighborhoods |(\n)|.", str(nearby_neighborhoods[len(nearby_neighborhoods) - 1].text))
        nearby = list(filter(lambda near: not (near is None) and len(str(near).replace(" ", "")) > 2, all_nearby))
    return [subway_stations, nearby]


def get_moovit_details(driver, search):
    subway_lines = "subway lines moovit"
    page_search = requests.get(f"https://www.google.com/search?q={search + subway_lines}")
    page_soup = BeautifulSoup(page_search.content, "html.parser")
    moovit_link = page_soup.find("a", href=re.compile(r"(moovitapp)")).attrs['href']
    moovit_list = re.split(r"&|\?q=|\?sa=", moovit_link)
    parsed_moovit_link = [link for link in moovit_list if link.startswith("http")][0]
    driver.get(parsed_moovit_link)
    other_page_source = BeautifulSoup(driver.page_source, "html.parser")
    other_subway_stations = other_page_source.find_all("a", {"class": "line-link"})
    return other_subway_stations


def call_selenium_drivers(url, search):
    driver = webdriver.Chrome(CHROME_DRIVER)
    subway_stations, nearby_neighborhoods = get_compass_details(driver, url)
    print("subway stations", subway_stations, "nearby neighborhoods", nearby_neighborhoods)

    stations = set()
    if len(subway_stations) > 0:
        for subway in subway_stations:
            stations.add(subway["alt"].split()[0])
    else:
        other_subway_stations = get_moovit_details(driver, search)
        if len(other_subway_stations) > 0:
            for other_subway in other_subway_stations:
                if len(other_subway.text) < 2:
                    stations.add(str(other_subway.text).lower())
                elif "x" in str(other_subway.text):
                    stations.add(str(other_subway.text).split("x")[0])

    driver.quit()
    print(nearby_neighborhoods)
    print(search, list(stations), nearby_neighborhoods)
    return list(stations), []


def get_subway_stations(dataframes):
    data = dataframes[0]
    column_names = dataframes[1]
    for index, borough_data in enumerate(data):
        borough_data["url_names"] = borough_data[column_names[index]].str.lower()
        borough_data["url_names"] = borough_data["url_names"].str.replace(" ", "-")
        borough_data["search_names"] = borough_data["url_names"].str.replace("-", " ")
        print(borough_data)
        borough_data["neighborhoods"] = borough_data.apply(lambda row: call_selenium_drivers(row["url_names"],
                                                                                             row["search_names"]), axis=1)
        borough_data[['subway_lines', 'nearby_neighborhoods']] = pd.DataFrame(borough_data["neighborhoods"].tolist(),
                                                                              index=borough_data.index)
        print(borough_data)


def main():
    borough_files = os.listdir("./boroughs")
    df_arr = parse_neighborhoods(borough_files)
    get_subway_stations(df_arr)


if __name__ == '__main__':
    main()
