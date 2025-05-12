from serpapi import GoogleSearch
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import logging
logger = logging.getLogger(__name__)
class MaterialPriceService:
    def __init__(self):
        self.api_key = os.getenv('SERP_API_KEY')
        self.cache = {}
        self.cache_duration = timedelta(hours=24)
        # ZIP codes for our supported cities
        self.zip_codes = {
            'San Diego': '92101',
            'Los Angeles': '90001',
            'LA': '90001',
            'SD': '92101'
        }
    def get_material_prices(self, materials: List[str], location: str) -> Dict[str, Dict]:
        """Get prices for materials from Home Depot based on location"""
        prices = {}
        zip_code = self.zip_codes.get(location, '92101')
        for material in materials:
            cache_key = f"{material}_{zip_code}"
            cached_data = self._get_cached_price(cache_key)
            if cached_data:
                prices[material] = cached_data
                continue
            try:
                params = {
                    'engine': 'home_depot',
                    'q': material,
                    'lowe\'s_zip': zip_code,
                    'api_key': self.api_key,
                    'num': 5
                }
                search = GoogleSearch(params)
                results = search.get_dict()
                if 'products' in results and results['products']:
                    product_prices = []
                    for product in results['products'][:5]:
                        price_data = self._extract_price_data(product)
                        if price_data:
                            product_prices.append(price_data)
                    if product_prices:
                        price_info = self._aggregate_prices(product_prices)
                        price_info['source'] = 'Home Depot'
                        price_info['location'] = location
                        price_info['timestamp'] = datetime.now().isoformat()
                        self._cache_price(cache_key, price_info)
                        prices[material] = price_info
                    else:
                        prices[material] = {
                            'error': 'No valid prices found',
                            'source': 'Home Depot',
                            'location': location
                        }
                else:
                    prices[material] = {
                        'error': 'No products found',
                        'source': 'Home Depot',
                        'location': location
                    }
            except Exception as e:
                logger.error(f"Error fetching price for {material}: {str(e)}")
                prices[material] = {
                    'error': str(e),
                    'source': 'Home Depot',
                    'location': location
                }
        return prices
    def _extract_price_data(self, product: Dict) -> Optional[Dict]:
        """Extract price information from a product result"""
        try:
            price_info = product.get('price', {})
            current_price = None
            if isinstance(price_info, dict):
                current_price = price_info.get('current')
            elif isinstance(price_info, (int, float)):
                current_price = price_info
            elif isinstance(price_info, str):
                current_price = float(price_info.replace('$', '').replace(',', ''))
            if current_price is None:
                return None
            return {
                'price': float(current_price),
                'title': product.get('title', ''),
                'unit': product.get('unit', 'each'),
                'availability': product.get('availability', {}).get('status', 'unknown'),
                'rating': product.get('rating', 0),
                'reviews': product.get('reviews', 0)
            }
        except:
            return None
    def _aggregate_prices(self, product_prices: List[Dict]) -> Dict:
        """Aggregate multiple product prices into summary statistics"""
        prices = [p['price'] for p in product_prices]
        return {
            'min_price': min(prices),
            'max_price': max(prices),
            'avg_price': sum(prices) / len(prices),
            'median_price': sorted(prices)[len(prices) // 2],
            'sample_size': len(prices),
            'products': product_prices[:3]
        }
    def _get_cached_price(self, cache_key: str) -> Optional[Dict]:
        """Get price from cache if not expired"""
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data
        return None
    def _cache_price(self, cache_key: str, price_data: Dict):
        """Cache price data with timestamp"""
        self.cache[cache_key] = (price_data, datetime.now())
    def get_common_materials(self, project_type: str) -> List[str]:
        """Get common materials for a project type"""
        materials_map = {
            'kitchen_remodel': [
                'kitchen cabinets',
                'quartz countertops',
                'stainless steel sink',
                'kitchen faucet',
                'tile backsplash'
            ],
            'bathroom_remodel': [
                'bathroom vanity',
                'toilet',
                'shower door',
                'bathroom tile',
                'bathroom faucet'
            ],
            'flooring': [
                'hardwood flooring',
                'laminate flooring',
                'carpet',
                'tile flooring',
                'flooring underlayment'
            ],
            'roofing': [
                'asphalt shingles',
                'roofing felt',
                'roofing nails',
                'flashing',
                'ridge vent'
            ]
        }
        return materials_map.get(project_type, [])