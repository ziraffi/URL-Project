# domain_checker file
import asyncio
import datetime
import logging
import whois
import aiohttp
from typing import List
from tqdm import tqdm
import pandas as pd
import os
import sys

# Logging setup with enhanced logging of successful and failed requests
logging.basicConfig(level=logging.INFO, filename='domain_info_checker.log')

async def fetch_url_status(url, session, semaphore, retry_attempts=2):
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
        except Exception as e:
            logging.error(f"Error fetching URL status for {url}: {e}")
        await asyncio.sleep(2)  # Wait for 2 seconds before retrying
    return None, None

async def get_domain_info_async(url, session, semaphore):
    try:
        print(f"Processing URL: {url}")  # Print the URL before processing
        start_time = datetime.datetime.now()

        url_status_task = asyncio.create_task(fetch_url_status(url, session, semaphore))
        whois_info = await asyncio.to_thread(whois.whois, url)
        url_status,status_message = await url_status_task
        end_time = datetime.datetime.now()
        response_time = (end_time - start_time).total_seconds()

        expiration_dates = (
            [date for date in whois_info.expiration_date if isinstance(date, datetime.datetime)]
            if isinstance(whois_info.expiration_date, list)
            else []
        )

        for name_server in whois_info.name_servers:
            if any(keyword in name_server.lower() for keyword in ['afternic', 'sedo', 'parking']):
                for_sale_indicator = 'Yes'
                break
        else:
            for_sale_indicator = 'No'

        if expiration_dates:
            domain_status = 'Expired' if any(date < datetime.datetime.now() for date in expiration_dates) else 'For Sale' if for_sale_indicator == 'Yes' else 'Fresh'
            expiration_date = max(expiration_dates, default=None)
        else:
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
            'Domain Status': 'Error',
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

if __name__ == '__main__':
    try:
        # Load URLs from CSV
        df = pd.read_csv(r'/workspaces/URL-Project/squarehotel.csv')
        urls = df['hotels_websitelist_losangels-href'].astype(str).tolist()

        # Set the semaphore value
        semaphore = asyncio.Semaphore(8)  # Adjust the value as needed

        # Run asynchronous tasks
        result_df = asyncio.run(process_urls_async(urls, semaphore))

        if result_df.empty:
            print("No data retrieved. Check for errors in asynchronous tasks.")
            sys.exit(0)

        # Save results to a new CSV file without overwriting
        output_file_path = 'domain_info.csv'
        count = 1
        while os.path.exists(output_file_path):
            output_file_path = f'domain_info_{count}.csv'
            count += 1
        result_df.to_csv(output_file_path, index=False)

        print(f"Domain information saved to: {output_file_path}")
        print("Column names:", result_df.columns)

        # Continue with any further analysis or visualization as needed...

    except Exception as e:
        print(f"An unexpected error occurred during task execution: {e}")
        sys.exit(1)  # Exit with an error code