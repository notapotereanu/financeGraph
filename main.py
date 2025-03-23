"""Main module for financial data analysis and RDF storage."""

import warnings
warnings.filterwarnings('ignore')
from packages.data_analyzer.financial_data_analyzer import FinancialDataAnalyzer

def main():
    try:
        analyzer = FinancialDataAnalyzer()
        analyzer.run_analysis()
    except Exception as e:
        print(f"❌ Application error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
