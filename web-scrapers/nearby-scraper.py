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


def call_selenium_drivers(row, borough_name):
    driver = webdriver.Chrome(CHROME_DRIVER)
    driver.get(NEARBY_BASE_URL + row)
    page_source = BeautifulSoup(driver.page_source, "html.parser")
    subway_stations = page_source.find_all("img", alt=re.compile(r"^[a-z0-9]( transit)$"))

    stations = set()
    if len(subway_stations) > 0:
        for subway in subway_stations:
            stations.add(subway["alt"].split()[0])
        print(row, list(stations))
        driver.quit()
    else:
        driver.quit()
        subway_lines = "subway lines"
        page_search = requests.get(f"https://www.google.com/search?q={row + subway_lines}")
        page_soup = BeautifulSoup(page_search.content, "html.parser")
        moovit_link = page_soup.find("a", href=re.compile(r"(moovitapp)")).attrs['href']
        parsed_moovit_link = moovit_link.split("&")[0].split("?q=")[1]
        driver.get(parsed_moovit_link)
        other_page_source = BeautifulSoup(driver.page_source, "html.parser")
        other_subway_stations = other_page_source.find_all("a", {"class": "line-link"})
        print(other_subway_stations)
        if len(other_subway_stations) > 0:
            for subway in other_subway_stations:
                if len(subway.text) <= 2:
                    stations.add(subway.text)
            print(row, list(stations))
        driver.quit()

    return list(stations)


def get_subway_stations(dataframes):
    data = dataframes[0]
    column_names = dataframes[1]
    for index, borough_data in enumerate(data):
        borough_data["url_names"] = borough_data[column_names[index]].str.lower().replace(" ", "-")
        borough_data["url_names"] = borough_data["url_names"].str.replace(" ", "-")
        print(borough_data["url_names"])
        borough_data["subway_lines"] = borough_data.apply(lambda row: call_selenium_drivers(row["url_names"], column_names[index]), axis=1)

def main():
    borough_files = os.listdir("./boroughs")
    df_arr = parse_neighborhoods(borough_files)
    get_subway_stations(df_arr)


if __name__ == '__main__':
    main()