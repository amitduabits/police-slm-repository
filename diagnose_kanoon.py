"""Diagnostic script to inspect Indian Kanoon HTML structure."""

import requests
from bs4 import BeautifulSoup

# Test search page
print("=" * 80)
print("FETCHING SEARCH RESULTS PAGE")
print("=" * 80)

try:
    url = "https://indiankanoon.org/search/?formInput=Gujarat+murder+Section+302"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "lxml")
        
        # Print first 3000 chars of HTML
        print("\nFull page snippet (first 3000 chars):")
        print(r.text[:3000])
        
        # Look for common article/result containers
        print("\n" + "=" * 80)
        print("LOOKING FOR RESULT CONTAINERS")
        print("=" * 80)
        
        # Try different selectors
        selectors_to_try = [
            ".result",
            ".search-result",
            ".judgement-result",
            "article",
            ".result-item",
            ".item",
            "div[class*='result']",
            ".search_item"
        ]
        
        for selector in selectors_to_try:
            elements = soup.select(selector)
            if elements:
                print(f"\n✓ Found {len(elements)} elements with selector: {selector}")
                if len(elements) > 0:
                    print(f"  First element HTML:\n{str(elements[0])[:500]}")
        
        # Get all divs with class containing 'result'
        print("\n" + "=" * 80)
        print("ALL DIVS WITH CLASSES CONTAINING 'result'")
        print("=" * 80)
        divs = soup.find_all("div", class_=lambda x: x and "result" in x.lower() if x else False)
        print(f"Found {len(divs)} divs")
        if divs:
            print(f"First one:\n{str(divs[0])[:800]}")

except Exception as e:
    print(f"ERROR: {e}")

# Test judgment page
print("\n\n" + "=" * 80)
print("FETCHING JUDGMENT PAGE")
print("=" * 80)

try:
    # Use a real doc ID from Indian Kanoon
    url = "https://indiankanoon.org/doc/1560742/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "lxml")
        
        print("\nFull page snippet (first 3000 chars):")
        print(r.text[:3000])
        
        # Look for judgment text
        print("\n" + "=" * 80)
        print("LOOKING FOR JUDGMENT TEXT")
        print("=" * 80)
        
        selectors = [
            "#judgment",
            ".judgments",
            ".expanded",
            ".judgment-content",
            ".content",
            "div[class*='judgment']",
            "div[class*='doc']",
            "main",
            ".judgement",
            "[role='main']"
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                print(f"\n✓ Found {len(elements)} elements with selector: {selector}")
                if len(elements) > 0:
                    text_len = len(elements[0].get_text())
                    print(f"  Text length: {text_len} chars")
                    print(f"  HTML snippet:\n{str(elements[0])[:600]}")

except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 80)
print("DONE - Check output above to see actual HTML structure")
print("=" * 80)
