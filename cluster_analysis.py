"""
Visual Clustering Analysis for Meta Ads
Clusters ads based on visual similarity and provides detailed analysis
"""

import os
import pandas as pd
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import json

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. Some clustering features will be limited.")

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clustering.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AdClusterer:
    """Analyzes and clusters ads based on visual features"""
    
    def __init__(self, excel_file: str):
        """Initialize clusterer with scraped data"""
        self.excel_file = excel_file
        self.df = None
        self.clusters = {}
        self.cluster_analysis = {}
        
        # Create output folder
        os.makedirs(config.CLUSTER_OUTPUT_FOLDER, exist_ok=True)
    
    def load_data(self) -> bool:
        """Load scraped data from Excel"""
        try:
            logger.info(f"Loading data from {self.excel_file}")
            self.df = pd.read_excel(self.excel_file, sheet_name='Ads')
            logger.info(f"Loaded {len(self.df)} ads")
            return True
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def create_feature_vectors(self) -> Optional[np.ndarray]:
        """Create feature vectors for clustering"""
        try:
            if not SKLEARN_AVAILABLE:
                logger.warning("scikit-learn not available. Using fallback clustering.")
                return None
            
            features = []
            
            for _, row in self.df.iterrows():
                feature_vector = self._create_single_feature_vector(row)
                features.append(feature_vector)
            
            features_array = np.array(features)
            logger.info(f"Created feature vectors of shape {features_array.shape}")
            return features_array
            
        except Exception as e:
            logger.error(f"Error creating feature vectors: {e}")
            return None
    
    def _create_single_feature_vector(self, row) -> list:
        """Create feature vector for single ad"""
        features = []
        
        # Orientation encoding (0=horizontal, 1=vertical, 2=square, 3=unknown)
        orientation_map = {'Horizontal': 0, 'Vertical': 1, 'Square': 2, 'Unknown': 3}
        features.append(orientation_map.get(str(row.get('orientation', 'Unknown')), 3))
        
        # Text density encoding (0=minimal, 1=light, 2=moderate, 3=heavy)
        text_density_map = {'Minimal Text': 0, 'Light Text': 1, 'Moderate Text': 2, 'Heavy Text Overlay': 3, 'Unknown': -1}
        features.append(text_density_map.get(str(row.get('text_density', 'Unknown')), -1))
        
        # Layout pattern encoding
        layout_map = {'Product-focused': 0, 'Lifestyle Imagery': 1, 'Testimonial-style': 2, 'Offer/Discount-heavy': 3, 'General': 4, 'Unknown': 5}
        features.append(layout_map.get(str(row.get('layout_pattern', 'Unknown')), 5))
        
        # Ad format encoding
        format_map = {'Image': 0, 'Video': 1, 'Carousel': 2, 'Unknown': 3}
        features.append(format_map.get(str(row.get('ad_format', 'Unknown')), 3))
        
        # Image count
        try:
            features.append(int(row.get('image_count', 0)))
        except:
            features.append(0)
        
        # CTA type encoding
        cta = str(row.get('cta_type', 'N/A')).lower()
        if 'shop' in cta:
            features.append(0)
        elif 'learn' in cta:
            features.append(1)
        elif 'sign' in cta:
            features.append(2)
        elif 'download' in cta:
            features.append(3)
        else:
            features.append(4)
        
        # Ad copy length (normalized)
        try:
            copy_length = len(str(row.get('ad_copy', '')))
            features.append(min(copy_length / 500, 1.0))  # Normalize to 0-1
        except:
            features.append(0)
        
        return features
    
    def perform_clustering(self) -> bool:
        """Perform K-means clustering"""
        try:
            if not SKLEARN_AVAILABLE:
                logger.warning("scikit-learn not available. Using rule-based clustering.")
                return self._rule_based_clustering()
            
            logger.info("Performing K-means clustering...")
            
            features_array = self.create_feature_vectors()
            if features_array is None or features_array.shape[0] == 0:
                logger.warning("No features to cluster")
                return False
            
            # Standardize features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features_array)
            
            # Determine optimal number of clusters
            num_clusters = min(config.NUM_CLUSTERS, len(self.df))
            
            # Perform clustering
            kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(features_scaled)
            
            # Assign clusters
            self.df['cluster'] = cluster_labels
            
            logger.info(f"Clustering completed. Created {num_clusters} clusters.")
            return True
            
        except Exception as e:
            logger.error(f"Error during clustering: {e}")
            return False
    
    def _rule_based_clustering(self) -> bool:
        """Fallback rule-based clustering when sklearn is unavailable"""
        try:
            logger.info("Using rule-based clustering...")
            
            cluster_id = 0
            self.df['cluster'] = -1
            
            # Cluster 1: Product-focused image ads
            mask1 = (self.df['layout_pattern'] == 'Product-focused') & (self.df['ad_format'] == 'Image')
            self.df.loc[mask1, 'cluster'] = cluster_id
            cluster_id += 1
            
            # Cluster 2: Lifestyle imagery
            mask2 = (self.df['layout_pattern'] == 'Lifestyle Imagery')
            self.df.loc[mask2, 'cluster'] = cluster_id
            cluster_id += 1
            
            # Cluster 3: Offer/Discount heavy
            mask3 = (self.df['layout_pattern'] == 'Offer/Discount-heavy')
            self.df.loc[mask3, 'cluster'] = cluster_id
            cluster_id += 1
            
            # Cluster 4: Testimonials
            mask4 = (self.df['layout_pattern'] == 'Testimonial-style')
            self.df.loc[mask4, 'cluster'] = cluster_id
            cluster_id += 1
            
            # Cluster 5: Video and carousel ads
            mask5 = (self.df['ad_format'].isin(['Video', 'Carousel']))
            self.df.loc[mask5, 'cluster'] = cluster_id
            
            # Assign unassigned to closest cluster
            self.df.loc[self.df['cluster'] == -1, 'cluster'] = 0
            
            logger.info("Rule-based clustering completed.")
            return True
            
        except Exception as e:
            logger.error(f"Error in rule-based clustering: {e}")
            return False
    
    def analyze_clusters(self) -> Dict:
        """Generate detailed analysis for each cluster"""
        try:
            logger.info("Analyzing clusters...")
            
            cluster_analysis = {}
            
            for cluster_id in self.df['cluster'].unique():
                cluster_df = self.df[self.df['cluster'] == cluster_id]
                
                analysis = {
                    'cluster_id': int(cluster_id),
                    'ad_count': len(cluster_df),
                    'percentage': round(len(cluster_df) / len(self.df) * 100, 2),
                    'orientation': self._get_dominant_value(cluster_df, 'orientation'),
                    'dominant_colors': self._aggregate_colors(cluster_df),
                    'cta_style': self._get_dominant_value(cluster_df, 'cta_type'),
                    'layout_pattern': self._get_dominant_value(cluster_df, 'layout_pattern'),
                    'text_density': self._get_dominant_value(cluster_df, 'text_density'),
                    'ad_format': self._get_dominant_value(cluster_df, 'ad_format'),
                    'avg_image_count': round(cluster_df['image_count'].mean(), 2),
                    'brand_indicators': self._aggregate_brands(cluster_df),
                    'sample_ads': cluster_df[['ad_id', 'ad_copy', 'landing_page_url']].head(3).to_dict('records')
                }
                
                cluster_analysis[f"Cluster_{cluster_id}"] = analysis
            
            self.cluster_analysis = cluster_analysis
            logger.info(f"Cluster analysis completed for {len(cluster_analysis)} clusters")
            return cluster_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing clusters: {e}")
            return {}
    
    def _get_dominant_value(self, df, column) -> str:
        """Get most common value in a column"""
        try:
            if column not in df.columns or df[column].empty:
                return 'Unknown'
            value_counts = df[column].value_counts()
            if len(value_counts) > 0:
                return str(value_counts.idxmax())
            return 'Unknown'
        except:
            return 'Unknown'
    
    def _aggregate_colors(self, cluster_df) -> str:
        """Aggregate dominant colors from cluster"""
        try:
            all_colors = []
            for colors_str in cluster_df['dominant_colors']:
                if isinstance(colors_str, str) and colors_str != 'Unknown':
                    all_colors.extend(colors_str.split('|'))
            
            if all_colors:
                # Count color frequencies
                color_freq = {}
                for color in all_colors:
                    color_freq[color] = color_freq.get(color, 0) + 1
                
                # Return top 3 colors
                top_colors = sorted(color_freq.items(), key=lambda x: x[1], reverse=True)[:3]
                return ' | '.join([f"{color} ({freq})" for color, freq in top_colors])
            
            return 'Unknown'
        except:
            return 'Unknown'
    
    def _aggregate_brands(self, cluster_df) -> str:
        """Aggregate brand indicators"""
        try:
            all_brands = []
            for brand_str in cluster_df['brand_indicators']:
                if isinstance(brand_str, str) and brand_str != 'Generic' and brand_str != 'Unknown':
                    all_brands.extend(brand_str.split('|'))
            
            if all_brands:
                # Count brand frequencies
                brand_freq = {}
                for brand in all_brands:
                    brand = brand.strip()
                    brand_freq[brand] = brand_freq.get(brand, 0) + 1
                
                # Return top 5 brands
                top_brands = sorted(brand_freq.items(), key=lambda x: x[1], reverse=True)[:5]
                return ' | '.join([f"{brand} ({freq})" for brand, freq in top_brands])
            
            return 'Generic/Unknown'
        except:
            return 'Generic/Unknown'
    
    def export_analysis(self) -> str:
        """Export cluster analysis to Excel and JSON"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Export Excel with cluster assignments
            excel_path = os.path.join(config.CLUSTER_OUTPUT_FOLDER, f"clusters_detailed_{timestamp}.xlsx")
            self.df.to_excel(excel_path, sheet_name='Clustered_Ads', index=False)
            logger.info(f"Clustered data exported to: {excel_path}")
            
            # Export cluster summary
            summary_path = os.path.join(config.CLUSTER_OUTPUT_FOLDER, f"cluster_summary_{timestamp}.xlsx")
            
            summary_data = []
            for cluster_name, analysis in self.cluster_analysis.items():
                summary_data.append({
                    'Cluster': cluster_name,
                    'Ad Count': analysis['ad_count'],
                    'Percentage': f"{analysis['percentage']}%",
                    'Orientation': analysis['orientation'],
                    'Dominant Colors': analysis['dominant_colors'],
                    'CTA Style': analysis['cta_style'],
                    'Layout Pattern': analysis['layout_pattern'],
                    'Text Density': analysis['text_density'],
                    'Ad Format': analysis['ad_format'],
                    'Avg Images': analysis['avg_image_count'],
                    'Top Brands': analysis['brand_indicators']
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(summary_path, sheet_name='Cluster_Analysis', index=False)
            logger.info(f"Cluster summary exported to: {summary_path}")
            
            # Export JSON for detailed analysis
            json_path = os.path.join(config.CLUSTER_OUTPUT_FOLDER, f"cluster_analysis_{timestamp}.json")
            with open(json_path, 'w') as f:
                json.dump(self.cluster_analysis, f, indent=2)
            logger.info(f"Cluster analysis JSON exported to: {json_path}")
            
            return summary_path
            
        except Exception as e:
            logger.error(f"Error exporting analysis: {e}")
            return ""
    
    def generate_report(self) -> str:
        """Generate a human-readable cluster report"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = os.path.join(config.CLUSTER_OUTPUT_FOLDER, f"cluster_report_{timestamp}.txt")
            
            with open(report_path, 'w') as f:
                f.write("="*80 + "\n")
                f.write(" "*20 + "META ADS CLUSTERING ANALYSIS REPORT\n")
                f.write("="*80 + "\n\n")
                f.write(f"Report Generated: {datetime.now().isoformat()}\n")
                f.write(f"Total Ads Analyzed: {len(self.df)}\n")
                f.write(f"Total Clusters: {len(self.cluster_analysis)}\n")
                f.write("\n" + "="*80 + "\n")
                
                for cluster_name, analysis in self.cluster_analysis.items():
                    f.write(f"\n\n{cluster_name}\n")
                    f.write("-" * 80 + "\n\n")
                    
                    f.write(f"📊 CLUSTER STATISTICS\n")
                    f.write(f"  • Number of Ads: {analysis['ad_count']}\n")
                    f.write(f"  • Percentage of Dataset: {analysis['percentage']}%\n\n")
                    
                    f.write(f"🖼️  VISUAL CHARACTERISTICS\n")
                    f.write(f"  • Orientation: {analysis['orientation']}\n")
                    f.write(f"  • Dominant Color Palette: {analysis['dominant_colors']}\n")
                    f.write(f"  • Average Number of Images: {analysis['avg_image_count']}\n")
                    f.write(f"  • Ad Format: {analysis['ad_format']}\n\n")
                    
                    f.write(f"💬 CONTENT CHARACTERISTICS\n")
                    f.write(f"  • CTA Style: {analysis['cta_style']}\n")
                    f.write(f"  • Layout Pattern: {analysis['layout_pattern']}\n")
                    f.write(f"  • Text Density: {analysis['text_density']}\n\n")
                    
                    f.write(f"🏢 BRAND INFORMATION\n")
                    f.write(f"  • Top Brands: {analysis['brand_indicators']}\n\n")
                    
                    f.write(f"📌 SAMPLE ADS FROM THIS CLUSTER\n")
                    for i, sample in enumerate(analysis['sample_ads'], 1):
                        f.write(f"  Sample {i}:\n")
                        f.write(f"    - ID: {sample['ad_id']}\n")
                        f.write(f"    - Copy: {str(sample['ad_copy'])[:100]}...\n")
                        f.write(f"    - Landing URL: {sample['landing_page_url']}\n")
                    
                    f.write("\n")
            
            logger.info(f"Cluster report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return ""
    
    def run_full_analysis(self):
        """Run complete clustering analysis pipeline"""
        print("\n" + "="*80)
        print(" "*15 + "STARTING VISUAL CLUSTERING ANALYSIS")
        print("="*80 + "\n")
        
        # Load data
        if not self.load_data():
            print("❌ Failed to load data")
            return
        
        # Perform clustering
        if not self.perform_clustering():
            print("❌ Failed to perform clustering")
            return
        
        # Analyze clusters
        self.analyze_clusters()
        
        # Export results
        summary_file = self.export_analysis()
        report_file = self.generate_report()
        
        # Print results
        print("\n" + "="*80)
        print("✅ CLUSTERING ANALYSIS COMPLETED SUCCESSFULLY!")
        print("="*80)
        print(f"\n📊 Cluster Summary:")
        for cluster_name, analysis in self.cluster_analysis.items():
            print(f"\n  {cluster_name}")
            print(f"    - Ads: {analysis['ad_count']} ({analysis['percentage']}%)")
            print(f"    - Orientation: {analysis['orientation']}")
            print(f"    - Layout: {analysis['layout_pattern']}")
            print(f"    - Text Density: {analysis['text_density']}")
            print(f"    - CTA Style: {analysis['cta_style']}")
        
        print(f"\n📁 Output Files:")
        print(f"  ✓ Summary: {summary_file}")
        print(f"  ✓ Report: {report_file}")
        print(f"  ✓ Detailed Excel: {os.path.join(config.CLUSTER_OUTPUT_FOLDER, 'clusters_detailed_*.xlsx')}")
        print("\n" + "="*80 + "\n")


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) < 2:
        print("\nUsage: python cluster_analysis.py <excel_file>")
        print("\nExample: python cluster_analysis.py output/meta_ads_20240101_120000.xlsx")
        print("\nOr place your Excel file in the output folder and run: python cluster_analysis.py")
        
        # Try to find most recent Excel file
        output_folder = config.OUTPUT_FOLDER
        if os.path.exists(output_folder):
            excel_files = [f for f in os.listdir(output_folder) if f.endswith('.xlsx') and 'meta_ads_' in f]
            if excel_files:
                latest_file = sorted(excel_files)[-1]
                excel_path = os.path.join(output_folder, latest_file)
                print(f"\n🔄 Using latest file: {latest_file}\n")
                
                clusterer = AdClusterer(excel_path)
                clusterer.run_full_analysis()
                return
        
        return
    
    excel_file = sys.argv[1]
    
    if not os.path.exists(excel_file):
        print(f"❌ Error: File not found: {excel_file}")
        return
    
    clusterer = AdClusterer(excel_file)
    clusterer.run_full_analysis()


if __name__ == "__main__":
    main()
