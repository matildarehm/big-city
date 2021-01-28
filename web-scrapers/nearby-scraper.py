import os
import re
import time
import json
import requests
import pandas as pd
from csv import writer
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver

# environment variables
load_dotenv()
CHROME_DRIVER = os.getenv("chrome_driver_url")
GECKO_DRIVER = os.getenv("gecko_driver_url")
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
        all_nearby = re.split(r" and the |,|Nearby Neighborhoods |[\n]| and |\.", str(nearby_neighborhoods[-1].text))
        nearby = list(filter(lambda near: not (near is None) and len(str(near).replace(" ", "")) > 2, all_nearby))
        nearby = [str(n).rstrip().lstrip() for n in nearby]
    return [subway_stations, nearby]


def google_search_request(search, search_definition):
    page_search = requests.get(f"https://www.google.com/search?q={search + search_definition}")
    page_soup = BeautifulSoup(page_search.content, "html.parser")
    all_links = page_soup.find("a", href=re.compile(r"(moovitapp)")).attrs['href']
    parsed_list = re.split(r"&|\?q=|\?sa=", all_links)
    parsed_link = [link for link in parsed_list if link.startswith("http")][0]
    return parsed_link


def google_search_driver(search, search_definition, driver):
    driver.get(f"https://www.google.com/search?q={search + search_definition}")
    page_soup = BeautifulSoup(driver.page_source, "html.parser")
    urban_edge_list = page_soup.find_all("a")
    urban_edge_pattern = re.compile(r"(urbanedge.apartments)")
    ue_list = [x.get("href") for x in urban_edge_list if urban_edge_pattern.search(str(x.get("href")))]
    urban_link = [link for link in ue_list if link.startswith("http")][0]
    return urban_link


def get_moovit_details(driver, search):
    subway_lines = "nearby nyc subway lines moovit"
    moovit_link = google_search_request(search, subway_lines)
    driver.get(moovit_link)
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


def get_aliases():
    aliases = dict()
    aliases["Garment District"] = "Fashion District"
    aliases["West Chelsea"] = "Chelsea"
    aliases["Midtown Center"] = "Midtown"
    aliases["Midtown South Central"] = "Midtown South"
    aliases["Gramercy Park"] = "Gramercy"
    aliases["Clinton"] = "Hells Kitchen"
    aliases["Stuyvesant"] = "Stuyvesant Heights"
    aliases["Greenwood"] = "Greenwood Heights"
    return aliases


def search_for_unknown(search, borough, alias, renamed):
    """
    :param search: Search query term
    :param borough: Name of borough to search
    :param alias: Alias of neighborhood
    :param renamed: Aliases dictionary store
    :return: Boolean -> Based on whether or not the neighborhood was found
            True - Was unknown and not found
            False - Was found
    """
    no_apostrophes = str(alias).replace("'", "")
    if no_apostrophes in list(renamed.keys()):
        no_apostrophes = renamed[no_apostrophes]
    if no_apostrophes not in borough.values:
        print("NO APOSTROPHES" + no_apostrophes + "done")
        with open('./neighborhoods/unable_to_find.csv', 'a') as f_object:
            writer_object = writer(f_object)
            writer_object.writerow([search, alias])
            f_object.close()
        return True
    return False


def get_urban_edge_details(driver, search, borough):
    renamed, all_neighborhoods = get_aliases(), []

    neighborhood = " urbanedge nyc nearby neighborhoods"
    urban_link = google_search_driver(search, neighborhood, driver)
    driver = webdriver.Firefox(executable_path=GECKO_DRIVER, log_path='./logs/geckodriver.log')
    driver.get(urban_link)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    time.sleep(10)
    other_page_source = BeautifulSoup(driver.page_source, "html.parser")
    other_neighborhoods = other_page_source.find_all("section", {"class": "nearby-neighborhoods"})

    for section in other_neighborhoods:
        neighborhood_area = section.find_all("h3")
        for area in neighborhood_area:
            area_text = str(area.text).split(".")[0].lstrip().rstrip()
            aliases = area_text.split(" / ")
            if len(aliases) > 1:
                for x in aliases:
                    no_apostrophes = str(x).replace("'", "")
                    if not search_for_unknown(search, borough, x, renamed):
                        all_neighborhoods.append(no_apostrophes)
            elif len(area_text.split(" & ")) > 1:
                aliases = area_text.split(" & ")
                for x in aliases:
                    no_apostrophes = str(x).replace("'", "")
                    if not search_for_unknown(search, borough, x, renamed):
                        all_neighborhoods.append(no_apostrophes)
            else:
                no_apostrophes = str(area_text).replace("'", "")
                if no_apostrophes in list(renamed.keys()):
                    no_apostrophes = renamed[no_apostrophes]
                all_neighborhoods.append(no_apostrophes)
                if no_apostrophes not in borough.values:
                    with open('./neighborhoods/unable_to_find.csv', 'a') as f_object:
                        writer_object = writer(f_object)
                        writer_object.writerow([search, area_text])
                        f_object.close()
    driver.quit()
    return list(set(all_neighborhoods))


def call_selenium_drivers(url, search, borough):
    nearby_neighborhoods = []
    driver = webdriver.Chrome(CHROME_DRIVER)
    subway_stations, nearby_neighborhoods = get_compass_details(driver, url)

    stations = set()
    if len(subway_stations) > 0:
        for subway in subway_stations:
            stations.add(str(subway["alt"].split()[0]).upper())
        near = []
        for nearby in nearby_neighborhoods:
            no_apostrophes = nearby.replace("'", "")
            renamed = get_aliases()
            if no_apostrophes in list(renamed.keys()):
                near.append(renamed[no_apostrophes])
            else:
                near.append(no_apostrophes)
        nearby_neighborhoods = near
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
            nearby_neighborhoods = get_urban_edge_details(driver, search, borough)

    driver.quit()
    print(search)
    print("subway stations: ", list(stations))
    print("nearby neighborhoods: ", nearby_neighborhoods)
    return list(stations), nearby_neighborhoods


def get_subway_stations(dataframes):
    borough_data, column_name = dataframes

    borough_data["search_names"] = borough_data[column_name].str.lower()
    borough_data["url_names"] = borough_data["search_names"].str.replace(" ", "-")

    borough_data["neighborhoods"] = borough_data.apply(lambda row: call_selenium_drivers(row["url_names"],
                                                                                         row["search_names"],
                                                                                         borough_data[column_name]), axis=1)
    borough_data[['subway_lines', 'nearby_neighborhoods']] = pd.DataFrame(borough_data["neighborhoods"].tolist(),
                                                                          index=borough_data.index)
    borough_data['borough'] = column_name
    borough_data['state'] = "New York"
    borough_data["neighborhood"] = borough_data[column_name]
    borough_data = borough_data.drop([column_name, 'url_names', 'search_names', 'neighborhoods'], axis=1)
    return borough_data


def write_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)


def convert_borough_data(borough, borough_name):
    with open('../scraped_data/neighborhood_schema/' + borough_name + ".json", 'w', encoding='utf-8') as json_file:
        borough_json = borough.to_json(orient="records")
        parsed_json = json.loads(borough_json)
        borough_dict = {borough_name: list(parsed_json)}
        json.dump(borough_dict, json_file, ensure_ascii=False, indent=4)


def borough_parse(parse, borough, borough_name):
    if parse != "skip":
        df_arr = parse_neighborhoods(borough)
        borough_data = get_subway_stations(df_arr)
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
