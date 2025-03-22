import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

def get_finviz_ratings(stock_symbol="AAPL"):
    # URL for the Finviz page of the stock
    url = f"https://finviz.com/quote.ashx?t={stock_symbol}&p=d"

    # Define headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Send GET request to the URL with headers
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to retrieve the page. Status Code: {response.status_code}")
        return None

    # Parse the HTML content of the page
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the table containing the ratings data by class name
    ratings_table = soup.find('table', {'class': 'js-table-ratings styled-table-new is-rounded is-small'})

    # Check if the table was found
    if ratings_table:
        # Find all rows in the table (skip the header row)
        rows = ratings_table.find_all('tr')[1:]  # [1:] to skip the header row
        
        # Get the current date and calculate the date 1 month ago
        today = datetime.utcnow()
        one_month_ago = today - timedelta(days=32)

        # List to store the data
        data = []

        # Iterate through each row and extract relevant columns
        for row in rows:
            columns = row.find_all('td')
            if len(columns) == 5:  # Ensure row has 5 columns
                date = columns[0].text.strip()
                action = columns[1].text.strip()
                analyst = columns[2].text.strip()
                rating_change = columns[3].text.strip()
                price_target_change = columns[4].text.strip()

                # Convert the date to datetime format (adjusted for "Jul-29-24" format)
                try:
                    row_date = datetime.strptime(date, "%b-%d-%y")
                except ValueError:
                    continue  # If date format doesn't match, skip this row

                # Only add rows where the date is within the last month
                if row_date >= one_month_ago:
                    data.append([date, action, analyst, rating_change, price_target_change])

        # Convert the data into a pandas DataFrame for easier manipulation
        df = pd.DataFrame(data, columns=["Date", "Action", "Analyst", "Rating Change", "Price Target Change"])

        # Return the DataFrame
        return df

    else:
        print("Ratings table not found.")
        return None
