# Selenium Imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# Dataframe and Excel Imports
import pandas as pd
import openpyxl

# Other imports
from datetime import datetime
import random
from icecream import ic
from itertools import cycle
import threading
import queue
import logging as log
from configparser import ConfigParser
import os
from Logging.init_logger import init_logger


log = init_logger()

def get_chrome_options():
    try:
        # Configure Chrome DevTools options
        # options = Options()
        # options.add_experimental_option("w3c", False)
        # options.add_argument("--disable-extensions")
        # options.add_argument("--disable-gpu")
        # options.add_argument("--headless")
        
        config = get_proxy_config()
        
        PROXY_SERVER = config.get('PROXY','PROXY_SERVER')
        PROXY_PORT = config.get('PROXY','PROXY_PORT')
        PROXY_USERNAME = config.get('PROXY','PROXY_USERNAME')
        PROXY_PASSWORD = config.get('PROXY','PROXY_PASSWORD')
        
        options = {
            'proxy': {
                'http' : f'http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_SERVER}:{PROXY_PORT}',
                'https' : f'https://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_SERVER}:{PROXY_PORT}',
                'verify_ssl': False,
            }
        }   
        
        return options
    except Exception as e:
        log.error(f"get_chrome_options : Error : {e}")
        
def get_proxy_config():
    returnValue = None
    try:
        path = os.path.dirname(os.path.realpath(__file__))
        config_filepath = os.path.join(path,"PROXY_CONFIG.ini")
        # check if the config file exists
        exists = os.path.exists(config_filepath)
        config = None
        if exists:
            log.info("--------PROXY_CONFIG.ini file found at ", config_filepath)
            config = ConfigParser()
            config.read(config_filepath)
            returnValue = config
        else:
            log.error("---------PROXY_CONFIG.ini file not found at ", config_filepath)
    except Exception as e:
        log.error(f"get_proxy_config : Error : {e}")
        
    return returnValue

def collect_data(search_term, driver, city=None, latitude=None, longitude=None):
    data = []
    try:
        if ((latitude is not None) and (longitude is not None)):    
            # Set Serach Location
            driver.execute_cdp_cmd('Emulation.setGeolocationOverride', {
                'latitude': latitude,
                'longitude': longitude,
                'accuracy': 100
            })
                       
        # Navigate to search results page
        driver.get(f"https://www.google.com/search?q={search_term}")
        
        # Wait for the page to load
        driver.implicitly_wait(random.randint(5, 20))
        
        # Collect data for sponsored links
        sponsored_links = driver.find_elements(By.XPATH, "//div[@class='uEierd']")
        
        # WebDriverWait(driver, timeout).until(sponsored_links)
        if len(sponsored_links) == 0:
            data.append({
                        "city" : city,
                        "latitude" : latitude,
                        "longitude" : longitude,
                        "search term" : search_term,
                        "link_text": None,
                        "link_url": None,
                        "link_description": None,
                        "additional_data": None,
                        "timestamp" : datetime.now(),
                        "Data Status" : "NOT PRESENT"
                    })
        else:
            log.info(f"No of Sponsored Links for {search_term} : {len(sponsored_links)}")
            for link in sponsored_links:
                link_element = link.find_element(By.TAG_NAME, "a")
                link_text = link_element.text
                link_url = link_element.get_attribute("href")
                link_description = link.find_element(By.TAG_NAME, "span").text
                
                additional_data_elements = link.find_elements(By.CSS_SELECTOR, ".MUxGbd, .yDYNvb, .lyLwlc")
                additional_data = [elem.text for elem in additional_data_elements]
                
                data.append({
                    "city" : city,
                    "latitude" : latitude,
                    "longitude" : longitude,
                    "search term" : search_term,
                    "link_text": link_text,
                    "link_url": link_url,
                    "link_description": link_description,
                    "additional_data": additional_data,
                    "timestamp" : datetime.now(),
                    "Data Status" : "PRESENT"
                })
    except Exception as e:
        log.error(f"collect_data : Error : {e}")    
        
    return data


def data_initialization():
    try:
        cities_excel_file = f'data_{datetime.now().strftime("%Y_%m_%d_%I_%M_%S_%p")}.xlsx'
        cities_df = pd.read_excel('cities_data.xlsx', sheet_name='cities')
        search_term_df = pd.read_excel('cities_data.xlsx', sheet_name='Search Terms')
        results_data = []
        
        with webdriver.Chrome() as driver:

            # driver = webdriver.Chrome()
            driver.options = get_chrome_options()
            # driver.options.add_experimental_option("w3c", False)
            # driver.options.add_argument("--disable-extensions")
            # driver.options.add_argument("--disable-gpu")
            # driver.options.add_argument("--headless")
            
            # Iterate over the cities and collect data for each city
            for i, row in search_term_df.iterrows():
                common_search_term = ''
                common_search_term = f"{row['Common']}"
                data = collect_data(
                    search_term=common_search_term, 
                    driver=driver
                )
                results_data.extend(data)

                for index, city_data in cities_df.iterrows():
                    common_search_term = ''
                    city = city_data["city"]
                    latitude = city_data["latitude"]
                    longitude = city_data["longitude"]
                    search_term = f"{row['City Wise']} {city}"
                    
                    data = collect_data(
                        search_term=search_term,
                        driver=driver, 
                        city=city, 
                        latitude=latitude,
                        longitude=longitude
                    )
                    results_data.extend(data)

        # Create a dataframe from the collected results data
        results_df = pd.DataFrame(results_data)

        # Append the results dataframe to the Excel sheet
        results_sheet_name = "results"

        try:
            with pd.ExcelWriter(cities_excel_file, mode="a", engine="openpyxl") as writer:
                results_df.to_excel(writer, sheet_name=results_sheet_name, index=False, header=not writer.book)

        except FileNotFoundError:
            results_df.to_excel(cities_excel_file, sheet_name=results_sheet_name, index=False)

        print("Data appended to Excel successfully.")
    
    except Exception as e:
        log.error(f"data_initialization : Error : {e}")    
    
    
data_initialization()