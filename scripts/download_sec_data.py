"""
Download real SEC 10-K filings for S&P 500 companies.

Uses sec-edgar-downloader to fetch the latest 10-K annual report
for each S&P 500 ticker. Data is saved to data/sec_filings/.
"""

import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from sec_edgar_downloader import Downloader

# Where to save filings
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sec_filings")

# SEC requires a User-Agent with company name and email
USER_AGENT = "FinancialRAGResearch contact@example.com"


def fetch_sp500_tickers():
    """
    Fetch the current list of S&P 500 ticker symbols from Wikipedia.

    Returns a list of ticker strings (e.g., ['AAPL', 'MSFT', ...]).
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    print(f"Fetching S&P 500 ticker list from Wikipedia...")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"ERROR: Could not fetch S&P 500 list: {e}")
        print("Falling back to built-in ticker list.")
        return _fallback_tickers()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"id": "constituents"})
    if not table:
        print("WARNING: Could not find constituents table. Using fallback list.")
        return _fallback_tickers()

    tickers = []
    rows = table.find_all("tr")[1:]  # skip header row
    for row in rows:
        cells = row.find_all("td")
        if cells:
            ticker = cells[0].text.strip().replace("\n", "")
            # Clean up: remove any extra whitespace or newlines
            ticker = "".join(ticker.split())
            if ticker and ticker not in tickers:
                tickers.append(ticker)

    print(f"  Found {len(tickers)} tickers from Wikipedia")
    return tickers


def _fallback_tickers():
    """Fallback list of major S&P 500 tickers (if Wikipedia fetch fails)."""
    return [
        "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "GOOG",
        "BRK.B", "JPM", "V", "JNJ", "WMT", "MA", "PG", "UNH", "XOM",
        "HD", "CVX", "BAC", "ABBV", "PFE", "MRK", "KO", "PEP", "TMO",
        "COST", "AVGO", "CSCO", "MCD", "WFC", "ACN", "ABT", "DHR",
        "LIN", "NKE", "NEE", "PM", "DIS", "AMD", "INTU", "TXN", "CAT",
        "AMGN", "IBM", "QCOM", "LOW", "UPS", "ORCL", "HON", "BA",
        "GE", "SPGI", "MS", "UNP", "GS", "RTX", "ISRG", "CMCSA",
        "BLK", "PLD", "T", "AXP", "BKNG", "DE", "ELV", "MDT",
        "SCHW", "ADP", "GILD", "CI", "C", "UBER", "SBUX", "LMT",
        "MMC", "ADI", "CB", "BMY", "MU", "TMUS", "ZTS", "AMT",
        "SO", "REGN", "LRCX", "MO", "DUK", "MDLZ", "CVS", "SYK",
        "VRTX", "FI", "ITW", "BSX", "BDX", "NOC", "FIS", "PNC",
        "EOG", "ETN", "EQIX", "ICE", "WM", "HCA", "SLB", "PSX",
    ]


def download_filings(tickers, limit=1, after="2020-01-01"):
    """
    Download the latest 10-K filing for each ticker.

    Args:
        tickers: List of ticker symbols.
        limit: Max number of filings to download per ticker (default 1 = latest).
        after: Only download filings after this date (YYYY-MM-DD).
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    # Initialize downloader with SEC-compliant User-Agent and output folder
    dl = Downloader("FinancialRAGResearch", "research@example.com", download_folder=DATA_DIR)

    # If we already have a specific output directory, use it
    # Note: sec-edgar-downloader saves to ./sec-edgar-filings/ by default
    total = len(tickers)
    success = 0
    failed = 0
    skipped = 0
    start_time = time.time()

    print(f"\nDownloading 10-K filings for {total} companies...")
    print(f"Output directory: {DATA_DIR}")
    print(f"Limit: {limit} filing(s) per company, After: {after}\n")

    for i, ticker in enumerate(tickers):
        pct = (i + 1) / total * 100
        elapsed = time.time() - start_time
        eta = (elapsed / (i + 1)) * (total - i - 1) if i > 0 else 0

        print(f"[{i+1}/{total}] {ticker} ({pct:.0f}%) | ETA: {eta:.0f}s", end=" ")

        # Check if this ticker already has data
        ticker_dir = os.path.join(DATA_DIR, ticker, "10-K")
        if os.path.isdir(ticker_dir) and any(
            f.endswith((".htm", ".html", ".txt")) for f in os.listdir(ticker_dir)
        ):
            print("-- already downloaded, skipping")
            skipped += 1
            continue

        try:
            dl.get(
                "10-K",
                ticker,
                limit=limit,
                after=after,
                download_details=True,
            )
            print("-- OK")
            success += 1
        except Exception as e:
            print(f"-- FAILED: {e}")
            failed += 1

        # Small delay between requests (sec-edgar-downloader handles rate limits,
        # but a small extra delay helps avoid any issues)
        if i > 0 and i % 20 == 0:
            time.sleep(1)

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"Download complete in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"  Success: {success}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed:  {failed}")
    print(f"  Total:   {total}")


def main():
    """Main entry point: fetch tickers and download filings."""
    # Fetch S&P 500 tickers
    tickers = fetch_sp500_tickers()

    if not tickers:
        print("ERROR: No tickers found. Exiting.")
        sys.exit(1)

    print(f"\nReady to download latest 10-K for {len(tickers)} S&P 500 companies.")
    print("This may take 10-20 minutes due to SEC rate limits (10 req/s).")
    print("Press Ctrl+C to cancel, or Enter to continue...")

    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)

    download_filings(tickers, limit=1, after="2023-01-01")


if __name__ == "__main__":
    main()
