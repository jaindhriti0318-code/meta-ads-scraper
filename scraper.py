"""
Meta Ads Library Scraper with Visual Clustering Support
Scrapes ad data from Facebook Ads Library and exports to Excel with image analysis
"""

import os
import time
import logging
import requests
import urllib.parse
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from PIL import Image
import pandas as pd
from bs4 import BeautifulSoup
import io

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MetaAdsScraper:
    """Scraper for Meta Ads Library with visual clustering capabilities"""
    
    def __init__(self):
        """Initialize the scraper"""
        self.driver = None
        self.wait = None
        self.ads_data = []
        self.image_counter = 0
        
        # Create output directories
        os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
        if config.SAVE_IMAGES:
            os.makedirs(config.IMAGE_FOLDER, exist_ok=True)
        
    def setup_driver(self):
        """Set up Selenium WebDriver"""
        try:
            logger.info("Setting up Chrome WebDriver...")
            options = webdriver.ChromeOptions()
            
            if config.HEADLESS:
                options.add_argument("--headless")
            
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
            self.wait = WebDriverWait(self.driver, config.WAIT_TIME)
            
            logger.info("WebDriver setup completed successfully")
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {e}")
            raise
    
    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")
    
    def load_page(self, url: str) -> bool:
        """Load the Meta Ads Library page"""
        try:
            logger.info(f"Loading URL: {url}")
            self.driver.get(url)
            time.sleep(config.SCROLL_PAUSE_TIME)
            
            # Wait for page to load
            try:
                self.wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'adCard')]|//div[@data-test='ad']")))
                logger.info("Page loaded successfully")
                return True
            except TimeoutException:
                logger.warning("Timeout waiting for ads to load, proceeding anyway...")
                return True
                
        except Exception as e:
            logger.error(f"Error loading page: {e}")
            return False
    
    def scroll_and_load_ads(self, max_attempts: int = config.MAX_SCROLL_ATTEMPTS) -> List[Dict]:
        """Scroll through the page to load all ads"""
        logger.info("Starting to scroll and load ads...")
        
        ads_found = set()
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for attempt in range(max_attempts):
            try:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(config.SCROLL_PAUSE_TIME)
                
                # Extract ads on current page
                current_ads = self._extract_ads_from_page()
                
                # Track unique ads
                current_ad_count = len(current_ads)
                new_ads_count = len(current_ads) - len(ads_found)
                
                logger.info(f"Scroll attempt {attempt + 1}: Found {current_ad_count} ads total, {new_ads_count} new ads")
                
                ads_found = set(ad.get('unique_id', str(ad)) for ad in current_ads)
                
                # Check if we've reached the end
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    logger.info("Reached end of page (no new content loaded)")
                    break
                last_height = new_height
                
            except Exception as e:
                logger.warning(f"Error during scroll attempt {attempt + 1}: {e}")
                continue
        
        # Final extraction
        final_ads = self._extract_ads_from_page()
        logger.info(f"Total ads extracted: {len(final_ads)}")
        return final_ads
    
    def _extract_ads_from_page(self) -> List[Dict]:
        """Extract ad data from current page"""
        ads = []
        try:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find all ad containers
            ad_containers = soup.find_all('div', {'data-test': 'ad'}) or \
                           soup.find_all('div', class_=lambda x: x and 'adCard' in (x or ''))
            
            logger.info(f"Found {len(ad_containers)} ad containers on page")
            
            for idx, container in enumerate(ad_containers):
                try:
                    ad_data = self._parse_ad_container(container, idx)
                    if ad_data and ad_data not in ads:
                        ads.append(ad_data)
                except Exception as e:
                    logger.warning(f"Error parsing ad container {idx}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error extracting ads from page: {e}")
        
        return ads
    
    def _parse_ad_container(self, container, idx: int) -> Optional[Dict]:
        """Parse individual ad container to extract all clustering data"""
        try:
            # Extract images for clustering
            images_data = self._extract_images_with_analysis(container)
            
            ad_data = {
                'ad_id': f"ad_{idx}_{datetime.now().timestamp()}",
                'unique_id': f"ad_{idx}_{datetime.now().timestamp()}",
                # Core data
                'ad_copy': self._extract_text(container),
                'ad_creative_images': images_data['urls'],
                'image_count': images_data['count'],
                'image_local_paths': images_data['local_paths'],
                # Clustering features
                'cta_type': self._extract_cta(container),
                'ad_format': self._extract_format(container),
                'orientation': self._extract_orientation(images_data),
                'dominant_colors': images_data['dominant_colors'],
                'text_density': self._extract_text_density(container, images_data),
                'layout_pattern': self._extract_layout_pattern(container, images_data),
                'brand_indicators': self._extract_brand_indicators(container),
                # Metadata
                'date_range_start': self._extract_date_range_start(container),
                'date_range_end': self._extract_date_range_end(container),
                'landing_page_url': self._extract_landing_url(container),
                'scraped_at': datetime.now().isoformat()
            }
            
            # Only return if we have some data
            if any([ad_data.get('ad_creative_images'), ad_data.get('ad_copy'), ad_data.get('landing_page_url')]):
                return ad_data
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing ad container: {e}")
            return None
    
    def _extract_images_with_analysis(self, container) -> Dict:
        """Extract images and perform visual analysis for clustering"""
        try:
            images_data = {
                'urls': [],
                'local_paths': [],
                'count': 0,
                'dominant_colors': [],
                'dimensions': []
            }
            
            img_elements = container.find_all('img')
            
            for img in img_elements:
                try:
                    src = img.get('src') or img.get('data-src')
                    if src and 'http' in src:
                        # Download and save image
                        local_path = self._download_image(src) if config.SAVE_IMAGES else None
                        
                        images_data['urls'].append(src)
                        if local_path:
                            images_data['local_paths'].append(local_path)
                            
                            # Analyze image
                            colors = self._analyze_image_colors(local_path)
                            dimensions = self._get_image_dimensions(local_path)
                            
                            images_data['dominant_colors'].append(colors)
                            images_data['dimensions'].append(dimensions)
                except Exception as e:
                    logger.debug(f"Error processing image: {e}")
                    continue
            
            images_data['count'] = len(images_data['urls'])
            return images_data
            
        except Exception as e:
            logger.debug(f"Error extracting images: {e}")
            return {'urls': [], 'local_paths': [], 'count': 0, 'dominant_colors': [], 'dimensions': []}
    
    def _download_image(self, url: str) -> Optional[str]:
        """Download image from URL and save locally"""
        try:
            self.image_counter += 1
            filename = f"ad_image_{self.image_counter}.jpg"
            filepath = os.path.join(config.IMAGE_FOLDER, filename)
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # Open image and resize
                img = Image.open(io.BytesIO(response.content))
                img.thumbnail(config.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
                img.save(filepath, 'JPEG', quality=config.IMAGE_QUALITY)
                logger.debug(f"Image saved: {filepath}")
                return filepath
        except Exception as e:
            logger.debug(f"Error downloading image: {e}")
        return None
    
    def _analyze_image_colors(self, image_path: str) -> str:
        """Analyze dominant colors in image"""
        try:
            img = Image.open(image_path)
            # Resize for faster processing
            img.thumbnail((150, 150))
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get color palette
            img_reduced = img.quantize(colors=5)  # Reduce to 5 main colors
            colors = img_reduced.palette.getdata()[1]
            
            # Convert to hex colors
            color_names = []
            for i in range(0, min(15, len(colors)), 3):
                r, g, b = colors[i:i+3]
                hex_color = '#{:02x}{:02x}{:02x}'.format(r, g, b)
                color_names.append(hex_color)
            
            return '|'.join(color_names[:5]) if color_names else 'Unknown'
        except Exception as e:
            logger.debug(f"Error analyzing colors: {e}")
            return 'Unknown'
    
    def _get_image_dimensions(self, image_path: str) -> str:
        """Get image dimensions for orientation analysis"""
        try:
            img = Image.open(image_path)
            width, height = img.size
            return f"{width}x{height}"
        except Exception as e:
            logger.debug(f"Error getting dimensions: {e}")
            return 'Unknown'
    
    def _extract_orientation(self, images_data: Dict) -> str:
        """Determine image orientation (horizontal, vertical, square)"""
        try:
            if not images_data.get('dimensions'):
                return 'Unknown'
            
            # Analyze first image dimensions
            for dim in images_data['dimensions']:
                try:
                    width, height = map(int, dim.split('x'))
                    aspect_ratio = width / height if height > 0 else 1
                    
                    if 0.9 < aspect_ratio < 1.1:
                        return 'Square'
                    elif aspect_ratio > 1.1:
                        return 'Horizontal'
                    else:
                        return 'Vertical'
                except:
                    continue
            
            return 'Unknown'
        except Exception as e:
            logger.debug(f"Error determining orientation: {e}")
            return 'Unknown'
    
    def _extract_text_density(self, container, images_data: Dict) -> str:
        """Analyze text overlay density"""
        try:
            text = container.get_text(strip=True)
            text_length = len(text)
            image_count = images_data.get('count', 1)
            
            # Estimate text density
            density_score = text_length / (image_count * 100)
            
            if density_score > 2:
                return 'Heavy Text Overlay'
            elif density_score > 1:
                return 'Moderate Text'
            elif density_score > 0.3:
                return 'Light Text'
            else:
                return 'Minimal Text'
        except Exception as e:
            logger.debug(f"Error analyzing text density: {e}")
            return 'Unknown'
    
    def _extract_layout_pattern(self, container, images_data: Dict) -> str:
        """Identify layout pattern"""
        try:
            text = container.get_text().lower()
            html = str(container).lower()
            
            # Check for testimonial indicators
            if any(word in text for word in ['review', 'rating', '⭐', '★', 'customer', 'says', 'quote']):
                return 'Testimonial-style'
            
            # Check for offer/discount
            if any(word in text for word in ['discount', 'sale', 'offer', '%', 'off', 'free', 'deal', 'limited']):
                return 'Offer/Discount-heavy'
            
            # Check for lifestyle imagery
            if any(word in text for word in ['lifestyle', 'experience', 'moment', 'live', 'enjoy', 'discover']):
                return 'Lifestyle Imagery'
            
            # Check for product-focused
            if any(word in text for word in ['product', 'new', 'shop', 'buy', 'available', 'feature']):
                return 'Product-focused'
            
            return 'General'
        except Exception as e:
            logger.debug(f"Error extracting layout pattern: {e}")
            return 'Unknown'
    
    def _extract_brand_indicators(self, container) -> str:
        """Extract potential brand indicators"""
        try:
            text = container.get_text()
            # Look for common brand identifiers
            if any(char.isupper() for char in text[:100]):
                # Extract first few capitalized words as brand indicators
                words = text.split()
                brand_words = [w for w in words[:5] if w and w[0].isupper()]
                return '|'.join(brand_words[:3]) if brand_words else 'Generic'
            return 'Generic'
        except Exception as e:
            logger.debug(f"Error extracting brand: {e}")
            return 'Unknown'
    
    def _extract_text(self, container) -> str:
        """Extract ad copy/text from container"""
        try:
            text_elements = container.find_all(['p', 'span', 'div'], class_=lambda x: x and ('text' in (x or '') or 'copy' in (x or '')))
            
            texts = []
            for elem in text_elements:
                text = elem.get_text(strip=True)
                if text and len(text) > 10:
                    texts.append(text)
            
            return ' | '.join(texts[:3]) if texts else 'N/A'
        except Exception as e:
            logger.debug(f"Error extracting text: {e}")
            return 'N/A'
    
    def _extract_cta(self, container) -> str:
        """Extract Call-to-Action type"""
        try:
            cta_keywords = ['learn more', 'shop now', 'sign up', 'download', 'get started', 'contact us', 'call', 'book', 'subscribe', 'register']
            text = container.get_text().lower()
            
            for keyword in cta_keywords:
                if keyword in text:
                    return keyword.title()
            
            buttons = container.find_all(['button', 'a'], class_=lambda x: x and 'button' in (x or '').lower())
            if buttons:
                for btn in buttons:
                    btn_text = btn.get_text(strip=True)
                    if btn_text:
                        return btn_text
            
            return 'N/A'
        except Exception as e:
            logger.debug(f"Error extracting CTA: {e}")
            return 'N/A'
    
    def _extract_format(self, container) -> str:
        """Extract ad format (image, video, carousel)"""
        try:
            text = str(container).lower()
            
            if 'video' in text or '<video' in text:
                return 'Video'
            elif 'carousel' in text:
                return 'Carousel'
            elif 'img' in text or 'image' in text:
                return 'Image'
            else:
                return 'Unknown'
        except Exception as e:
            logger.debug(f"Error extracting format: {e}")
            return 'Unknown'
    
    def _extract_date_range_start(self, container) -> str:
        """Extract ad start date"""
        try:
            text = container.get_text()
            if 'active' in text.lower():
                return 'Active'
            return 'N/A'
        except Exception as e:
            logger.debug(f"Error extracting start date: {e}")
            return 'N/A'
    
    def _extract_date_range_end(self, container) -> str:
        """Extract ad end date"""
        try:
            return 'Ongoing'
        except Exception as e:
            logger.debug(f"Error extracting end date: {e}")
            return 'N/A'
    
    def _extract_landing_url(self, container) -> str:
        """Extract landing page URL"""
        try:
            links = container.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if href and 'http' in href and 'facebook.com' not in href and 'instagram.com' not in href:
                    return href
            return 'N/A'
        except Exception as e:
            logger.debug(f"Error extracting landing URL: {e}")
            return 'N/A'
    
    def scrape(self, url: str) -> List[Dict]:
        """Main scraping method"""
        try:
            logger.info("=" * 70)
            logger.info("Starting Meta Ads Library Scrape with Clustering Data")
            logger.info("=" * 70)
            
            # Validate URL
            if not self._validate_url(url):
                logger.error("Invalid Meta Ads Library URL")
                return []
            
            # Setup driver
            self.setup_driver()
            
            # Load page
            if not self.load_page(url):
                logger.error("Failed to load page")
                return []
            
            # Scroll and extract ads
            self.ads_data = self.scroll_and_load_ads()
            
            logger.info(f"Scraping completed. Total ads: {len(self.ads_data)}")
            logger.info("=" * 70)
            
            return self.ads_data
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return []
        finally:
            self.close_driver()
    
    def _validate_url(self, url: str) -> bool:
        """Validate if URL is from Meta Ads Library"""
        try:
            if 'facebook.com/ads/library' in url:
                logger.info("URL validated successfully")
                return True
            else:
                logger.error("URL must be from facebook.com/ads/library")
                return False
        except Exception as e:
            logger.error(f"Error validating URL: {e}")
            return False
    
    def export_to_excel(self, filename: Optional[str] = None) -> str:
        """Export scraped data to Excel file with clustering information"""
        try:
            os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if config.TIMESTAMP_OUTPUT else ""
                filename = f"meta_ads_{timestamp}.xlsx" if timestamp else "meta_ads.xlsx"
            
            filepath = os.path.join(config.OUTPUT_FOLDER, filename)
            
            # Convert to DataFrame
            df = pd.DataFrame(self.ads_data)
            
            # Reorder columns for better readability
            column_order = [
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
                'image_local_paths',
                'date_range_start',
                'date_range_end',
                'landing_page_url',
                'scraped_at'
            ]
            
            available_cols = [col for col in column_order if col in df.columns]
            df = df[available_cols]
            
            # Write to Excel with formatting
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Ads', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Ads']
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
            logger.info(f"Total rows: {len(df)}")
            logger.info(f"Clustering features collected: orientation, dominant_colors, text_density, layout_pattern, brand_indicators")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return ""


def main():
    """Main entry point"""
    print("\n" + "="*70)
    print(" "*15 + "META ADS LIBRARY SCRAPER v2.0")
    print(" "*10 + "With Visual Clustering Support")
    print("="*70)
    print("\n📋 PASTE YOUR META ADS LIBRARY URL")
    print("-" * 70)
    print("Example URL format:")
    print("https://www.facebook.com/ads/library/?active_status=active&...")
    print("-" * 70 + "\n")
    
    url = input("🔗 Enter Meta Ads Library URL: ").strip()
    
    if not url:
        print("❌ No URL provided. Exiting.")
        return
    
    print("\n⏳ Starting scraper... This may take several minutes.\n")
    
    scraper = MetaAdsScraper()
    ads_data = scraper.scrape(url)
    
    if ads_data:
        output_file = scraper.export_to_excel()
        print(f"\n" + "="*70)
        print("✅ SCRAPING COMPLETED SUCCESSFULLY!")
        print("="*70)
        print(f"📊 Total Ads Scraped: {len(ads_data)}")
        print(f"💾 Excel File: {output_file}")
        print(f"🖼️  Images Folder: {config.IMAGE_FOLDER}")
        print(f"\n📈 Clustering Data Collected:")
        print("   • Orientation (horizontal/vertical/square)")
        print("   • Dominant colors palette")
        print("   • Text density levels")
        print("   • Layout patterns")
        print("   • Brand indicators")
        print(f"\n👉 Next Step: Run cluster_analysis.py to generate visual clusters")
        print("="*70 + "\n")
    else:
        print("\n❌ No ads were scraped. Check scraper.log for details.\n")


if __name__ == "__main__":
    main()
