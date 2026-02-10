"""Detailed diagnostic for judgment page structure."""

import requests
from bs4 import BeautifulSoup

try:
    url = "https://indiankanoon.org/doc/1560742/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {r.status_code}\n")
    
    soup = BeautifulSoup(r.text, "lxml")
    
    # Find article.middle_column
    article = soup.select_one("article.middle_column")
    if article:
        print("✓ Found article.middle_column")
        print(f"  Text length: {len(article.get_text())} chars")
        print(f"\n  Children of article:")
        for i, child in enumerate(article.children):
            if hasattr(child, 'name') and child.name:
                print(f"    {i}: <{child.name}> with class={child.get('class', [])}")
        
        # Get first 2000 chars of content
        print(f"\n  First 2000 chars of text:")
        print(article.get_text()[:2000])
        print("\n" + "="*80)
        
        # Look for text containers
        for selector in [".judgement", ".content", "p", ".doc_content", "div[id*='content']"]:
            elements = article.select(selector)
            if elements:
                print(f"\n✓ Found {len(elements)} elements with {selector} inside article")
        
        # Check for divs with specific classes
        print(f"\n  All divs inside article:")
        for div in article.find_all("div", recursive=True, limit=10):
            classes = div.get("class", [])
            print(f"    <div class='{' '.join(classes)}'> - text: {len(div.get_text())} chars")
    
    # Also check for the actual document text location
    print("\n" + "="*80)
    print("LOOKING FOR ACTUAL DOC TEXT")
    print("="*80)
    
    # Try finding by data attributes
    for elem in soup.find_all(True):  # All elements
        if elem.get("data-doc") or elem.get("data-docfragment"):
            print(f"\n✓ Found element with data attribute: <{elem.name}> {elem.get('class', [])}")
            print(f"  Attributes: {elem.attrs}")

except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
