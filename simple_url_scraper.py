#!/usr/bin/env python3
"""
Simple URL input scraper
Just paste URL and scrape
"""

from scraper import MetaAdsScraper
import config


def main():
    print("\n" + "="*70)
    print(" "*15 + "SIMPLE URL SCRAPER")
    print("="*70)
    print("\nPaste Meta Ads Library URL and scrape instantly")
    print("Example URL format:")
    print("https://www.facebook.com/ads/library/?active_status=active&...")
    print("-" * 70 + "\n")
    
    # Get URL
    url = input("🔗 Paste your URL: ").strip()
    
    if not url:
        print("No URL provided. Exiting.")
        return
    
    # Scrape
    print("\n⏳ Scraping... This may take a few minutes.\n")
    
    scraper = MetaAdsScraper()
    ads_data = scraper.scrape(url)
    
    # Export
    if ads_data:
        output_file = scraper.export_to_excel()
        print(f"\n{'='*70}")
        print("✅ SCRAPING COMPLETED!")
        print(f"{'='*70}")
        print(f"📊 Total Ads: {len(ads_data)}")
        print(f"💾 Exported to: {output_file}")
        print(f"\n⏭️  Next: python cluster_analysis.py {output_file}")
        print(f"{'='*70}\n")
    else:
        print("✗ No ads found")


if __name__ == "__main__":
    main()
