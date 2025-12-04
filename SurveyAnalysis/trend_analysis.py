# trend_analysis.py
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('data/raw/yelp_reviews.csv')

# Create sentiment
df['sentiment'] = df['Rating'].apply(lambda x: 'positive' if x >= 4 else 'negative' if x <= 2 else 'neutral')

# Convert date
df['Date'] = pd.to_datetime(df['Date'])

# GROUP BY MONTH (cleaner than daily)
monthly = df.groupby([pd.Grouper(key='Date', freq='M'), 'sentiment']).size().unstack(fill_value=0)
percentages = monthly.div(monthly.sum(axis=1), axis=0) * 100

# Create CLEAN chart
plt.figure(figsize=(14, 6))
colors = {'positive': '#2ecc71', 'negative': '#e74c3c', 'neutral': '#f39c12'}

for sentiment in ['positive', 'negative', 'neutral']:
    if sentiment in percentages.columns:
        plt.plot(percentages.index, percentages[sentiment], 
                marker='o', linewidth=2.5, markersize=6,
                color=colors[sentiment], label=sentiment.capitalize())

plt.title('Yelp Review Sentiment Analysis - Sidney Dairy Barn', fontsize=16, fontweight='bold')
plt.xlabel('Month/Year', fontsize=12)
plt.ylabel('Percentage (%)', fontsize=12)
plt.legend(loc='best')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('outputs/sentiment_trends_clean.png', dpi=300)
plt.show()

# Print insights
print(f"\n📊 INSIGHTS:")
print(f"Average Positive: {percentages['positive'].mean():.1f}%")
print(f"Best Month: {percentages['positive'].idxmax().strftime('%B %Y')}")
print(f"Recent Trend: {percentages['positive'].iloc[-3:].mean():.1f}% positive (last 3 months)")