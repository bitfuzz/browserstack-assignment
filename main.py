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
    # Keep it local; the BrowserStack SDK intercepts this automatically
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    return driver

def scrape_elpais_opinion(driver):
    url = "https://elpais.com/opinion/"
    driver.get(url)

    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
        )
        accept_button.click()
    except TimeoutException:
        pass 

    articles = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "article"))
    )

    results = []
    for article in articles:
        if len(results) == 5:
            break
        data = {"title": None, "link": None, "image_url": None, "content": None}
        
        try:
            header = article.find_element(By.TAG_NAME, "h2")
            link_element = header.find_element(By.TAG_NAME, "a")
            data["title"] = header.text
            data["link"] = link_element.get_attribute("href")
        except NoSuchElementException:
            continue 

        try:
            content = article.find_element(By.TAG_NAME, "p")
            data["content"] = content.text
        except NoSuchElementException:
            data["content"] = None 

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
    return response.json().get('trans', {})

def save_image(link):
    if not link:
        return 0

    directory = os.path.join(os.getcwd(), 'cover_image')
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        pass
        
    try:
        response = requests.get(link, stream=True) 
        response.raise_for_status()  
        clean = link.split('/')[-1]
        clean = clean.split('?')[0]
        image_path = os.path.join(directory, clean)
        
        with open(image_path, 'wb') as file:
            for chunk in response.iter_content(1024): 
                file.write(chunk)
        print(f"Image saved: {image_path}")
    except Exception as e:
        print("Failed to download image")
        
def wods_repeated_twice(titles):
    if titles:
        text = " ".join(titles).lower()
        words = re.findall(r"[a-z0-9'-]+", text) 
        word_counts = Counter(words)
        
        frequent_words = {
            word: count 
            for word, count in word_counts.items() 
            if count > 2
        }  
        return frequent_words
    return {}

if __name__ == "__main__":
    driver = setup_driver()
    try:
        extracted_data = scrape_elpais_opinion(driver)
        titles = []
        for i, item in enumerate(extracted_data, 1):
            save_image(item["image_url"])
            
            english = translate_espanyol_to_eng(item['title'], item['content'])
            title_en = english.get('title', '')
            
            if title_en:
                titles.append(title_en)
                
        word_count = wods_repeated_twice(titles)
        print('\nRepeated Words With Count')
        if word_count:
            for word, count in word_count.items():
                print(f"Word: {word:<10} | Count: {count:>10}")
        else:
            print("None")

        # Evaluate execution and explicitly mark the session as Passed/Failed on BrowserStack
        if len(titles) > 0:
            driver.execute_script('browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"passed", "reason": "Data extracted and translated successfully"}}')
        else:
            driver.execute_script('browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"failed", "reason": "Failed to extract required data"}}')

    finally:
        driver.quit()