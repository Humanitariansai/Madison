# smart_universal_competitor_analysis.py
"""
SMART Universal Competitor Finder
- Automatically detects YOUR industry
- Finds competitors for THAT specific industry
- Filters out junk phrases
"""

import pandas as pd
import matplotlib.pyplot as plt
import re
from collections import Counter

class SmartCompetitorAnalyzer:
    def __init__(self):
        # Expanded competitor database for ALL industries
        self.competitors_by_industry = {
            'ice_cream': [
                'baskin robbins', 'cold stone', 'coldstone', 'dairy queen', 'dq',
                'haagen-dazs', 'haagen dazs', 'ben & jerry', 'ben and jerry',
                'carvel', 'marble slab', 'friendlys', 'tcby', 'orange leaf'
            ],
            'coffee': [
                'starbucks', 'dunkin', 'dunkin donuts', 'peets', 'caribou',
                'tim hortons', 'coffee bean', 'dutch bros', 'blue bottle'
            ],
            'restaurant': [
                'olive garden', 'applebees', 'chilis', 'tgi fridays', 
                'red lobster', 'outback', 'cheesecake factory', 'pf changs'
            ],
            'fast_food': [
                'mcdonalds', 'burger king', 'wendys', 'taco bell', 'kfc',
                'subway', 'chipotle', 'five guys', 'chick-fil-a'
            ],
            'pizza': [
                'dominos', 'pizza hut', 'papa johns', 'little caesars',
                'marcos', 'jets pizza', 'blaze pizza', 'mod pizza'
            ],
            'hotel': [
                'marriott', 'hilton', 'holiday inn', 'hyatt', 'sheraton',
                'best western', 'hampton inn', 'comfort inn', 'ramada'
            ],
            'bakery': [
                'panera', 'crumbl', 'nothing bundt cakes', 'cake factory',
                'cheesecake factory', 'corner bakery', 'paris baguette'
            ]
        }
        
        # Better junk word filter
        self.junk_phrases = [
            'they taste', 'it tastes', 'any other', 'this place', 'that place',
            'most', 'others', 'anywhere', 'somewhere', 'everywhere',
            'the original', 'i expected', 'it was', 'they were',
            'we had', 'you get', 'nothing', 'everything', 'something'
        ]
    
    def detect_industry(self, df):
        """Smart industry detection from reviews"""
        sample_text = ' '.join(df['Review Text'].head(200).astype(str)).lower()
        
        industry_signals = {
            'ice_cream': ['ice cream', 'cone', 'scoop', 'flavor', 'sundae', 'frozen yogurt', 'gelato'],
            'coffee': ['coffee', 'latte', 'espresso', 'cappuccino', 'barista', 'brew'],
            'pizza': ['pizza', 'slice', 'pepperoni', 'crust', 'delivery'],
            'bakery': ['cake', 'pastry', 'bakery', 'cupcake', 'bread', 'croissant'],
            'restaurant': ['dinner', 'lunch', 'menu', 'waiter', 'meal', 'appetizer'],
            'fast_food': ['drive thru', 'fast food', 'burger', 'fries', 'combo'],
            'hotel': ['room', 'stay', 'hotel', 'check in', 'bed', 'suite']
        }
        
        # Score each industry
        scores = {}
        for industry, keywords in industry_signals.items():
            score = sum(sample_text.count(kw) for kw in keywords)
            scores[industry] = score
        
        # Get highest scoring industry
        best_industry = max(scores, key=scores.get)
        confidence = scores[best_industry]
        
        # Default to restaurant if low confidence
        if confidence < 5:
            best_industry = 'restaurant'
        
        return best_industry, confidence, scores
    
    def find_competitors(self, df, industry):
        """Find competitors for the detected industry"""
        all_reviews = ' '.join(df['Review Text'].astype(str)).lower()
        
        # Get competitor list for this industry
        known_competitors = self.competitors_by_industry.get(industry, [])
        
        # Method 1: Find known competitors
        found_competitors = {}
        for competitor in known_competitors:
            count = all_reviews.count(competitor)
            if count > 0:
                # Clean up name for display
                clean_name = competitor.replace('&', 'and').title()
                if competitor == 'dq':
                    clean_name = 'Dairy Queen'
                elif competitor == 'kfc':
                    clean_name = 'KFC'
                elif competitor == 'tcby':
                    clean_name = 'TCBY'
                
                found_competitors[clean_name] = count
        
        # Method 2: Find mentioned in comparisons (but filter better)
        comparison_patterns = [
            r'better than ([a-z\s&\']+?)(?:\.|,|!|$)',
            r'worse than ([a-z\s&\']+?)(?:\.|,|!|$)',
            r'compared to ([a-z\s&\']+?)(?:\.|,|!|$)',
            r'prefer (?:this|here) over ([a-z\s&\']+?)(?:\.|,|!|$)'
        ]
        
        mentioned = []
        for pattern in comparison_patterns:
            matches = re.findall(pattern, all_reviews)
            mentioned.extend(matches)
        
        # Clean and filter mentioned competitors
        for mention in mentioned:
            mention = mention.strip()
            # Skip if it's a junk phrase
            if mention in self.junk_phrases or len(mention) < 3:
                continue
            # Skip if it's too generic
            if all(word in ['the', 'a', 'an', 'this', 'that'] for word in mention.split()):
                continue
            
            # Add to found competitors
            clean_mention = mention.title()
            if clean_mention in found_competitors:
                found_competitors[clean_mention] += 1
            else:
                found_competitors[clean_mention] = 1
        
        return found_competitors
    
    def analyze(self, csv_path='data/raw/yelp_reviews.csv'):
        """Main analysis function"""
        print("🤖 SMART COMPETITOR ANALYSIS")
        print("=" * 50)
        
        # Load data
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(df)} reviews\n")
        
        # Detect industry
        print("🔍 DETECTING YOUR INDUSTRY...")
        industry, confidence, all_scores = self.detect_industry(df)
        print(f"✅ Detected: {industry.upper()} business (Confidence: {confidence})")
        
        # Show detection scores
        print("\n📊 Industry Detection Scores:")
        for ind, score in sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"   {ind}: {score} points")
        
        # Find competitors
        print(f"\n🏢 FINDING {industry.upper()} COMPETITORS...")
        competitors = self.find_competitors(df, industry)
        
        if competitors:
            # Sort by mentions
            sorted_competitors = dict(sorted(competitors.items(), 
                                           key=lambda x: x[1], 
                                           reverse=True))
            
            print(f"\n✅ Found {len(competitors)} competitors:")
            for comp, count in list(sorted_competitors.items())[:10]:
                print(f"   {comp}: {count} mentions")
            
            # Create visualization
            plt.figure(figsize=(12, 8))
            
            # Get top 10 for chart
            top_10 = dict(list(sorted_competitors.items())[:10])
            
            bars = plt.bar(top_10.keys(), top_10.values(), 
                          color='lightblue', edgecolor='darkblue', linewidth=2)
            
            # Highlight top 3
            colors = ['gold', 'silver', '#CD7F32']  # Gold, Silver, Bronze
            for i in range(min(3, len(bars))):
                bars[i].set_color(colors[i])
                bars[i].set_edgecolor('black')
            
            plt.xlabel('Competitor Name', fontsize=14)
            plt.ylabel('Times Mentioned', fontsize=14)
            plt.title(f'Top {industry.title()} Competitors Mentioned in Your Reviews', 
                     fontsize=16, fontweight='bold')
            plt.xticks(rotation=45, ha='right')
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{int(height)}', ha='center', va='bottom', fontsize=12)
            
            plt.tight_layout()
            plt.savefig(f'outputs/{industry}_competitors.png', dpi=300)
            plt.show()
            
            print(f"\n📊 Chart saved to: outputs/{industry}_competitors.png")
            
            # Insights
            print("\n💡 COMPETITIVE INSIGHTS:")
            top_competitor = list(sorted_competitors.keys())[0]
            print(f"   • Your main competitor: {top_competitor}")
            print(f"   • Industry category: {industry.title()}")
            print(f"   • Total unique competitors mentioned: {len(competitors)}")
            
        else:
            print("\n❌ No competitors found")
        
        return industry, competitors

# Run it
if __name__ == "__main__":
    analyzer = SmartCompetitorAnalyzer()
    industry, competitors = analyzer.analyze()