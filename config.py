"""
Configuration settings for Meta Ads Library Scraper with Clustering
"""

# Browser settings
HEADLESS = True  # Set to False if you want to see the browser
WAIT_TIME = 10  # Seconds to wait for page elements to load
SCROLL_PAUSE_TIME = 2  # Seconds to pause between scrolls

# Data to scrape
FIELDS_TO_SCRAPE = [
    'ad_creative_images',
    'ad_copy',
    'cta_type',
    'ad_format',
    'date_range_start',
    'date_range_end',
    'landing_page_url'
]

# Output settings
OUTPUT_FOLDER = 'output'
OUTPUT_FORMAT = 'xlsx'  # or 'csv'
TIMESTAMP_OUTPUT = True  # Add timestamp to filename

# Scroll settings
MAX_SCROLL_ATTEMPTS = 50  # Maximum number of scroll attempts to load more ads
ADS_PER_LOAD = 10  # Approximate ads loaded per scroll

# Timeout settings
PAGE_LOAD_TIMEOUT = 30  # Seconds
ELEMENT_LOAD_TIMEOUT = 10  # Seconds

# Image processing settings
SAVE_IMAGES = True  # Download and save ad images
IMAGE_FOLDER = 'output/images'  # Folder to save images
MAX_IMAGE_SIZE = (800, 600)  # Max resolution for images
IMAGE_QUALITY = 85  # JPEG quality

# Clustering settings
CLUSTER_ANALYSIS = True  # Enable clustering analysis
NUM_CLUSTERS = 5  # Number of clusters for K-means
CLUSTER_OUTPUT_FOLDER = 'output/clusters'
CLUSTER_VISUALIZATION = True  # Create visualization images

# Vision AI settings (for advanced analysis)
USE_VISION_AI = False  # Set to True if you have Vision API key
VISION_API_KEY = None  # Add your API key here

# Similarity threshold (0-1)
SIMILARITY_THRESHOLD = 0.7  # Minimum similarity to be in same cluster
