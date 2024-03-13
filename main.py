# main.py file
import asyncio
import pandas as pd
import os
import sys
import whois
from domain_checker import process_urls_async


async def process_dataSet_urls(urlSet, semaphore):
    urls = urlSet['data']  # Assuming 'data' key in dataSet contains the list of URLs
    return await process_urls_async(urls, semaphore)


if __name__ == '__main__':
    try:
        # Your dataSet object containing URLs
        urlSet = {}
        
        semaphore = asyncio.Semaphore(8)  # Adjust the value as needed

        # Run asynchronous tasks
        result_df = asyncio.run(process_dataSet_urls(urlSet, semaphore))

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
