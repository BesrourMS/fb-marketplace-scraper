import asyncio
import re
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import json
from bs4 import BeautifulSoup

async def main():
    browser_config = BrowserConfig()  # Default browser configuration
    run_config = CrawlerRunConfig()   # Default crawl run configuration
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.facebook.com/marketplace/111663698852329/propertyforsale",
            config=run_config
        )
        html_data = result.html  # Get clean markdown content
        
        pattern = r'"result":{"data":{"viewer":{"marketplace_feed_stories":{"edges":(\[.*?\}\])'

        # Find the match
        match = re.search(pattern, html_data, re.DOTALL)  # re.DOTALL allows . to match newlines

        if match:
            edges_str = match.group(1)  # Extract the captured array as a string
            print("--- Found potential match for 'edges' ---")

            # Define the output filename
            output_filename = "edges_output.json"

            # --- SAVE THE EXTRACTED STRING TO A FILE ---
            try:
                with open(output_filename, "w", encoding="utf-8") as outfile:
                    outfile.write(edges_str)
                print(f"Successfully saved the raw extracted string to '{output_filename}'")
            except IOError as e:
                print(f"Error: Could not write to file '{output_filename}': {e}")
            # -------------------------------------------
            try:
                # Parse the extracted string as JSON
                edges = json.loads(edges_str)
                print(f"Found {len(edges)} nodes:")
                print(edges_str)
                
                # Check if 24 nodes are present
                if len(edges) == 24:
                    print("Successfully extracted 24 nodes!")
                else:
                    print(f"Only {len(edges)} nodes found. Expected 24.")
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
        else:
            print("No match found for the edges array")

if __name__ == "__main__":
    asyncio.run(main())