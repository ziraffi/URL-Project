# domain_checker file
import asyncio
import datetime
import logging
from flask import jsonify
import whois
import aiohttp
from tqdm import tqdm
import time
from typing import List, AsyncGenerator, Dict, Any


# Logging setup with enhanced logging of successful and failed requests
logging.basicConfig(level=logging.INFO, filename='domain_info_checker.log')

async def fetch_url_status(url, session, semaphore, retry_attempts=2):
    # Ensure URL has a protocol (http:// or https://)
    if not url.startswith("http://") and not url.startswith("https://"):
        # Assuming HTTP as default protocol
        url = "http://" + url

    # Log the received dataSet
    logging.info(f"Received dataSet: {url}")  # Review the current dataSet which is going to be processed
    
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
            expiration_date = max(expiration_dates, default=None) #.strftime('%d-%m-%Y %I:%M:%S')  # Format expiration date
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
            'Domain Status': f'{e}',
            'Expiration Date': None,
            'For Sale': None,
            'Response Time': None,            
        }
        
# Variable to store progress information
progress_info = {
    'processed_urls': 0,
    'total_urls': 0,
    'status': 'Processing',
    'iteration_times': [],  # Store processing times of completed iterations
    'progress_percentage': 0  # Initialize progress percentage
}      

# Update progress information after each iteration
def update_progress(total_iterations, completed_iterations):
    if total_iterations > 0:
        progress_info['total_urls'] = total_iterations
        progress_info['processed_urls'] = completed_iterations
        progress_info['progress_percentage'] = (completed_iterations / total_iterations) * 100
    else:
        logging.error("Total iterations cannot be zero.")

# Function to simulate processing URLs
async def process_urls_async(urls: List[str], semaphore) -> AsyncGenerator[Dict[str, Any], None]:
    try:
        domain_info_list = []
        start_time = time.time()

        async with aiohttp.ClientSession() as session:
            for idx, url in enumerate(tqdm(urls, desc="Processing URLs"), 1):
                domain_info = await get_domain_info_async(url, session, semaphore)

                if domain_info is not None:
                    domain_info_list.append(domain_info)

                # Calculate time taken for this iteration
                iteration_time = time.time() - start_time

                # Update progress after each iteration
                update_progress(len(urls), idx)

                # Check if all URLs have been processed
                if idx == len(urls):
                    break

                # Calculate mean time per iteration (avoid division by zero)
                mean_time_per_iteration = iteration_time / max(idx, 1)

                # Calculate estimated remaining time
                remaining_iterations = len(urls) - idx
                estimated_remaining_time = remaining_iterations * mean_time_per_iteration

                yield {
                    'mean_time_per_iteration': mean_time_per_iteration,
                    'current_iteration': idx,
                    'estimated_remaining_time': estimated_remaining_time,
                    'domain_info': domain_info
                }

    except Exception as e:
        logging.error(f"Error processing URLs: {e}")
        yield {'error': str(e)}





