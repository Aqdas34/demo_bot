import json
import requests
import concurrent.futures
from RavaDynamics import load_excluded_domains
import re
from urllib.parse import urlparse
import requests
from RavaDynamics import get_device_id
from activity_data import fetch_app_data
from urllib.parse import urlparse
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import openpyxl




def get_domain_name(url):
    # Parse the URL, adding 'http' if it doesn't already start with it
    parsed_url = urlparse(url if url.startswith('http') else f'http://{url}')
    domain = parsed_url.netloc
    # Remove 'www.' or any subdomain before the first dot
    domain_parts = domain.split('.')
    
    # If there are more than two parts, drop the first part (subdomain)
    if len(domain_parts) > 2:
        domain = '.'.join(domain_parts[1:])
    
    return domain

excluded = None

# print(excluded)
def excludeit(w,excluded_list):
    excluded = excluded_list   
    w = get_domain_name(w)
    if w not in excluded:
        return False
    return True
   

           
def clean_keywords(keywords):
    keywords=str(keywords)
    # Replace non-alphabet characters with '+'
    cleaned_keywords = re.sub(r'[^a-zA-Z0-9]', '+', keywords)
    # Remove consecutive '+' signs
    cleaned_keywords = re.sub(r'\++', '+', cleaned_keywords)
    
    return cleaned_keywords.strip('+')


resultList = []
failRequests=[]




# Define headers with the static API key
headers = {
    'X-API-KEY': '693d32df04b913a4db709358d9f14f81e95fb7c1',
    'Content-Type': 'application/json'
}

# Create a persistent session with retry strategy
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=0.2,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["POST"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)

import time

def google(ur, excluded_domains_list):
    
    # print("called")

    # Initialize variables for response data
    title = ''
    kg = ''
    link1 = ''
    link2 = ''
    link3 = ''
    rating = ''  
    rating_count = ''
    phone = ''
    address = ''

    try:
        # Define the search query payload
        payload = json.dumps({
            "q": ur  # Search query term
        })

        # Send the request using the persistent session
        response = session.post("https://google.serper.dev/search", headers=headers, data=payload)
        data = response.json()

        # Make additional request to places endpoint
        places_payload = json.dumps({
            "q": ur
        })
        places_response = session.post("https://google.serper.dev/places", headers=headers, data=places_payload)
        places_data = places_response.json()

        # Extract places data if available
        if places_data.get("places") and len(places_data["places"]) > 0:
            first_place = places_data["places"][0]
            address = first_place.get("address", "")
            rating = first_place.get("rating", "")
            rating_count = first_place.get("ratingCount", "")
            phone = first_place.get("phoneNumber", "")

        # Check if knowledgeGraph exists
        knowledge_graph = data.get("knowledgeGraph", {})
        if knowledge_graph:
            title = knowledge_graph.get('title', '')
            kg = knowledge_graph.get('type', '')  # Extract knowledge graph type
            link1 = knowledge_graph.get('website', None)

            # Call excludeit function to exclude the link, not the title
            if link1 and not excludeit(link1, excluded_domains_list):
                return [ur, title, kg, link1, link2, link3, address, rating, rating_count, phone]

        # Extract results from the organic section if no knowledgeGraph is present
        results = data.get("organic", [])

        # Get the top three non-wikipedia links
        count = 0
        for result in results:
            link = result.get('link', None)

            # Call excludeit function on the link
            if link and not excludeit(link, excluded_domains_list):
                if count == 0:
                    title = result.get('title', None)
                    link1 = link
                elif count == 1:
                    link2 = link
                elif count == 2:
                    link3 = link

                count += 1

            # Stop after collecting 3 valid links
            if count >= 3:
                break

        return [ur, title, kg, link1, link2, link3, address, rating, rating_count, phone]

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for '{ur}': {e}")

    except Exception as e:
        print(f"An error occurred: {e}")

    # In case of failure or no valid links found
    return [ur, title, kg, link1, link2, link3, address, rating, rating_count, phone]




# def google(ur, excluded_domains_list):
    
#     # print("called")

#     # Initialize variables for response data
#     title = ''
#     kg = ''
#     link1 = ''
#     link2 = ''
#     link3 = ''
#     rating = ''  
#     rating_count = ''
#     phone = ''
#     address = ''

#     try:
#         # Define the search query payload
#         payload = json.dumps({
#             "q": ur  # Search query term
#         })

#         # Send the request using the persistent session
#         response = session.post("https://google.serper.dev/search", headers=headers, data=payload)
#         # response.raise_for_status()  # Raise an error for bad responses
#         data = response.json()



#         # Check if knowledgeGraph exists
#         knowledge_graph = data.get("knowledgeGraph", {})
#         if knowledge_graph:
#             title = knowledge_graph.get('title', '')
#             kg = knowledge_graph.get('type', '')  # Extract knowledge graph type
#             link1 = knowledge_graph.get('website', None)
#             rating_count = knowledge_graph.get('ratingCount', None)
#             rating = knowledge_graph.get('rating', None)  # Extract rating
#             address = knowledge_graph.get('attributes', {}).get('Address', None)

#             # Fetch and split the phone numbers, keeping only the first one
#             phone_list = knowledge_graph.get('attributes', {}).get('Phone', None)
#             if phone_list:
#                 phone = phone_list.split('⋅')[0].strip()  # Take the first phone number

#             # Call excludeit function to exclude the link, not the title
#             if link1 and not excludeit(link1, excluded_domains_list):
#                 return [ur, title,kg, link1, link2, link3, address, rating, rating_count, phone]

#         # Extract results from the organic section if no knowledgeGraph is present
#         results = data.get("organic", [])

#         # Get the top three non-wikipedia links
#         count = 0
#         for result in results:
#             link = result.get('link', None)

#             # Call excludeit function on the link
#             if link and not excludeit(link, excluded_domains_list):
#                 if count == 0:
#                     title = result.get('title', None)
#                     link1 = link
#                 elif count == 1:
#                     link2 = link
#                 elif count == 2:
#                     link3 = link

#                 count += 1

#             # Stop after collecting 3 valid links
#             if count >= 3:
#                 break

#         # print("Done")
#         return [ur, title,kg, link1, link2, link3, address, rating, rating_count, phone]

#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching data for '{ur}': {e}")

#     except Exception as e:
#         print(f"An error occurred: {e}")

#     # In case of failure or no valid links found
#     return [ur, title,kg, link1, link2, link3, address, rating, rating_count, phone]


def main(urls, excluded_domains_list):  
    # print("main")
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        # Use a lambda to pass excluded_domains_list to google
        executor.map(lambda url: google(url, excluded_domains_list), urls)


def set_excluded_domains(domains):
    excluded = load_excluded_domains()
    for dm in domains:
        if not dm in excluded:
           excluded.append(dm)


