import json
import urllib.parse
from datetime import datetime, timedelta
from curl_cffi import requests
import time
import pandas as pd 

def build_payload(keywords, timeframe='today 1-m', geo='US'):
    token_payload = {
        'hl': 'en-US',
        'tz': '0',
        'req': {
            'comparisonItem': [{'keyword': keyword, 'time': timeframe, 'geo': geo} for keyword in keywords],
            'category': 0,
            'property': ''
        }
    }
    token_payload['req'] = json.dumps(token_payload['req'])
    return token_payload

def convert_to_desired_format(raw_data):
    trend_data = {}
    for entry in raw_data['default']['timelineData']:
        timestamp = int(entry['time'])
        date_time_str = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        value = entry['value'][0]
        trend_data[date_time_str] = value
    return trend_data

# Cookies
def get_google_cookies(impersonate_version='chrome110'):
    with requests.Session() as session:
        session.get("https://www.google.com", impersonate=impersonate_version)
        return session.cookies

def googleAPI_get_df(keywords, days_ago=365, geo='US', hl='en-US', max_retries=5, 
                     browser_version='chrome110', browser_switch_retries=2):
    browser_versions = ['chrome110', 'edge101', 'chrome107', 'chrome104', 'chrome100', 'chrome101', 'chrome99']
    current_browser_version_index = browser_versions.index(browser_version)
    cookies = get_google_cookies(impersonate_version=browser_versions[current_browser_version_index])

    for browser_retry in range(browser_switch_retries + 1):
        data_fetched = False  # Reset data_fetched at the beginning of each browser_retry
        with requests.Session() as s:
            # Phase 1: Fetch token
            for retry in range(max_retries):
                time.sleep(2)
                token_payload = build_payload(keywords)
                url = 'https://trends.google.com/trends/api/explore'
                params = urllib.parse.urlencode(token_payload)
                full_url = f"{url}?{params}"
                response = s.get(full_url, impersonate=browser_versions[current_browser_version_index], cookies=cookies)
                if response.status_code == 200:
                    content = response.text[4:]
                    try:
                        data = json.loads(content)
                        widgets = data['widgets']
                        tokens = {}
                        request_obj = {}
                        for widget in widgets:
                            if widget['id'] == 'TIMESERIES':
                                tokens['timeseries'] = widget['token']
                                request_obj['timeseries'] = widget['request']
                        break  # Successfully fetched token
                    except json.JSONDecodeError:
                        print(f"Failed to decode JSON while fetching token, retrying {retry + 1}/{max_retries}")
                else:
                    print(f"Error {response.status_code} while fetching token, retrying {retry + 1}/{max_retries}")
            else:
                print(f"Exceeded maximum retry attempts ({max_retries}) while fetching token. Exiting...")
                return None

            # Phase 2: Fetch trends data
            for retry in range(max_retries):
                time.sleep(5)
                req_string = json.dumps(request_obj['timeseries'], separators=(',', ':'))
                encoded_req = urllib.parse.quote(req_string, safe=':,+')
                url = f"https://trends.google.com/trends/api/widgetdata/multiline?hl={hl}&tz=0&req={encoded_req}&token={tokens['timeseries']}&tz=0"
                response = s.get(url, impersonate=browser_versions[current_browser_version_index], cookies=cookies)
                if response.status_code == 200:
                    content = response.text[5:]
                    try:
                        raw_data = json.loads(content)
                        # Convert raw data to a dictionary with date keys and score values
                        trend_data = convert_to_desired_format(raw_data)
                        data_fetched = True
                        # Create a DataFrame from the dictionary.
                        # The dictionary keys become the DataFrame's index (date), and the values become a column 'score'.
                        df = pd.DataFrame.from_dict(trend_data, orient='index', columns=['score'])
                        df.index.name = 'date'
                        # Optionally, convert the index to a datetime object
                        df.index = pd.to_datetime(df.index)
                        return df
                    except json.JSONDecodeError:
                        print(f"Failed to decode JSON while fetching trends data, retrying {retry + 1}/{max_retries}")
                else:
                    print(f"Error {response.status_code} while fetching trends data, retrying {retry + 1}/{max_retries}")
            else:
                print(f"Exceeded maximum retry attempts ({max_retries}) while fetching trends data.")

        # Change browser version if needed
        if not data_fetched and browser_retry < browser_switch_retries:
            time.sleep(5)
            current_browser_version_index = (current_browser_version_index + 1) % len(browser_versions)
            print(f"Switching browser version to {browser_versions[current_browser_version_index]} and retrying...")

    print(f"Exceeded maximum browser switch attempts ({browser_switch_retries}). Exiting...")
    return None
