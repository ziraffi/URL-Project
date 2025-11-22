"""
Domain Checker Module

This module provides functionality for checking URL status codes and WHOIS information
for bulk URL processing operations.
"""

import aiohttp
import asyncio
import datetime
import logging
import whois
import time
from typing import List, Dict, Any, AsyncGenerator
from tqdm import tqdm

# Global cancel flag for processing
global_cancel_flag = False

# Progress tracking constants
REMAINING_ITERATIONS = 'remaining_iterations'
PROCESSED_URLS = 'processed_urls'
PROCESSING_STATUS = 'Processing'
PROGRESS_PERCENT = 'tryPercent'
TOTAL_URLS = 'total_urls'
ITERATION_TIMES = 'iteration_times'
PROGRESS_INFO_OBJ = 'pInfo_obj'
DOMAIN_INFO_KEY = 'domain_info'
CANCEL_FLAG = 'cancelFlag'
URL_KEY = 'URL'

# Domain analysis constants
STATUS_CODE = 'Status Code'
RESPONSE_MESSAGE = 'Response Message'
DOMAIN_STATUS = 'Domain Status'
EXPIRATION_DATE = 'Expiration Date'
FOR_SALE = 'For Sale'
RESPONSE_TIME = 'Response Time'

# Status values
FRESH_STATUS = 'Fresh'
EXPIRED_STATUS = 'Expired'
FOR_SALE_STATUS = 'For Sale'
NA_STATUS = 'NA'

# Progress info object
progress_info = {
    PROGRESS_PERCENT: 0,
    PROCESSED_URLS: 0,
    TOTAL_URLS: 0,
    PROCESSING_STATUS: PROCESSING_STATUS,
    ITERATION_TIMES: [],
    PROGRESS_INFO_OBJ: [],
    REMAINING_ITERATIONS: 0
}


async def check_url_status(url: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore,
                          cancel_flag: bool, max_retries: int = 2) -> tuple:
    """
    Check URL status with retry logic for both HTTP and HTTPS protocols.

    Args:
        url: The URL to check
        session: aiohttp session object
        semaphore: asyncio semaphore for concurrency control
        cancel_flag: Flag to cancel the operation
        max_retries: Maximum number of retry attempts

    Returns:
        Tuple of (status_codes, response_messages)
    """
    HTTP_PREFIX = 'http://'
    HTTPS_PREFIX = 'https://'
    target_url = url
    global global_cancel_flag
    global_cancel_flag = cancel_flag

    # Ensure URL has a protocol
    if not target_url.startswith(HTTP_PREFIX) and not target_url.startswith(HTTPS_PREFIX):
        target_url = HTTPS_PREFIX + target_url
        https_first = True
    else:
        https_first = False

    http_success = False
    https_success = False
    logging.info(f"Received dataSet: {target_url}")
    retry_count = 0

    while retry_count < max_retries:
        if global_cancel_flag:
            break

        try:
            async with semaphore, session.get(target_url, timeout=8, allow_redirects=False) as response:
                status_codes = [response.status]
                response_messages = [response.reason]

                # Follow redirects
                while response.history:
                    response = response.history[0]
                    status_codes.append(response.status)
                    response_messages.append(response.reason)
                    if global_cancel_flag:
                        break

                if http_success:
                    print('HTTP prototype was successful.')
                elif https_success:
                    print('HTTPS prototype was successful.')

                return status_codes, response_messages

        except aiohttp.ClientError as client_error:
            logging.error(f"Client error fetching URL status for {target_url}: {client_error}")
            if 'Server disconnected' in str(client_error):
                retry_count += 1
                continue
            elif 'Cannot connect to host' in str(client_error):
                retry_count += 1
                continue
            else:
                retry_count += 1
                continue

        except asyncio.TimeoutError:
            logging.error(f"Timeout error fetching URL status for {target_url}. Retrying...")
            retry_count += 1

        except Exception as general_error:
            logging.error(f"Error fetching URL status for {target_url}: {general_error}")
            retry_count += 1

        # Try HTTP if HTTPS failed on first attempt
        if retry_count == 1 and target_url.startswith(HTTPS_PREFIX):
            target_url = target_url.replace(HTTPS_PREFIX, HTTP_PREFIX)
            http_success = True
            continue

        await asyncio.sleep(2)
        logging.info('Retrying...')

    logging.warning(f"Exceeded maximum retries for URL: {target_url}")
    return [None], ['Exceeded maximum retries']


async def fetch_domain_info(url: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore,
                           cancel_flag: bool) -> Dict[str, Any]:
    """
    Fetch WHOIS information and URL status for a domain.

    Args:
        url: The URL/domain to analyze
        session: aiohttp session object
        semaphore: asyncio semaphore for concurrency control
        cancel_flag: Flag to cancel the operation

    Returns:
        Dictionary containing domain information
    """
    processing_cancel_flag = cancel_flag
    global global_cancel_flag
    global_cancel_flag = processing_cancel_flag

    try:
        print(f"Processing URL: {url}")
        start_time = datetime.datetime.now()
        status_task = asyncio.create_task(check_url_status(url, session, semaphore, processing_cancel_flag))
        whois_data = await asyncio.to_thread(whois.whois, url)
        status_codes, response_messages = await status_task
        end_time = datetime.datetime.now()
        response_time = (end_time - start_time).total_seconds()

        if global_cancel_flag:
            return None

        # Process expiration dates
        expiration_dates = [date for date in whois_data.expiration_date
                          if isinstance(date, datetime.datetime)] if isinstance(whois_data.expiration_date, list) else []

        # Check if domain is for sale based on name servers
        for_sale = 'No'
        for name_server in whois_data.name_servers or []:
            if any(parking_domain in name_server.lower()
                  for parking_domain in ['afternic', 'sedo', 'parking']):
                for_sale = 'Yes'
                break

        # Determine domain status
        if expiration_dates:
            domain_status = EXPIRED_STATUS if any(exp_date < datetime.datetime.now()
                                                 for exp_date in expiration_dates) else (FOR_SALE_STATUS if for_sale == 'Yes' else FRESH_STATUS)
            expiration_date = max(expiration_dates, default=None)
        else:
            expiration_date = whois_data.expiration_date
            domain_status = (EXPIRED_STATUS if (expiration_date and isinstance(expiration_date, datetime.datetime)
                                              and expiration_date < datetime.datetime.now())
                           else (FOR_SALE_STATUS if for_sale == 'Yes'
                               else (FRESH_STATUS if expiration_date else NA_STATUS)))

        print(f"Domain Status: {domain_status}\nExpiration Date: {expiration_date}\nFor Sale: {for_sale}")

        return {
            URL_KEY: url,
            STATUS_CODE: status_codes,
            RESPONSE_MESSAGE: response_messages,
            DOMAIN_STATUS: domain_status,
            EXPIRATION_DATE: expiration_date,
            FOR_SALE: for_sale,
            RESPONSE_TIME: response_time
        }

    except Exception as error:
        logging.error(f"Error fetching WHOIS information for {url}: {error}")
        return {
            URL_KEY: url,
            STATUS_CODE: None,
            RESPONSE_MESSAGE: None,
            DOMAIN_STATUS: str(error),
            EXPIRATION_DATE: None,
            FOR_SALE: None,
            RESPONSE_TIME: None
        }


async def process_urls_async(urls: List[str], semaphore: asyncio.Semaphore,
                           cancel_flag: bool) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Process a list of URLs asynchronously, yielding progress updates and results.

    Args:
        urls: List of URLs to process
        semaphore: asyncio semaphore for concurrency control
        cancel_flag: Flag to cancel the operation

    Yields:
        Dictionary containing processing results and progress information
    """
    processing_cancel_flag = cancel_flag
    url_list = urls
    global global_cancel_flag
    global_cancel_flag = processing_cancel_flag

    try:
        domain_results = []
        progress_info[ITERATION_TIMES] = []
        progress_info[PROGRESS_INFO_OBJ] = []

        async with aiohttp.ClientSession() as session:
            start_time = time.time()

            for index, url in enumerate(tqdm(url_list, desc='Processing URLs'), 1):
                if global_cancel_flag:
                    print('Processing canceled at iteration:', index)
                    logging.info('Process canceled by user.')
                    yield {'message': 'Process canceled by user'}
                    return

                domain_data = await fetch_domain_info(url, session, semaphore, processing_cancel_flag)

                if domain_data is not None:
                    domain_results.append(domain_data)

                elapsed_time = time.time() - start_time
                remaining_urls = len(url_list) - index

                if remaining_urls > 0 or (remaining_urls == 0 and index == len(url_list)) and not global_cancel_flag:
                    progress_percentage = (index / len(url_list)) * 100
                    progress_info[PROGRESS_PERCENT] = progress_percentage
                    progress_info[TOTAL_URLS] = len(url_list)
                    progress_info[PROCESSING_STATUS] = PROCESSING_STATUS
                    progress_info[PROCESSED_URLS] = index
                    progress_info[REMAINING_ITERATIONS] = remaining_urls
                    progress_info[ITERATION_TIMES].append(elapsed_time)
                    progress_info[PROGRESS_INFO_OBJ].append(domain_data)
                    progress_info[PROGRESS_INFO_OBJ][-1][URL_KEY] = url

                yield {'current_iteration': index, DOMAIN_INFO_KEY: domain_data, CANCEL_FLAG: global_cancel_flag}

    except Exception as error:
        if global_cancel_flag:
            logging.info(f"Process stopped by user: {error}")
        else:
            logging.error(f"Error processing URLs: {error}")
        yield {'message': str(error)}

# Initialize progress info
progress_info = {
    PROGRESS_PERCENT: 0,
    PROCESSED_URLS: 0,
    TOTAL_URLS: 0,
    PROCESSING_STATUS: PROCESSING_STATUS,
    ITERATION_TIMES: [],
    PROGRESS_INFO_OBJ: [],
    REMAINING_ITERATIONS: 0
}