import asyncio
import os
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import re
import json
import time
from groq import Groq

class MarketplaceScraper:
    def __init__(self, items):
        self.items = items
        self.ai_client = Groq(api_key="")  # Initialize the Groq client
        
    async def scrape_marketplace_item(self, crawler, item_id, item_title):
        url = f"https://www.facebook.com/marketplace/item/{item_id}/"
        print(f"Scraping: {item_title} - {url}")
        
        # Set up run config
        run_config = CrawlerRunConfig()
        
        try:
            # Navigate and get content
            result = await crawler.arun(
                url=url,
                config=run_config
            )
            
            # Create output directory if it doesn't exist
            os.makedirs("output", exist_ok=True)
            
            # Save markdown and HTML for debugging
            with open(f"output/{item_id}_data.md", "w", encoding="utf-8") as file:
                file.write(result.markdown)
            
            with open(f"output/{item_id}_data.html", "w", encoding="utf-8") as file:
                file.write(result.html)
            
            # Extract redacted description if available
            pattern = r'("redacted_description"\s*:\s*\{\s*"text"\s*:\s*".*?"\s*\})'
            match = re.search(pattern, result.html)
            
            if match:
                extracted_string = match.group(1)
                text_pattern = r'"text"\s*:\s*"(.*?)"\s*\}'
                text_match = re.search(text_pattern, extracted_string, re.DOTALL)
                
                if text_match:
                    escaped_text = text_match.group(1)
                    
                    # Extract phone numbers using AI
                    phone_numbers = await self.extract_phone_numbers(escaped_text)
                    
                    output_data = {
                        "id": item_id,
                        "title": item_title,
                        "redacted_description": {
                            "text": escaped_text
                        },
                        "phone_numbers": phone_numbers
                    }
                    
                    # Save to JSON file
                    with open(f"output/{item_id}_description.json", 'w', encoding='utf-8') as outfile:
                        json.dump(output_data, outfile, indent=4, ensure_ascii=True)
                    
                    print(f"Successfully processed item: {item_title}")
                    return True, phone_numbers
                else:
                    print(f"Could not extract text content for item: {item_title}")
            else:
                print(f"Pattern not found for item: {item_title}")
            
        except Exception as e:
            print(f"Error scraping {item_title}: {e}")
        
        return False, []
    
    async def extract_phone_numbers(self, phone_text):
        try:
            response = self.ai_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """
                        You are a data specialist focusing on scraping the web.
                        - Extract all Tunisian mobile phone numbers from the provided HTML.
                        - Tunisian mobile numbers are 8 digits long, starting with 2, 4, 5, or 9, and may be prefixed with +216 or 00216 (optionally followed by a space).
                        - Output ONLY the numbers in a JSON format with a single key 'sms_numbers'.
                        """
                    },
                    {
                        "role": "user",
                        "content": f"The HTML that contain the phone numbers : \"{phone_text}\"."
                    }
                ],
                model="llama3-70b-8192",
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=39,
                top_p=0.9,
            )
            
            print(response.choices[0].message.content)
            
            sms_numbers = json.loads(response.choices[0].message.content)['sms_numbers']
            return sms_numbers
        except Exception as e:
            print(f"Error extracting phone numbers: {e}")
            return []
    
    async def run(self):
        # Set up browser config
        browser_config = BrowserConfig()
        
        # Track successful and failed items
        successful = []
        failed = []
        phone_number_results = {}
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for item in self.items:
                item_id = item["id"]
                item_title = item["marketplace_listing_title"]
                
                success, phone_numbers = await self.scrape_marketplace_item(crawler, item_id, item_title)
                
                if success:
                    successful.append(item)
                    phone_number_results[item_id] = phone_numbers
                else:
                    failed.append(item)
                
                # Add a small delay between requests to avoid rate limiting
                await asyncio.sleep(2)
            
            # Save summary report
            summary = {
                "total_items": len(self.items),
                "successful": len(successful),
                "failed": len(failed),
                "failed_items": failed,
                "phone_numbers": phone_number_results
            }
            
            with open("output/scraping_summary.json", 'w', encoding='utf-8') as outfile:
                json.dump(summary, outfile, indent=4, ensure_ascii=True)
            
            print(f"\nScraping completed. Successful: {len(successful)}, Failed: {len(failed)}")

async def main():
    # Load the list of marketplace items
    with open("real_estate_listings_2.json", "r", encoding="utf-8") as file:
        items = json.load(file)
    
    scraper = MarketplaceScraper(items)
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())