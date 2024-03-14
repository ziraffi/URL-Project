# domain_checker file
import asyncio
import datetime
import logging
import pandas as pd
import whois
import aiohttp
from tqdm import tqdm
from typing import List


# Logging setup with enhanced logging of successful and failed requests
logging.basicConfig(level=logging.INFO, filename='domain_info_checker.log')
# if(#check)
async def fetch_url_status(url, session, semaphore, retry_attempts=2):
    # Log the received dataSet
    logging.info(f"Received dataSet: {url}") #Review the current dataSet which is going to be processed
    
    for _ in range(retry_attempts):
        try:
            async with semaphore, session.get(url, timeout=8) as response:
                status_code = response.status
                status_message = response.reason
                return status_code, status_message
        except aiohttp.ClientError as ce:
            logging.error(f"Client error fetching URL status for {url}: {ce}")        
        except asyncio.TimeoutError:
            logging.error(f"Timeout error fetching URL status for {url}")
            return None, None
        except Exception as e:
            logging.error(f"Error fetching URL status for {url}: {e}")
        await asyncio.sleep(2)            
    return None, None

async def get_domain_info_async(url, session, semaphore):
    try:
        print(f"Processing URL: {url}")  # Print the URL before processing
        start_time = datetime.datetime.now()

        # Fetch URL status concurrently
        url_status_task = asyncio.create_task(fetch_url_status(url, session, semaphore))

        # Fetch WHOIS information
        whois_info = await asyncio.to_thread(whois.whois, url)

        # Wait for both tasks to complete
        url_status, status_message = await url_status_task

        end_time = datetime.datetime.now()
        response_time = (end_time - start_time).total_seconds()

        expiration_dates = (
            [date for date in whois_info.expiration_date if isinstance(date, datetime.datetime)]
            if isinstance(whois_info.expiration_date, list)
            else []
        )

        # Check for specific name servers associated with domain parking or sales platforms
        for name_server in whois_info.name_servers:
            if any(keyword in name_server.lower() for keyword in ['afternic', 'sedo', 'parking']):
                for_sale_indicator = 'Yes'
                break
        else:
            for_sale_indicator = 'No'

        if expiration_dates:
            # Handle the case where expiration_dates is a non-empty list
            domain_status = 'Expired' if any(date < datetime.datetime.now() for date in expiration_dates) else 'For Sale' if for_sale_indicator == 'Yes' else 'Fresh'
            expiration_date = max(expiration_dates, default=None)
        else:
            # Handle other cases, including when expiration_dates is an empty list or not a list
            expiration_date = whois_info.expiration_date
            domain_status = 'Expired' if expiration_date and (isinstance(expiration_date, datetime.datetime) and expiration_date < datetime.datetime.now()) else 'For Sale' if for_sale_indicator == 'Yes' else 'Fresh' if expiration_date else 'NA'

        print(f'Domain Status: {domain_status}\nExpiration Date: {expiration_date}\nFor Sale: {for_sale_indicator}')
        return {
            'URL': url,
            'Status Code': url_status,
            'Response Message': status_message,            
            'Domain Status': domain_status,
            'Expiration Date': expiration_date,
            'For Sale': for_sale_indicator,
            'Response Time': response_time,            
        }
    except Exception as e:
        logging.error(f"Error fetching WHOIS information for {url}: {e}")
        return {
            'URL': url,
            'Status Code': None,
            'Response Message': None,            
            'Domain Status': f'WHOIS Error: {e}',
            'Expiration Date': None,
            'For Sale': None,
            'Response Time': None,            
        }

async def process_urls_async(urls: List[str], semaphore) -> pd.DataFrame:
    try:
        domain_info_list = []

        async with aiohttp.ClientSession() as session:
            for url in tqdm(urls, desc="Processing URLs"):
                domain_info = await get_domain_info_async(url, session, semaphore)
                if domain_info is not None:                
                    domain_info_list.append(domain_info)

        df = pd.DataFrame(domain_info_list)
        return df
    except Exception as e:
        logging.error(f"Error in process_urls_async: {e}")
        return pd.DataFrame()
