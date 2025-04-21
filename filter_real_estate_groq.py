import json
from groq import Groq
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os

# Initialize Groq client (replace with your Groq API key)
GROQ_API_KEY = ""  # Set this in your environment
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set.")
client = Groq(api_key=GROQ_API_KEY)

def is_real_estate_groq(title):
    """Use Groq LLM to determine if a listing title is related to real estate."""
    try:
        # Craft a prompt for the LLM
        prompt = (
            "Classify the following marketplace listing title as related to real estate or not. "
            "Real estate includes properties like villas, apartments, houses, or land. "
            "Return only 'True' or 'False'.\n\n"
            f"Title: {title}"
        )
        
        # Call Groq API
        response = client.chat.completions.create(
            model="llama3-8b-8192",  # You can also use "llama-3.1-8b-instant" or others
            messages=[
                {"role": "system", "content": "You are a classifier for marketplace listings."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0.0  # Low temperature for deterministic output
        )
        
        # Extract the response
        result = response.choices[0].message.content.strip()
        return result == "True"
    
    except Exception as e:
        print(f"Error querying Groq API for title '{title}': {str(e)}")
        return False  # Fallback to False if API call fails

def process_listings(json_file_path):
    """Process JSON file to extract real estate listings."""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        real_estate_listings = []
        
        # Check the structure of the JSON file
        if isinstance(json_data, list):
            # If the root element is a list
            items_to_process = json_data
        elif isinstance(json_data, dict):
            # Try different common keys if it's a dictionary
            if 'results' in json_data:
                items_to_process = json_data.get('results', [])
            elif 'listings' in json_data:
                items_to_process = json_data.get('listings', [])
            elif 'items' in json_data:
                items_to_process = json_data.get('items', [])
            else:
                # If no known keys are found, use the entire dictionary as a single item
                items_to_process = [json_data]
        else:
            items_to_process = []
        
        # Process each item in the list
        for item in items_to_process:
            # Try different paths to find listing information
            if 'node' in item and 'listing' in item.get('node', {}):
                listing = item['node']['listing']
            elif 'listing' in item:
                listing = item['listing']
            else:
                listing = item  # Assume the item itself is the listing
            
            # Extract listing ID and title
            listing_id = listing.get('id')
            title = listing.get('marketplace_listing_title')
            
            if not title and 'title' in listing:
                title = listing.get('title')  # Try alternative title field
            
            if listing_id and title and is_real_estate_groq(title):
                real_estate_listings.append({
                    'id': listing_id,
                    'marketplace_listing_title': title
                })
        
        return real_estate_listings
    
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found.")
        return []
    except json.JSONDecodeError:
        print("Error: Invalid JSON format.")
        return []
    except Exception as e:
        print(f"Error processing listings: {str(e)}")
        return []

def main():
    # Set up browser config with longer timeout
    browser_config = BrowserConfig()
    
    # Initial run config
    run_config = CrawlerRunConfig()
    
    # Example JSON file path (replace with actual path)
    json_file_path = 'edges_output.json'
    
    # Process the listings
    real_estate_listings = process_listings(json_file_path)
    
    # Output results
    if real_estate_listings:
        print("Real Estate Listings:")
        for listing in real_estate_listings:
            print(f"ID: {listing['id']}, Title: {listing['marketplace_listing_title']}")
        
        # Save to a JSON file
        with open('real_estate_listings_2.json', 'w', encoding='utf-8') as f:
            json.dump(real_estate_listings, f, ensure_ascii=False, indent=2)
        print("Results saved to real_estate_listings.json")
    else:
        print("No real estate listings found.")
    
if __name__ == "__main__":
    main()