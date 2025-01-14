import multiprocessing
import os 
import json 
import time 
import random 
import re 
from typing import List, Dict
from selenium import webdriver 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


# BASE_URL = 'https://archive.aks.ac.kr/letter/letter.do#list.do?itemId=letter&gubun=lettername'
# [한국고문서-Korea Ancient Texts](https://archive.aks.ac.kr/letter/letter.do#list.do?itemId=letter&gubun=lettername)

# 조선왕조실록 - 朝鮮王朝實錄Veritable Records of the Joseon Dynasty 다운로드 가능한 URL 
JOSEON_DYNASTY_URL = 'https://sillok.history.go.kr/'

in_local = True
debug = True
use_multiprocessing = True


def random_sleep():
    """
    Need this function to avoid 'HttpConnectionPool: Read timed out' at the time of collecting data(2024.12.28 ~ 2025.01.xx)
    """
    time.sleep(min(random.random() * 6 + 0.5, random.random() + 3))


def get_action_id(driver: webdriver.Firefox):
    """
    Extracts the actual url for the text(title, hanja and hangul(Korean))
    """
    # Locate the form element by its ID
    form_element = driver.find_element(By.ID, "topSearchForm")
    
    # Extract the 'action' attribute
    action_url = form_element.get_attribute("action")
    return action_url 


def get_contents_links(driver: webdriver.Firefox) -> List[str]:
    """
    Extracts the top-level links (hrefs) from the page's content list.
    
    Args:
        driver (webdriver.Firefox): A Selenium WebDriver instance.

    Returns:
        List[str]: A list of URLs (hrefs) extracted from the top contents of the page.
    """
    link_list = []
    content_list = driver.find_element(By.ID, "m_cont_list")
    target_class_elements = content_list.find_elements(By.CLASS_NAME, "m_cont_top")

    for element in target_class_elements:
        links = element.find_elements(By.TAG_NAME, "a")
        for link in links:
            link_text = link.text.strip()
            # Only collect if the first character is a digit and there's text
            if link_text and link_text[0].isdigit():
                link_list.append(link.get_attribute("href"))
    return link_list


def navigate_to(driver: webdriver.Firefox, xpath: str, timeout: int = 30):
    """
    Waits until the element specified by the given XPath is clickable, then returns it.

    Args:
        driver (webdriver.Firefox): A Selenium WebDriver instance.
        xpath (str): The XPath of the target element.
        timeout (int): Time to wait until the element is clickable.

    Returns:
        WebElement: The clickable web element if found within the timeout period.
    """
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )


def scrape_inn_hrefs(driver: webdriver.Firefox) -> List[str]:
    """
    Scrapes and returns all the inner links for a single mid-level page.

    Args:
        driver (webdriver.Firefox): A Selenium WebDriver instance.

    Returns:
        List[str]: A list of inner hrefs.
    """
    contents = driver.find_element(By.XPATH, '//*[@id="cont_area"]/div[1]/div[3]/div/dl')
    inn_links = contents.find_elements(By.TAG_NAME, "a")
    return [link.get_attribute("href") for link in inn_links]


def scrape_page_data(driver: webdriver.Firefox, out_data: List[Dict]) -> None:
    """
    Scrapes the current page data (title, left_texts, right_texts, and URL), 
    and appends it to out_data if successful.

    Args:
        driver (webdriver.Firefox): A Selenium WebDriver instance.
        out_data (List[Dict]): A list to append the scraped data to.
    """
    try:
        # Custom function assumed to be available
        action_url = get_action_id(driver)
        
        # Title
        text_title = driver.find_element(By.XPATH, '//*[@id="cont_area"]/div[1]/ul[1]').text
        
        # Left Text
        left_text_element = driver.find_element(By.XPATH, '//*[@id="cont_area"]/div[1]/div[3]/div[1]/div/div')
        left_texts = "".join([p.text for p in left_text_element.find_elements(By.TAG_NAME, 'p')])
        
        # Right Text
        right_text_element = driver.find_element(By.XPATH, '//*[@id="cont_area"]/div[1]/div[3]/div[2]/div/div')
        right_texts = "".join([p.text for p in right_text_element.find_elements(By.TAG_NAME, 'p')])
        
        out_data.append({
            "title": text_title,
            "hangul": left_texts,
            "hanja": right_texts,
            "url": action_url,
        })
    except Exception as e:
        # If something fails, print the URL for debugging
        print(f"Exception while scraping page: {e}")


def scrape_mid_level_pages(driver: webdriver.Firefox, mid_hrefs: List[str]) -> List[Dict]:
    """
    Given a list of mid-level URLs, navigates to each one and scrapes
    nested links (inn_hrefs), then scrapes their page data.

    Args:
        driver (webdriver.Firefox): A Selenium WebDriver instance.
        mid_hrefs (List[str]): A list of mid-level URLs.

    Returns:
        List[Dict]: A list of all scraped data from the inn-level pages.
    """
    out_data = []
    for mid_href in mid_hrefs:
        driver.get(mid_href)
        navigate_to(driver, '//*[@id="cont_area"]/div[1]/div[1]/div/span[2]/ul/li[1]/a', timeout=60)
        
        # Get inn_hrefs and iterate
        inn_hrefs = scrape_inn_hrefs(driver)
        for inn_href in inn_hrefs:
            driver.get(inn_href)
            navigate_to(driver, '//*[@id="cont_area"]/div[1]/div[2]/div/a[1]', timeout=60)            
            scrape_page_data(driver, out_data)
            driver.back()
            random_sleep()
            if debug:
                break 
        
        driver.back()
        random_sleep()
        if debug: 
            break 
    return out_data


def scrape_sub_links(driver: webdriver.Firefox, out_href: str) -> List[Dict]:
    """
    Scrapes data from the sub-links of a given top-level URL.

    Args:
        driver (webdriver.Firefox): A Selenium WebDriver instance.
        out_href (str): The top-level URL to navigate to.

    Returns:
        List[Dict]: Collected data from all nested sub-links.
    """
    # Container for all data from this link
    out_data = []

    # Navigate to the top-level link
    navigate_to(driver, '//*[@id="m_cont_list"]/div[1]/ul[4]/li[4]/a', timeout=30)
    driver.get(out_href)
    # navigate_to(driver, '//*[@id="cont_area"]/div/div[2]/ul[3]/li/div/a', timeout=30)
    random_sleep()

    # Find the main table
    table_element = driver.find_element(By.XPATH, '//*[@id="cont_area"]/div/div[2]/ul[2]')
    divs = table_element.find_elements(By.TAG_NAME, "div")
    xpaths = [f'//*[@id="cont_area"]/div/div[2]/ul[2]/li[{i}]/ul' for i in range(1, len(divs) + 1)]

    # Traverse each sub-section
    for xpath in xpaths:
        sub_section = driver.find_element(By.XPATH, xpath)
        links = sub_section.find_elements(By.TAG_NAME, "a")
        mid_hrefs = [link.get_attribute("href") for link in links]
        
        # Scrape each mid-level page
        mid_level_data = scrape_mid_level_pages(driver, mid_hrefs)
        out_data.extend(mid_level_data)

        if debug:
            break 

    return out_data


def get_file_name_from_url(out_href: str) -> str:
    """
    Extracts a sanitized filename from a URL.

    Args:
        url (str): The URL to extract a filename from.

    Returns:
        str: A sanitized filename extracted from the URL.
    """
    # Extract a name from the URL for the pickle file
    # Example: if out_href = "'example(link)'", the regex picks 'example(link)'
    match = re.findall(r"'(.*?)'", out_href)
    if match:
        out_text = match[0]
    else:
        # If there's no match, fallback to a sanitized version of the raw URL
        out_text = re.sub(r'[^a-zA-Z0-9_\-]', '_', out_href)

    filename = out_text.replace('(', '_').replace(')', '_')
    return filename


def get_filepath(filename:str):
    # Change this to the desired directory
    return f"/{filename}.jsonl"


def save_data_to_pickle(filepath: str, data: List[Dict]):
    """
    Saves the given data to a pickle file.

    Args:
        filepath (str): The desired filepath (without .jsonl extension).
        data (List[Dict]): The data to save.
    """
    with open(filepath, 'w') as f:
        for d in data:
            f.write(json.dumps(d) + '\n')


def main_scraper(driver: webdriver.Firefox):
    """
    Main scraping logic. Gets the top-level content links, iterates through them,
    scrapes data, and saves each portion of data to a pickle file.
    """
    out_hrefs = get_contents_links(driver)

    for out_href in out_hrefs:
        filename = get_file_name_from_url(out_href)
        filepath = get_filepath(filename)
        if os.path.exists(filepath):
            print(f"File {filename}.jsonl already exists, skipping...")
            continue
        out_data = scrape_sub_links(driver, out_href)
        print(f"Saving data to {filepath}...")
        # save_data_to_pickle(filepath, out_data)
        driver.back()
        random_sleep()
        if debug:
            break 

def main_scraper_for_multiprocessing(url):
    driver = webdriver.Firefox() 
    driver.get(JOSEON_DYNASTY_URL)
    random_sleep()
    out_data = scrape_sub_links(driver, url)
    filename = get_file_name_from_url(url)
    filepath = get_filepath(filename)
    print(filepath, len(out_data))
    # save_data_to_pickle(filepath, out_data)
    driver.quit()


if __name__ == "__main__":
    if in_local:
        if use_multiprocessing:
            driver = webdriver.Firefox()
            driver.get(JOSEON_DYNASTY_URL)
            out_hrefs = get_contents_links(driver)
            if debug:
                out_hrefs = out_hrefs[:2]
            driver.quit()
            
            processes = []
            for url in out_hrefs:
                p = multiprocessing.Process(target=main_scraper_for_multiprocessing, args=(url,))
                p.start() 
                processes.append(p) 
            
            for p in processes:
                p.join()
        else:
            driver = webdriver.Firefox()
            driver.get(JOSEON_DYNASTY_URL)
            main_scraper(driver)
            driver.quit()
