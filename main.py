from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import requests
import os
import json
from dotenv import load_dotenv
import re

from collections import Counter

load_dotenv()

api_key = os.environ.get("RAPID_API_KEY")

def setup_driver():
    options = webdriver.ChromeOptions()
    # I skiped headless mode for now
    driver = webdriver.Chrome(options=options)
    return driver

def scrape_elpais_opinion(driver):
    url = "https://elpais.com/opinion/"
    driver.get(url)

    # annoying cookie consent banner 
    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
        )
        accept_button.click()
    except TimeoutException:
        pass # no banner

    # articles element 
    articles = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "article"))
    )[:5]

    results = []
    for article in articles:
        data = {"title": None, "link": None, "image_url": None, "content": None}
        try:
            header = article.find_element(By.TAG_NAME, "h2")
            link_element = header.find_element(By.TAG_NAME, "a")
            content = article.find_element(By.TAG_NAME, "p")
            data["content"] = content.text
            data["title"] = header.text
            data["link"] = link_element.get_attribute("href")
        except NoSuchElementException as e:
            print(f"Error: {e}")
            continue
        try:
            img_element = article.find_element(By.TAG_NAME, "img")
            data["image_url"] = img_element.get_attribute("src")
            
        except NoSuchElementException:
            data["image_url"] = None 

        results.append(data)

    return results

def translate_espanyol_to_eng(title, content):
    url = "https://google-translate113.p.rapidapi.com/api/v1/translator/json"
    payload = {
        "from": "es", 
        "to": "en",
        "json": {"title": title, "content":content}
    }
    headers = {
	"x-rapidapi-key": api_key,
	"x-rapidapi-host": "google-translate113.p.rapidapi.com",
	"Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()['trans']


def save_image(link):
    #check if dir exits
    if not link:
        return 0

    directory = '/cover_image'
    try:
        os.makedirs('/cover_image', exist_ok=True)
    except Exception as e:
        print(f"Couldn't create directory: {e}")
    try:

        response = requests.get(link, stream=True) #we stream for large images 
        response.raise_for_status()  
        clean = link.split('/')[-1]
        clean = clean[0:clean.find('?')]
        image_path = directory + '/' + clean
        with open(image_path, 'wb') as file:
            for chunk in response.iter_content(1024): # chunking, again for large images 
                file.write(chunk)
        print(f"Image saved: {image_path}")
    except Exception as e:
        print("Failed to download image")
        
def wods_repeated_twice(titles):
    #input is a list of all the eng titles,
    if titles:
        text = " ".join(titles).lower()
        words = re.findall(r"[a-z0-9'-]+", text) # ignores puntuation and other stuff 
        word_counts = Counter(words)
        frequent_words = {
        word: count 
        for word, count in word_counts.items() 
        if count > 2} # removes any words that aren't repeated 2 times  
        return frequent_words
    


if __name__ == "__main__":
    driver = setup_driver()
    try:
        extracted_data = scrape_elpais_opinion(driver)
        titles = []
        for i, item in enumerate(extracted_data, 1):
            print(f"Article {i}:")
            print(f"Title: {item['title']}")
            print(f"Content: {item['content']}")
            print(f"Link: {item['link']}")
            print(f"Image URL: {item['image_url']}")
            save_image(item["image_url"])
            # translate
            english = translate_espanyol_to_eng(item['title'], item['content'])
            title_en = english['title']
            content_en = english['content']

            titles.append(title_en)
            # print(type(english))
            print("\nTranslated English verion:")
            print(f"Title: {title_en}")
            print(f"Content: {content_en}")

        # I am only checking for repeated words in titles of all translated english text, because the email said headers and I am a bit confused if the content comes under "header", I assume it doesn't 

        word_count  = wods_repeated_twice(titles)
        print('\nWord Counts')
        for word, count in word_count.items():
            print(f"Word: {word:<10} | Count: {count:>10}")

    finally:
        driver.quit()