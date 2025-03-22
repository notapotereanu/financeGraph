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