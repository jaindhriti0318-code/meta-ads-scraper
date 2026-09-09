"""
Brand Configuration for Meta Ads Library Scraper
Contains brand information and auto-generates Meta Ads Library URLs
"""

# Health & Wellness D2C Brands to Scrape
BRANDS = {
    'kapiva': {
        'name': 'Kapiva',
        'category': 'Health & Wellness',
        'facebook_page_id': '1234567890',  # Replace with actual Page ID
        'search_keywords': ['Kapiva', 'Kapiva Health'],
        'country': 'IN',
        'active_status': 'all',  # 'active', 'inactive', or 'all'
    },
    'oziva': {
        'name': 'OZiva',
        'category': 'Health & Wellness',
        'facebook_page_id': '1234567890',
        'search_keywords': ['OZiva', 'O Ziva'],
        'country': 'IN',
        'active_status': 'all',
    },
    'zandu': {
        'name': 'Zandu (Emami)',
        'category': 'Health & Wellness',
        'facebook_page_id': '1234567890',
        'search_keywords': ['Zandu', 'Emami'],
        'country': 'IN',
        'active_status': 'all',
    },
    'dabur': {
        'name': 'Dabur',
        'category': 'Health & Wellness',
        'facebook_page_id': '1234567890',
        'search_keywords': ['Dabur'],
        'country': 'IN',
        'active_status': 'all',
    },
    'himalaya': {
        'name': 'Himalaya Wellness',
        'category': 'Health & Wellness',
        'facebook_page_id': '1234567890',
        'search_keywords': ['Himalaya', 'Himalaya Wellness'],
        'country': 'IN',
        'active_status': 'all',
    },
    'patanjali': {
        'name': 'Patanjali',
        'category': 'Health & Wellness',
        'facebook_page_id': '1234567890',
        'search_keywords': ['Patanjali'],
        'country': 'IN',
        'active_status': 'all',
    },
    'wow_skin': {
        'name': 'Wow Skin Science',
        'category': 'Health & Wellness',
        'facebook_page_id': '1234567890',
        'search_keywords': ['Wow Skin Science', 'WOW'],
        'country': 'IN',
        'active_status': 'all',
    },
    'muscleblaze': {
        'name': 'MuscleBlaze',
        'category': 'Health & Wellness',
        'facebook_page_id': '1234567890',
        'search_keywords': ['MuscleBlaze', 'Muscle Blaze'],
        'country': 'IN',
        'active_status': 'all',
    },
    'healthkart': {
        'name': 'HealthKart',
        'category': 'Health & Wellness',
        'facebook_page_id': '1234567890',
        'search_keywords': ['HealthKart', 'Health Kart'],
        'country': 'IN',
        'active_status': 'all',
    },
    'mamaearth': {
        'name': 'Mamaearth',
        'category': 'Health & Wellness',
        'facebook_page_id': '1234567890',
        'search_keywords': ['Mamaearth', 'Mama Earth'],
        'country': 'IN',
        'active_status': 'all',
    }
}

# URL Templates for Meta Ads Library
ADS_LIBRARY_BASE_URL = "https://www.facebook.com/ads/library/"

URL_TEMPLATES = {
    'by_page': {
        'description': 'Search by Facebook Page ID',
        'template': (
            "https://www.facebook.com/ads/library/"
            "?active_status={active_status}"
            "&ad_type=all"
            "&country={country}"
            "&is_targeted_country=false"
            "&media_type=all"
            "&search_type=page"
            "&sort_data[direction]=desc"
            "&sort_data[mode]=total_impressions"
            "&view_all_page_id={page_id}"
        )
    },
    'by_advertiser': {
        'description': 'Search by Advertiser Name',
        'template': (
            "https://www.facebook.com/ads/library/"
            "?active_status={active_status}"
            "&ad_type=all"
            "&country={country}"
            "&is_targeted_country=false"
            "&media_type=all"
            "&search_type=advertiser"
            "&sort_data[direction]=desc"
            "&sort_data[mode]=total_impressions"
            "&search_query={brand_name}"
        )
    },
    'image_and_meme': {
        'description': 'Images and Memes Only',
        'template': (
            "https://www.facebook.com/ads/library/"
            "?active_status={active_status}"
            "&ad_type=all"
            "&country={country}"
            "&is_targeted_country=false"
            "&media_type=image_and_meme"
            "&search_type=page"
            "&sort_data[direction]=desc"
            "&sort_data[mode]=total_impressions"
            "&view_all_page_id={page_id}"
        )
    },
    'video': {
        'description': 'Videos Only',
        'template': (
            "https://www.facebook.com/ads/library/"
            "?active_status={active_status}"
            "&ad_type=all"
            "&country={country}"
            "&is_targeted_country=false"
            "&media_type=video"
            "&search_type=page"
            "&sort_data[direction]=desc"
            "&sort_data[mode]=total_impressions"
            "&view_all_page_id={page_id}"
        )
    },
    'carousel': {
        'description': 'Carousel Ads Only',
        'template': (
            "https://www.facebook.com/ads/library/"
            "?active_status={active_status}"
            "&ad_type=all"
            "&country={country}"
            "&is_targeted_country=false"
            "&media_type=carousel"
            "&search_type=page"
            "&sort_data[direction]=desc"
            "&sort_data[mode]=total_impressions"
            "&view_all_page_id={page_id}"
        )
    }
}


def generate_url(brand_key: str, url_type: str = 'by_advertiser', **kwargs) -> str:
    """
    Generate Meta Ads Library URL for a brand
    
    Args:
        brand_key: Key from BRANDS dict
        url_type: Type of URL ('by_page', 'by_advertiser', 'image_and_meme', 'video', 'carousel')
        **kwargs: Override values (active_status, country, etc.)
    
    Returns:
        Generated URL string
    """
    if brand_key not in BRANDS:
        raise ValueError(f"Brand '{brand_key}' not found in configuration")
    
    brand = BRANDS[brand_key]
    template = URL_TEMPLATES.get(url_type, URL_TEMPLATES['by_advertiser'])
    
    # Prepare parameters
    params = {
        'active_status': kwargs.get('active_status', brand['active_status']),
        'country': kwargs.get('country', brand['country']),
        'page_id': kwargs.get('page_id', brand['facebook_page_id']),
        'brand_name': kwargs.get('brand_name', brand['name']),
    }
    
    return template['template'].format(**params)


def generate_urls_for_brand(brand_key: str, all_types: bool = False) -> dict:
    """
    Generate all URL variants for a brand
    
    Args:
        brand_key: Key from BRANDS dict
        all_types: If True, generate URLs for all media types
    
    Returns:
        Dictionary of URL type -> URL
    """
    urls = {}
    
    if all_types:
        for url_type in URL_TEMPLATES.keys():
            urls[url_type] = generate_url(brand_key, url_type)
    else:
        # Default: by_advertiser (most reliable)
        urls['by_advertiser'] = generate_url(brand_key, 'by_advertiser')
    
    return urls


def get_all_brand_urls(all_types: bool = False) -> dict:
    """
    Get URLs for all configured brands
    
    Args:
        all_types: If True, generate all URL variants for each brand
    
    Returns:
        Dictionary of brand_key -> URLs
    """
    brand_urls = {}
    
    for brand_key in BRANDS.keys():
        brand_urls[brand_key] = generate_urls_for_brand(brand_key, all_types)
    
    return brand_urls


if __name__ == '__main__':
    # Example usage
    print("Sample URLs for Health & Wellness Brands:\n")
    
    for brand_key in list(BRANDS.keys())[:3]:
        print(f"\n{BRANDS[brand_key]['name']}:")
        urls = generate_urls_for_brand(brand_key, all_types=True)
        for url_type, url in urls.items():
            print(f"  {url_type}: {url[:100]}...")
