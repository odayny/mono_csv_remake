import csv
import sys
import requests
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Read API key from a separate file
with open('api_key.txt', 'r') as api_key_file:
    API_KEY = api_key_file.read().strip()
    
# Cache for storing exchange rates by date
exchange_rate_cache = {}

def convert_date_format(date_str):
    # Assuming the input date format is 'DD.MM.YYYY HH:MM:SS'
    # Convert it to 'YYYY-MM-DD' for the API
    try:
        date_obj = datetime.strptime(date_str, '%d.%m.%Y %H:%M:%S')
        formatted_date = date_obj.strftime('%Y-%m-%d')
        return formatted_date
    except ValueError:
        return None

def get_currency_rate(date):
    # Check if the rate for the given date is already in the cache
    formatted_date = convert_date_format(date)
    
    if formatted_date in exchange_rate_cache:
        logger.info(f"Using cached exchange rate for {formatted_date}")
        return exchange_rate_cache[formatted_date]

    if formatted_date is None:
        logger.error(f"Error formatting date: {date}")
        return None

    url = f'http://api.exchangeratesapi.io/v1/{formatted_date}?access_key={API_KEY}&symbols=UAH&format=1'

    try:
        response = requests.get(url)
        data = response.json()
        uah_to_eur_rate = 1 / data['rates']['UAH']
        logger.info(f"Retrieved UAH to EUR exchange rate for {formatted_date}: {uah_to_eur_rate}")

        # Cache the exchange rate for this date
        exchange_rate_cache[formatted_date] = uah_to_eur_rate

        return uah_to_eur_rate
    except (requests.RequestException, KeyError) as e:
        logger.error(f"Error fetching currency rate for {formatted_date}: {e}")
        return None

def insert_and_calculate(input_file, output_file):
    output_rows = []

    with open(input_file, 'r', newline='') as input_csv:
        reader = csv.reader(input_csv)
        header = next(reader)  # Read and preserve the header

        # Add "EUR" to the header at index 5
        header.insert(5, "EUR")

        for row in reader:
            # Assuming the date and time is in the first column (0-based index)
            date_and_time = row[0]

            # Calculate the currency rate for the date
            currency_rate = get_currency_rate(date_and_time)

            if currency_rate is None:
                return

            # Assuming D is the 4th column (0-based index)
            d_value = float(row[3])  # Convert D value to float

            # Calculate the new value based on the currency rate
            new_value = d_value * currency_rate

            # Insert the new column value before column E (index 5)
            row.insert(5, new_value)

            output_rows.append(row)

    with open(output_file, 'w', newline='') as output_csv:
        writer = csv.writer(output_csv)
        writer.writerow(header)  # Write the preserved header
        writer.writerows(output_rows)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py input_file")
        sys.exit(1)

    input_file = sys.argv[1]
    output_directory = os.path.dirname(input_file)
    output_file = os.path.join(output_directory, "modified_" + os.path.basename(input_file))

    insert_and_calculate(input_file, output_file)
