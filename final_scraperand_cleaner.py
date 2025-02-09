import json
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import crawl4ai
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

import json
import asyncio
import nest_asyncio
nest_asyncio.apply()
import re
from bs4 import BeautifulSoup

async def extract_children(base_url):
  async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=base_url
        )
        if not result.success:
            print("Crawl failed:", result.error_message)
            return

        # Parse the extracted JSON
        return result

base_url = "https://www.renesas.com"

urls_set = set()
result = asyncio.run(extract_children(base_url + "/en/applications"))
htmlParse = BeautifulSoup(result.html, "html.parser")
application_categories = [a["href"] for a in htmlParse.find("div",class_="paragraph--type--cards").findAll("a")]
for category in application_categories:
  result1 = asyncio.run(extract_children(base_url + category))
  htmlParse1 = BeautifulSoup(result1.html, "html.parser")
  sub_categories = [a["href"] for a in htmlParse1.find("div",class_="rcard").findAll("a")]
  for sub_category in sub_categories:
    result2 = asyncio.run(extract_children(base_url + sub_category))
    htmlParse2 = BeautifulSoup(result2.html, "html.parser")
    applications = [a["href"] for a in htmlParse2.findAll("a",class_="application-category-list__link")]
    for application in applications:
      print(base_url + application)
      urls_set.add(base_url + application)

# Target URLs
urls = list(urls_set)

# List of User Agents (Rotating between requests)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:92.0) Gecko/20100101 Firefox/92.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/92.0.902.55"
]

# File to store all scraped and cleaned data
output_file = "raw_data.json"

# Load existing data if file already exists
try:
    with open(output_file, "r", encoding="utf-8") as f:
        all_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    all_data = []

# Setup Selenium WebDriver
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Rotate User Agent
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f"user-agent={user_agent}")

    # Start browser session
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# Rate limiter: Time delay between requests (in seconds)
RATE_LIMIT = random.randint(10, 20)  # Randomized delay between 10-20 seconds

# Iterate through each URL
for url in urls:
    print(f"🔍 Scraping: {url}")

    # Initialize a new browser session for each request
    driver = setup_driver()

    try:
        # Open the webpage
        driver.get(url)

        # Wait for the page title to load
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "title")))
        page_title = driver.title.strip()

        # Detect Cloudflare block (if the title is "Just a moment...")
        if "Just a moment..." in page_title or "Verify" in page_title:
            print(f"⚠️ Cloudflare is blocking this request: {url}. Skipping...")
            driver.quit()
            continue

        # Wait for the Description section to load (if available)
        try:
            overview_div = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "wysiwyg.field--name-body"))
            )
            raw_html = overview_div.get_attribute("outerHTML")
        except Exception:
            print(f"⚠️ No 'Description' section found for: {page_title}")
            raw_html = ""

        # === CLEANING PROCESS ===

        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(raw_html, "html.parser")

        # Extract only <p> tags inside the Overview section
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
        cleaned_text = "\n\n".join(paragraphs) if paragraphs else "No relevant content found."

        # Store extracted and cleaned data
        data = {
            "title": page_title,
            "url": url,
            "section": f"Description of {page_title}",
            "content": cleaned_text
        }

        # Append the new data
        all_data.append(data)
        print(f"Successfully scraped and cleaned: {page_title}")

    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")

    finally:
        driver.quit()  # Close the browser after each request

    # Rate limit before moving to the next page
    wait_time = random.randint(10, 20)  # Random delay between 10-20 seconds
    print(f"Waiting {wait_time} seconds before the next request...")
    time.sleep(wait_time)

# Save all scraped data to the file
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=4, ensure_ascii=False)

print(f"\n All data successfully saved in '{output_file}'")