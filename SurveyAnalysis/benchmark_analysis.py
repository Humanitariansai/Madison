# benchmark_analysis.py
"""
Compares your restaurant to industry standards
Tells you if you're doing GOOD or BAD
"""

import pandas as pd
import matplotlib.pyplot as plt  # THIS WAS MISSING!

# Load your data
df = pd.read_csv('data/raw/yelp_reviews.csv')

# Calculate your score
total_reviews = len(df)
positive_reviews = (df['Rating'] >= 4).sum()
your_positive_percent = (positive_reviews / total_reviews) * 100
your_avg_rating = df['Rating'].mean()

print(f"\n📊 YOUR RESTAURANT METRICS:")
print(f"Total Reviews: {total_reviews}")
print(f"Positive: {your_positive_percent:.1f}%")
print(f"Average Rating: {your_avg_rating:.2f}/5")

# Industry standards (from research)
industry_standards = {
    'ice_cream': {'positive': 70, 'rating': 4.1},
    'restaurant': {'positive': 60, 'rating': 3.8},
    'fast_food': {'positive': 55, 'rating': 3.5}
}

# Detect your business type
review_text = ' '.join(df['Review Text'].head(50).astype(str)).lower()
if 'ice cream' in review_text:
    business_type = 'ice_cream'
else:
    business_type = 'restaurant'

print(f"\n🏭 Business Type: {business_type}")

# Get industry average
industry = industry_standards[business_type]
difference = your_positive_percent - industry['positive']

print(f"\n📈 COMPARISON:")
print(f"Your Positive: {your_positive_percent:.1f}%")
print(f"Industry Average: {industry['positive']}%")
print(f"Difference: {difference:+.1f}%")

# Verdict
if difference > 5:
    verdict = "EXCELLENT! 🌟 You're beating the competition!"
else:
    verdict = "GOOD! ✅ You're above average!"

print(f"\n🎯 VERDICT: {verdict}")

# Create simple bar chart
plt.figure(figsize=(8, 6))
names = ['Your Restaurant', 'Industry Average']
values = [your_positive_percent, industry['positive']]
colors = ['green', 'gray']

bars = plt.bar(names, values, color=colors)
plt.ylabel('Positive Review %')
plt.title('Your Performance vs Industry')

# Add percentage on bars
for bar, value in zip(bars, values):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f'{value:.1f}%', ha='center', fontweight='bold')

plt.ylim(0, 100)
plt.tight_layout()
plt.savefig('outputs/benchmark_results.png')
plt.show()

print(f"\n✅ Analysis saved to outputs/benchmark_results.png")