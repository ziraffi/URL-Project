import aiohttp
import asyncio
import datetime
import logging
import whois
import time
from typing import List, Dict, Any, AsyncGenerator
from tqdm import tqdm

globalCancel = False

async def fetch_url_status(url, session, semaphore, cancelFlag, max_retries=2):
    global globalCancel  # Add this line to reference the global variable

    globalCancel = cancelFlag  # Assign the value of cancelFlag to globalCancel

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
        statushttpS = True

    statushttp = False
    statushttpS = False
    logging.info(f"Received dataSet: {url}")

    retry_count = 0
    while retry_count < max_retries:
        if globalCancel:  # Check globalCancel before proceeding
            break

        try:
            async with semaphore, session.get(url, timeout=8, allow_redirects=True) as response:
                status_codes = [response.status]
                status_messages = [response.reason]

                while response.history:
                    response = response.history[0]
                    status_codes.append(response.status)
                    status_messages.append(response.reason)

                    if globalCancel:
                        break

                if statushttp:
                    print("HTTP prototype was successful.")
                elif statushttpS:
                    print("HTTPS prototype was successful.")

                return status_codes, status_messages

        except aiohttp.ClientError as ce:
            logging.error(f"Client error fetching URL status for {url}: {ce}")
            if "Server disconnected" in str(ce):
                retry_count += 1
                continue
            elif "Cannot connect to host" in str(ce):
                retry_count += 1
                continue
            else:
                retry_count += 1
                continue

        except asyncio.TimeoutError:
            logging.error(f"Timeout error fetching URL status for {url}. Retrying...")
            retry_count += 1
        except Exception as e:
            logging.error(f"Error fetching URL status for {url}: {e}")
            retry_count += 1

        if retry_count == 1 and url.startswith("https://"):
            url = url.replace("https://", "http://")
            statushttp = True
            continue

        await asyncio.sleep(2)
        logging.info("Retrying...")

    logging.warning(f"Exceeded maximum retries for URL: {url}")
    return [None], ["Exceeded maximum retries"]


async def get_domain_info_async(url, session, semaphore, cancelFlag):
    global globalCancel  # Add this line to reference the global variable

    globalCancel = cancelFlag
        
    try:
        print(f"Processing URL: {url}")
        start_time = datetime.datetime.now()

        url_status_task = asyncio.create_task(fetch_url_status(url, session, semaphore, cancelFlag))

        whois_info = await asyncio.to_thread(whois.whois, url)

        url_status, status_message = await url_status_task

        end_time = datetime.datetime.now()
        response_time = (end_time - start_time).total_seconds()
        if globalCancel:
            return
        expiration_dates = (
            [date for date in whois_info.expiration_date if isinstance(date, datetime.datetime)]
            if isinstance(whois_info.expiration_date, list)
            else []
        )

        for name_server in whois_info.name_servers or []:
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
            'Domain Status': f'{e}',
            'Expiration Date': None,
            'For Sale': None,
            'Response Time': None,
        }

async def process_urls_async(urls: List[str], semaphore, cancelFlag) -> AsyncGenerator[Dict[str, Any], None]:
    global globalCancel  # Add this line to reference the global variable
    globalCancel = cancelFlag
    try:
        domain_info_list = []
        progress_info['iteration_times'] = []
        progress_info['pInfo_obj'] = []

        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            for idx, url in enumerate(tqdm(urls, desc="Processing URLs"), 1):
                if globalCancel:
                    print("Processing canceled at iteration:", idx)
                    logging.info("Process canceled by user.")
                    yield {'error': "Process canceled by user"}
                    return  # Stop processing further URLs

                domain_info = await get_domain_info_async(url, session, semaphore, cancelFlag)

                if domain_info is not None:
                    domain_info_list.append(domain_info)

                iteration_time = time.time() - start_time
                remaining_iterations = len(urls) - idx
                if ((remaining_iterations > 0) or (remaining_iterations == 0 and idx == len(urls)) and not globalCancel):
                    try_percentage = (idx / len(urls)) * 100

                    progress_info['tryPercent'] = try_percentage
                    progress_info['total_urls'] = len(urls)
                    progress_info['status'] = "Processing"
                    progress_info['processed_urls'] = idx
                    progress_info['remaining_iterations'] = remaining_iterations
                    progress_info['iteration_times'].append(iteration_time)
                    progress_info['pInfo_obj'].append(domain_info)
                    progress_info['pInfo_obj'][-1]['URL'] = url

                yield {
                    'current_iteration': idx,
                    'domain_info': domain_info,
                    'cancelFlag': globalCancel,
                }

    except Exception as e:
        if globalCancel:
            logging.info(f'Process stopped by user: {e}')
        else:
            logging.error(f"Error processing URLs: {e}")
        yield {'error': str(e)}

# Variable to store progress information
progress_info = {
    'tryPercent' : 0,
    'processed_urls': 0,
    'total_urls': 0,
    'status': 'Processing',
    'iteration_times': [],  
    'pInfo_obj': [],
    'remaining_iterations': 0
}
