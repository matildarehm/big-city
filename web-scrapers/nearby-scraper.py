import os
import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from urllib.request import urlopen

# environment variables
load_dotenv()
CHROME_DRIVER = os.getenv("chrome_driver_url")
FIREFOX_DRIVER = os.getenv("firefox_driver_url")
NEARBY_BASE_URL = os.getenv("nearby_base_url")
ELEGRAN_BASE_URL = os.getenv("elegran_base_url")


def parse_neighborhoods(borough):
    column_name = borough.split(".")[0].replace("-", " ").title()
    filename = "./boroughs/" + borough
    borough_df = pd.read_csv(filename, sep='\n')
    return [borough_df, column_name]


def get_compass_details(driver, url):
    driver.get(NEARBY_BASE_URL + url)
    page_source = BeautifulSoup(driver.page_source, "html.parser")
    subway_stations = page_source.find_all("img", alt=re.compile(r"^[a-z0-9]( transit)$"))
    nearby_neighborhoods = page_source.find_all("div", {"class": "neighborhoodGuides-locationDetailsBoundary"})
    nearby = []
    if len(subway_stations) > 0:
        all_nearby = re.split(r" and the |,|Nearby Neighborhoods |[\n]| and ", str(nearby_neighborhoods[-1].text))
        nearby = list(filter(lambda near: not (near is None) and len(str(near).replace(" ", "")) > 2, all_nearby))
    return [subway_stations, nearby]


def get_moovit_details(driver, search):
    subway_lines = "nearby subway lines moovit"
    page_search = requests.get(f"https://www.google.com/search?q={search + subway_lines}")
    page_soup = BeautifulSoup(page_search.content, "html.parser")
    moovit_link = page_soup.find("a", href=re.compile(r"(moovitapp)")).attrs['href']
    moovit_list = re.split(r"&|\?q=|\?sa=", moovit_link)
    parsed_moovit_link = [link for link in moovit_list if link.startswith("http")][0]
    driver.get(parsed_moovit_link)
    other_page_source = BeautifulSoup(driver.page_source, "html.parser")
    other_subway_stations = other_page_source.find_all("a", {"class": "line-link"})
    return other_subway_stations


def get_elegran_details(driver, url):
    driver.get(ELEGRAN_BASE_URL + url)
    page_soup = BeautifulSoup(driver.page_source, "html.parser")
    nearby_neighborhoods = []
    nearby = page_soup.find_all("a", {"class": "border-link"})
    for near in nearby:
        elegran_list = re.split(r"All ", str(near.text))
        nearby = list(filter(lambda neighborhood: not (neighborhood is None) and len(str(neighborhood)) > 2, elegran_list))[0]
        nearby_neighborhoods.append(nearby)
    return nearby_neighborhoods


def get_urban_edge_details(driver, search):
    neighborhood = "urbanedge nearby neighborhoods"
    page_search = driver.get(f"https://www.google.com/search?q={search + neighborhood}")
    page_soup = BeautifulSoup(driver.page_source, "html.parser")
    urban_edge_list = page_soup.find_all("a")
    urban_edge_pattern = re.compile(r"(urbanedge.apartments)")
    ue_list = [x.get("href") for x in urban_edge_list if urban_edge_pattern.search(str(x.get("href")))]
    parsed_urban_link = [link for link in ue_list if link.startswith("http")][0]
    print(parsed_urban_link)
    driver.quit()
    driver = webdriver.Firefox(FIREFOX_DRIVER)
    driver.get(parsed_urban_link)
    driver.set_window_position(0, 0)
    driver.set_window_size(100000, 200000)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)
    all_neighborhoods = []
    other_page_source = BeautifulSoup(driver.page_source, "html.parser")
    other_neighborhoods = other_page_source.find_all("section", {"class": "nearby-neighborhoods"})
    print(other_neighborhoods)
    for section in other_neighborhoods:
        neighborhood_area = section.find_all("h3")
        for area in neighborhood_area:
            print(area.text)
            all_neighborhoods.append(area.text)
    #         print(area.get_text())
    # return all_neighborhoods


def call_selenium_drivers(url, search):
    nearby_neighborhoods = []
    driver = webdriver.Chrome(CHROME_DRIVER)
    subway_stations, nearby_neighborhoods = get_compass_details(driver, url)

    stations = set()
    if len(subway_stations) > 0:
        for subway in subway_stations:
            stations.add(str(subway["alt"].split()[0]).upper())
    else:
        other_subway_stations = get_moovit_details(driver, search)
        if len(other_subway_stations) > 0:
            for other_subway in other_subway_stations:
                if len(other_subway.text) < 2:
                    stations.add(str(other_subway.text).upper())
                elif "x" in str(other_subway.text):
                    stations.add(str(other_subway.text).split("x")[0].upper())
        nearby_neighborhoods = get_elegran_details(driver, url)
        if len(nearby_neighborhoods) == 0:
            nearby_neighborhoods = get_urban_edge_details(driver, search)

    driver.quit()
    print(search)
    print("subway stations: ", list(stations))
    print("nearby neighborhoods: ", nearby_neighborhoods)
    return list(stations), nearby_neighborhoods


def get_subway_stations(dataframes):
    borough_data = dataframes[0]
    column_name = dataframes[1]

    borough_data["url_names"] = borough_data[column_name].str.lower()
    borough_data["url_names"] = borough_data["url_names"].str.replace(" ", "-")
    borough_data["search_names"] = borough_data["url_names"].str.replace("-", " ")

    borough_data["neighborhoods"] = borough_data.apply(lambda row: call_selenium_drivers(row["url_names"],
                                                                                         row["search_names"]), axis=1)
    borough_data[['subway_lines', 'nearby_neighborhoods']] = pd.DataFrame(borough_data["neighborhoods"].tolist(),
                                                                              index=borough_data.index)
    return borough_data


def main():
    borough_files = os.listdir("./boroughs")
    for borough in borough_files:
        name = borough.split(".")[0].replace("-", " ").title()
        parse_borough = input(name + " => ")
        if parse_borough != "skip":
            df_arr = parse_neighborhoods(borough)
            borough_data = get_subway_stations(df_arr)
        else:
            print("Skipping borough: " + name + " ... ")


if __name__ == '__main__':
    main()
