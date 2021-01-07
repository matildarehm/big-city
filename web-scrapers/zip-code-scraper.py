from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import re
import pandas as pd
from tabulate import tabulate
import os
from dotenv import load_dotenv

# environment variables
load_dotenv()
CHROME_DRIVER = os.getenv("chrome_driver_url")
ZIP_CODE_BASE = os.getenv("zipcode_base_url")
ZIP_CODE_SUFFIX = os.getenv("zipcode_suffix_url")


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
    driver.implicitly_wait(5)
    driver.get(ZIP_CODE_BASE + row + ZIP_CODE_SUFFIX)
    page_source = BeautifulSoup(driver.page_source, 'html.parser')
    zip_code = page_source.find_all("a", href=re.compile(r"^/zip/"))
    all_zip_codes = []

    if len(zip_code) > 0:
        for zip in zip_code:
            all_zip_codes.append(zip.text.strip())
    print(row, all_zip_codes)
    driver.quit()
    return all_zip_codes


def get_zip_codes(dataframes):
    data = dataframes[0]
    column_names = dataframes[1]
    for index, borough_data in enumerate(data):
        borough_data['url_names'] = borough_data[column_names[index]].str.replace(" ", "-")
        borough_data.apply(lambda row: call_selenium_drivers(row["url_names"], column_names[index]), axis=1)
        print(borough_data)


def main():
    borough_files = os.listdir("./boroughs")
    df_arr = parse_neighborhoods(borough_files)
    get_zip_codes(df_arr)


if __name__ == '__main__':
    main()

