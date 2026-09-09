#!/usr/bin/env python3
"""
Quick setup guide and brand page finder
Helps find Facebook page IDs for brands
"""

import logging
from typing import Optional
import brands_config

logger = logging.getLogger(__name__)


def display_setup_guide():
    """Display setup guide"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  META ADS SCRAPER - SETUP GUIDE                            ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 QUICK START GUIDE
════════════════════════════════════════════════════════════════════════════

1️⃣  OPTION A: Scrape Pre-configured Brands
    ─────────────────────────────────────
    python multi_brand_scraper.py
    - Select option 1 to scrape all health & wellness brands
    - Or select specific brands
    
    Pre-configured brands:
    • Kapiva
    • OZiva  
    • Zandu (Emami)
    • Dabur
    • Himalaya Wellness
    • Patanjali
    • Wow Skin Science
    • MuscleBlaze
    • HealthKart
    • Mamaearth


2️⃣  OPTION B: Scrape with Custom Brand URLs
    ────────────────────────────────────────
    python multi_brand_scraper.py
    - Select option 3 to enter manual URLs
    - Paste Meta Ads Library URLs one by one
    - Leave blank line when done


3️⃣  OPTION C: Single URL Scraper
    ─────────────────────────────
    python simple_url_scraper.py
    - Just paste a Meta Ads Library URL
    - Get Excel file automatically


4️⃣  Cluster Analysis
    ───────────────────
    python cluster_analysis.py output/multi_brand_ads_*.xlsx
    - Analyzes visual similarity of ad creatives
    - Groups into clusters with detailed analysis
    - Exports cluster report with insights


📌 WHAT'S BEING COLLECTED
════════════════════════════════════════════════════════════════════════════

Each scraped ad includes:
✓ Ad Creative Images (thumbnails, URL references)
✓ Ad Copy (text content)
✓ CTA Type (Shop Now, Learn More, etc.)
✓ Ad Format (Image, Video, Carousel)
✓ Orientation (Horizontal, Vertical, Square)
✓ Dominant Colors (palette analysis)
✓ Text Density (minimal, light, moderate, heavy)
✓ Layout Pattern (product-focused, lifestyle, testimonial, offer-heavy)
✓ Brand Indicators
✓ Landing Page URL
✓ Date Range (when active)


🔍 FINDING FACEBOOK PAGE IDs
════════════════════════════════════════════════════════════════════════════

To update brands with correct Facebook Page IDs:

1. Go to: https://www.facebook.com/ads/library/
2. Search for the brand name
3. Click on the brand page
4. Look at URL: facebook.com/[BRAND_NAME]/
   Find the numeric ID by:
   - Right-click → Inspect → Find 'page_id' in data attributes
   - Or use: facebook.com/ads/library/?search_type=page&search_query=[BRAND]

5. Update brands_config.py:
   BRANDS['brand_key']['facebook_page_id'] = 'ACTUAL_PAGE_ID'


📊 OUTPUT FILES
════════════════════════════════════════════════════════════════════════════

After scraping:
📁 output/
   ├── multi_brand_ads_YYYYMMDD_HHMMSS.xlsx      (All scraped ads)
   ├── images/                                     (Downloaded ad images)
   └── clusters/
       ├── cluster_summary_*.xlsx                  (Cluster analysis)
       ├── clusters_detailed_*.xlsx                (Ads with cluster IDs)
       ├── cluster_analysis_*.json                 (Detailed JSON data)
       └── cluster_report_*.txt                    (Human-readable report)

Log files:
📄 scraper.log                                     (Scraping details)
📄 clustering.log                                  (Clustering details)
📄 multi_brand_scraper.log                        (Multi-brand scraping)


⚡ PERFORMANCE TIPS
════════════════════════════════════════════════════════════════════════════

• Adjust config.py settings:
  - MAX_SCROLL_ATTEMPTS: Increase for more ads
  - HEADLESS: False to watch scraping
  - SAVE_IMAGES: False to speed up (disables color analysis)

• For large batches:
  - Scrape brands separately, then combine
  - Reduce MAX_SCROLL_ATTEMPTS for faster runs
  - Run clustering analysis separately


⚠️  REQUIREMENTS
════════════════════════════════════════════════════════════════════════════

Install dependencies:
  pip install -r requirements.txt

Needed:
✓ Python 3.8+
✓ Google Chrome/Chromium browser
✓ Internet connection
✓ 2GB+ RAM recommended
✓ 1GB+ disk space for images


🆘 TROUBLESHOOTING
════════════════════════════════════════════════════════════════════════════

No ads found?
  → Check URL is correct Meta Ads Library URL
  → Try different filters in URL
  → Check scraper.log for details

Chrome driver issues?
  → Auto-downloaded, but may need Chrome installed
  → Run: pip install webdriver-manager --upgrade

Memory issues?
  → Reduce MAX_SCROLL_ATTEMPTS in config.py
  → Set SAVE_IMAGES = False
  → Scrape fewer brands at once

Slow performance?
  → Check internet connection
  → Reduce window size in config.py
  → Run at off-peak hours


📞 SUPPORT
════════════════════════════════════════════════════════════════════════════

Check logs for detailed error messages:
  tail -f scraper.log
  tail -f clustering.log

Common issues documented in README.md

╚════════════════════════════════════════════════════════════════════════════╝
    """)


def find_brand_info(brand_name: str) -> Optional[dict]:
    """Find brand configuration"""
    for key, brand in brands_config.BRANDS.items():
        if brand_name.lower() in [b.lower() for b in [brand['name']] + brand.get('search_keywords', [])]:
            return {'key': key, 'brand': brand}
    return None


def main():
    print("\n" + "="*70)
    print(" "*15 + "SETUP & CONFIGURATION")
    print("="*70 + "\n")
    
    print("Select an option:")
    print("1. Display full setup guide")
    print("2. List all configured brands")
    print("3. Find brand information")
    print("4. Generate brand URLs")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        display_setup_guide()
    
    elif choice == "2":
        print("\nConfigured Brands:\n")
        for key, brand in brands_config.BRANDS.items():
            print(f"  • {brand['name']}")
            print(f"    Key: {key}")
            print(f"    Category: {brand['category']}")
            print(f"    Page ID: {brand['facebook_page_id']}")
            print()
    
    elif choice == "3":
        brand_name = input("Enter brand name to search: ").strip()
        result = find_brand_info(brand_name)
        if result:
            print(f"\nFound: {result['brand']['name']}")
            print(f"Key: {result['key']}")
            print(f"Config: {result['brand']}")
        else:
            print(f"Brand '{brand_name}' not found")
    
    elif choice == "4":
        print("\nGenerating URLs for all brands...\n")
        urls = brands_config.get_all_brand_urls(all_types=True)
        for brand_key, brand_urls in urls.items():
            print(f"\n{brands_config.BRANDS[brand_key]['name']}:")
            for url_type, url in brand_urls.items():
                print(f"  {url_type}:")
                print(f"    {url}")


if __name__ == "__main__":
    main()
