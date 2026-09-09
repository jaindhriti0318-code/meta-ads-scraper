#!/usr/bin/env python3
"""
Multi-Brand Meta Ads Scraper
Scrapes ads for multiple brands and clusters them
"""

import os
import sys
import logging
from typing import List, Dict, Optional
from datetime import datetime

from scraper import MetaAdsScraper
import config
import brands_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_brand_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MultiBrandScraper:
    """Scrapes ads for multiple brands and aggregates results"""
    
    def __init__(self):
        """Initialize multi-brand scraper"""
        self.results = {}
        self.all_ads_data = []
        self.scrape_summary = {}
    
    def scrape_brand(self, brand_key: str, url_type: str = 'by_advertiser') -> Dict:
        """
        Scrape ads for a single brand
        
        Args:
            brand_key: Key from brands_config.BRANDS
            url_type: Type of URL to use
        
        Returns:
            Dictionary with scrape results
        """
        try:
            brand = brands_config.BRANDS[brand_key]
            logger.info(f"\n{'='*70}")
            logger.info(f"Scraping: {brand['name']}")
            logger.info(f"{'='*70}")
            
            # Generate URL
            url = brands_config.generate_url(brand_key, url_type)
            logger.info(f"URL: {url[:100]}...")
            
            # Create scraper
            scraper = MetaAdsScraper()
            
            # Scrape
            ads_data = scraper.scrape(url)
            
            # Store results
            result = {
                'brand_key': brand_key,
                'brand_name': brand['name'],
                'ads_count': len(ads_data),
                'ads_data': ads_data,
                'status': 'success' if ads_data else 'no_ads',
                'timestamp': datetime.now().isoformat()
            }
            
            self.results[brand_key] = result
            self.all_ads_data.extend(ads_data)
            
            logger.info(f"✓ Scraped {len(ads_data)} ads for {brand['name']}")
            return result
            
        except Exception as e:
            logger.error(f"✗ Error scraping {brand_key}: {e}")
            self.results[brand_key] = {
                'brand_key': brand_key,
                'brand_name': brands_config.BRANDS[brand_key]['name'],
                'ads_count': 0,
                'ads_data': [],
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return self.results[brand_key]
    
    def scrape_multiple_brands(self, brand_keys: Optional[List[str]] = None, url_types: Optional[List[str]] = None) -> Dict:
        """
        Scrape ads for multiple brands
        
        Args:
            brand_keys: List of brand keys to scrape (default: all)
            url_types: List of URL types to try (default: ['by_advertiser'])
        
        Returns:
            Dictionary with all results
        """
        if brand_keys is None:
            brand_keys = list(brands_config.BRANDS.keys())
        
        if url_types is None:
            url_types = ['by_advertiser']
        
        logger.info(f"\n{'#'*70}")
        logger.info(f"Starting Multi-Brand Scrape")
        logger.info(f"Brands: {len(brand_keys)}")
        logger.info(f"URL Types: {', '.join(url_types)}")
        logger.info(f"{'#'*70}\n")
        
        for brand_key in brand_keys:
            if brand_key not in brands_config.BRANDS:
                logger.warning(f"Brand '{brand_key}' not found, skipping...")
                continue
            
            for url_type in url_types:
                self.scrape_brand(brand_key, url_type)
        
        # Generate summary
        self._generate_summary()
        
        return self.results
    
    def _generate_summary(self):
        """Generate scraping summary"""
        total_ads = len(self.all_ads_data)
        successful_brands = len([r for r in self.results.values() if r['status'] == 'success'])
        failed_brands = len([r for r in self.results.values() if r['status'] == 'error'])
        no_ads_brands = len([r for r in self.results.values() if r['status'] == 'no_ads'])
        
        self.scrape_summary = {
            'total_brands': len(self.results),
            'successful_brands': successful_brands,
            'failed_brands': failed_brands,
            'no_ads_brands': no_ads_brands,
            'total_ads': total_ads,
            'timestamp': datetime.now().isoformat()
        }
    
    def export_to_excel(self, filename: Optional[str] = None) -> str:
        """
        Export all scraped data to Excel
        
        Args:
            filename: Custom filename
        
        Returns:
            Path to exported file
        """
        try:
            import pandas as pd
            
            os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
            
            # Generate filename
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"multi_brand_ads_{timestamp}.xlsx"
            
            filepath = os.path.join(config.OUTPUT_FOLDER, filename)
            
            # Convert to DataFrame
            if self.all_ads_data:
                df = pd.DataFrame(self.all_ads_data)
                
                # Add brand name column
                def get_brand_name(ad_id):
                    for result in self.results.values():
                        if any(ad.get('ad_id') == ad_id for ad in result.get('ads_data', [])):
                            return result['brand_name']
                    return 'Unknown'
                
                df['brand'] = df['ad_id'].apply(lambda x: [r['brand_name'] for r in self.results.values() if x in [ad.get('ad_id') for ad in r.get('ads_data', [])]])
                df['brand'] = df['brand'].apply(lambda x: x[0] if x else 'Unknown')
                
                # Reorder columns
                column_order = [
                    'brand',
                    'ad_id',
                    'ad_copy',
                    'ad_format',
                    'cta_type',
                    'orientation',
                    'dominant_colors',
                    'text_density',
                    'layout_pattern',
                    'brand_indicators',
                    'ad_creative_images',
                    'image_count',
                    'date_range_start',
                    'date_range_end',
                    'landing_page_url',
                    'scraped_at'
                ]
                
                available_cols = [col for col in column_order if col in df.columns]
                df = df[available_cols]
                
                # Write to Excel
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='All_Ads', index=False)
                    
                    # Create summary sheet
                    summary_df = pd.DataFrame([
                        {
                            'Brand': result['brand_name'],
                            'Ads Count': result['ads_count'],
                            'Status': result['status']
                        }
                        for result in self.results.values()
                    ])
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Auto-adjust columns
                    for worksheet in writer.sheets.values():
                        for column in worksheet.columns:
                            max_length = 0
                            column_letter = column[0].column_letter
                            for cell in column:
                                try:
                                    if len(str(cell.value)) > max_length:
                                        max_length = len(str(cell.value))
                                except:
                                    pass
                            adjusted_width = min(max_length + 2, 50)
                            worksheet.column_dimensions[column_letter].width = adjusted_width
                
                logger.info(f"Data exported to: {filepath}")
                return filepath
            else:
                logger.warning("No ads to export")
                return ""
                
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return ""
    
    def print_summary(self):
        """Print scraping summary"""
        print("\n" + "="*70)
        print("MULTI-BRAND SCRAPING SUMMARY")
        print("="*70)
        print(f"\nTotal Brands Configured: {self.scrape_summary.get('total_brands', 0)}")
        print(f"Successfully Scraped: {self.scrape_summary.get('successful_brands', 0)}")
        print(f"Failed: {self.scrape_summary.get('failed_brands', 0)}")
        print(f"No Ads Found: {self.scrape_summary.get('no_ads_brands', 0)}")
        print(f"\nTotal Ads Collected: {self.scrape_summary.get('total_ads', 0)}")
        
        print("\nBrand Breakdown:")
        print("-" * 70)
        print(f"{'Brand':<30} {'Ads':<10} {'Status':<15}")
        print("-" * 70)
        
        for result in sorted(self.results.values(), key=lambda x: x['ads_count'], reverse=True):
            print(f"{result['brand_name']:<30} {result['ads_count']:<10} {result['status']:<15}")
        
        print("\n" + "="*70 + "\n")


def main():
    """Main entry point"""
    print("\n" + "="*70)
    print(" "*10 + "MULTI-BRAND META ADS SCRAPER")
    print(" "*10 + "Health & Wellness D2C Brands")
    print("="*70)
    
    print("\nAvailable Options:")
    print("1. Scrape ALL configured brands")
    print("2. Scrape specific brands")
    print("3. Manual URL input")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    scraper = MultiBrandScraper()
    
    if choice == "1":
        print(f"\nScraping all {len(brands_config.BRANDS)} brands...")
        scraper.scrape_multiple_brands()
    
    elif choice == "2":
        print("\nAvailable Brands:")
        for i, (key, brand) in enumerate(brands_config.BRANDS.items(), 1):
            print(f"{i}. {brand['name']}")
        
        selection = input("\nEnter brand numbers (comma-separated, e.g., 1,3,5): ").strip()
        selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
        selected_brands = [list(brands_config.BRANDS.keys())[i] for i in selected_indices if i < len(brands_config.BRANDS)]
        
        if selected_brands:
            print(f"\nScraping {len(selected_brands)} selected brands...")
            scraper.scrape_multiple_brands(selected_brands)
        else:
            print("No valid selection")
            return
    
    elif choice == "3":
        print("\nEnter URLs (one per line, empty line to finish):")
        urls = []
        while True:
            url = input("URL: ").strip()
            if not url:
                break
            urls.append(url)
        
        if urls:
            print(f"\nScraping {len(urls)} manual URLs...")
            for i, url in enumerate(urls, 1):
                logger.info(f"\nScraping URL {i}/{len(urls)}")
                scraper_instance = MetaAdsScraper()
                ads = scraper_instance.scrape(url)
                scraper.all_ads_data.extend(ads)
                scraper.results[f"manual_{i}"] = {
                    'brand_name': f"Manual URL {i}",
                    'ads_count': len(ads),
                    'status': 'success' if ads else 'no_ads',
                    'timestamp': datetime.now().isoformat()
                }
            scraper._generate_summary()
        else:
            print("No URLs provided")
            return
    
    else:
        print("Invalid option")
        return
    
    # Print summary
    scraper.print_summary()
    
    # Export results
    if scraper.all_ads_data:
        output_file = scraper.export_to_excel()
        print(f"\n✓ Exported to: {output_file}")
        print(f"\n⏭️  Next Step: Run 'python cluster_analysis.py {output_file}' for clustering analysis")
    else:
        print("\n✗ No data to export")


if __name__ == "__main__":
    main()
