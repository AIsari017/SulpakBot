# scrape_sulpak.py
import requests
from bs4 import BeautifulSoup
import json
import logging

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_sulpak_air_conditioners():
    search_url = "https://www.sulpak.kz/f/kondicioneriy"
    response = requests.get(search_url)
    
    if response.status_code != 200:
        logger.error(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    
    products = []
    product_containers = soup.select('.product__item')  # Updated selector
    
    if not product_containers:
        logger.warning("No product containers found. The CSS selector might be incorrect.")
    
    for item in product_containers:
        try:
            title_element = item['data-name']  # Updated selector to get attribute value
            link_element = item.select_one('.product__item-images-block a')  # Updated selector
            price_element = item['data-price']  # Updated selector to get attribute value
            
            if not title_element or not price_element or not link_element:
                logger.warning("Missing title, link, or price element in a product container.")
                continue

            title = title_element
            link = link_element['href']
            price = price_element
            
            products.append({
                "title": title,
                "price": price,
                "link": f"https://www.sulpak.kz{link}"
            })
        except Exception as e:
            logger.error(f"Error processing a product container: {e}")
    
    # Save scraped data to a JSON file
    with open('air_conditioners.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)
    
    return products

if __name__ == "__main__":
    air_conditioners = scrape_sulpak_air_conditioners()
    print(f"Scraped {len(air_conditioners)} air conditioners from Sulpak.kz")