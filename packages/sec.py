import time
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET


# Use a proper User-Agent (with contact information) as required by the SEC
HEADERS = {
    "User-Agent": "MyScraper/1.0 (https://www.mywebsite.com/contact; contact@mywebsite.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive"
}

# A mapping of transaction codes to full descriptions.
TRANSACTION_CODE_MAPPING = {
    "P": "Purchase",
    "S": "Sale",
    "F": "Gift",
    "M": "Exercise"
}


class InsiderTransaction:
    def __init__(self, detail_url, insider_name, relationship, transactions, xml_link):
        self.detail_url = detail_url
        self.insider_name = insider_name
        self.relationship = relationship
        self.transactions = transactions  # List of transaction dictionaries
        self.xml_link = xml_link

    def __str__(self):
        # Create a formatted string for transactions.
        txn_str = "\n".join(
            [
                f"  Date: {txn.get('date')}, Type: {txn.get('transaction_type')}, "
                f"Cost: {txn.get('cost')}, Shares: {txn.get('shares')}, "
                f"Value: {txn.get('value')}, Shares Total: {txn.get('shares_total')}"
                for txn in self.transactions
            ]
        )
        return (
            f"Detail URL: {self.detail_url}\n"
            f"Insider Name: {self.insider_name}\n"
            f"Relationship: {self.relationship}\n"
            f"Transactions:\n{txn_str}\n"
            f"XML Link: {self.xml_link}"
        )


def parse_form4_xml(xml_content, detail_url, xml_link):
    """
    Parse the Form 4 XML content and extract insider trading details.
    
    Returns a dictionary with:
      - detail_url
      - insider_name
      - relationship
      - transactions: a list of dictionaries for each transaction
      - xml_link
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"Error parsing XML from {xml_link}: {e}")
        return None

    # --- Extract Insider Name ---
    insider_name = ""
    name_elem = root.find(".//reportingOwner/reportingOwnerId/rptOwnerName")
    if name_elem is not None and name_elem.text:
        insider_name = name_elem.text.strip()

    # --- Extract Relationship ---
    relationship = ""
    rel_elem = root.find(".//reportingOwner/reportingOwnerRelationship")
    if rel_elem is not None:
        parts = []
        if rel_elem.findtext("isDirector") == "1":
            parts.append("Director")
        if rel_elem.findtext("isOfficer") == "1":
            officer_title = rel_elem.findtext("officerTitle") or ""
            parts.append(f"Officer ({officer_title.strip()})" if officer_title.strip() else "Officer")
        if rel_elem.findtext("isTenPercentOwner") == "1":
            parts.append("10% Owner")
        if rel_elem.findtext("isOther") == "1":
            parts.append("Other")
        relationship = ", ".join(parts)

    # --- Extract Transaction Details ---
    transactions = []
    for txn in root.findall(".//nonDerivativeTable/nonDerivativeTransaction"):
        txn_date = txn.findtext(".//transactionDate/value")
        raw_txn_code = txn.findtext(".//transactionCoding/transactionCode")
        txn_type = TRANSACTION_CODE_MAPPING.get(raw_txn_code, raw_txn_code)
        cost = txn.findtext(".//transactionAmounts/transactionPricePerShare/value")
        shares = txn.findtext(".//transactionAmounts/transactionShares/value")
        try:
            computed_value = float(cost) * float(shares)
            computed_value = round(computed_value, 2)
        except Exception:
            computed_value = ""
        shares_total = txn.findtext(".//postTransactionAmounts/sharesOwnedFollowingTransaction/value")
        transactions.append({
            "date": txn_date,
            "transaction_type": txn_type,
            "cost": cost,
            "shares": shares,
            "value": str(computed_value),
            "shares_total": shares_total
        })

    return {
        "detail_url": detail_url,
        "insider_name": insider_name,
        "relationship": relationship,
        "transactions": transactions,
        "xml_link": xml_link
    }


def scrape_filing_detail(detail_url):
    """
    Scrape an individual Form 4 filing detail page to extract the insider information,
    transaction details, and the XML link. Then fetch and parse the XML content.
    """
    try:
        response = requests.get(detail_url, headers=HEADERS)
        response.raise_for_status()
    except Exception as e:
        print(f"Errore scraping detail page {detail_url}: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    # --- Find the XML link ---
    xml_link = ""
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.lower().endswith('.xml'):
            possible_xml_url = "https://www.sec.gov" + href
            try:
                head_response = requests.head(possible_xml_url, headers=HEADERS)
                content_type = head_response.headers.get('Content-Type', '')
                if 'xml' in content_type.lower():
                    xml_link = possible_xml_url
                    break
            except Exception as e:
                print(f"Error checking URL {possible_xml_url}: {e}")

    if not xml_link:
        print(f"No XML link found for {detail_url}")
        return None

    # --- Fetch the XML content ---
    try:
        xml_response = requests.get(xml_link, headers=HEADERS)
        xml_response.raise_for_status()
        xml_content = xml_response.content
    except Exception as e:
        print(f"Error fetching XML content from {xml_link}: {e}")
        return None

    # --- Parse the XML and extract desired data ---
    filing_data = parse_form4_xml(xml_content, detail_url, xml_link)
    return filing_data


def scrape_sec_filings(url):
    """Scrape the SEC Form 4 filings list page and process each filing's detail page."""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except Exception as e:
        print(f"Errore scraping list page: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    filings = []

    # The filings are usually listed in a table.
    # Look for rows that include a link to the filing detail page.
    for row in soup.find_all('tr'):
        link_tag = row.find('a', href=True)
        if link_tag and 'Archives' in link_tag['href']:
            detail_url = "https://www.sec.gov" + link_tag['href']
            print(f"🔹 Processing filing detail page: {detail_url}")
            filing_data = scrape_filing_detail(detail_url)
            if filing_data:
                filings.append(filing_data)
            # Pause to respect SEC rate limiting guidelines.
            time.sleep(0.5)

    return filings

def get_sec_fillings(SEC_URL):
    filings = scrape_sec_filings(SEC_URL)
    insider_transactions = []

    # Create an InsiderTransaction object for each filing.
    for filing in filings:
        txn_obj = InsiderTransaction(
            detail_url=filing.get("detail_url"),
            insider_name=filing.get("insider_name"),
            relationship=filing.get("relationship"),
            transactions=filing.get("transactions"),
            xml_link=filing.get("xml_link")
        )
        insider_transactions.append(txn_obj)
    return insider_transactions
        
if __name__ == "__main__":
    SEC_CIK = "0000320193"  
    SEC_URL = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={SEC_CIK}&type=4&owner=only&count=10"
    for txn in get_sec_fillings(SEC_URL):
        print("========================================")
        print(txn)
