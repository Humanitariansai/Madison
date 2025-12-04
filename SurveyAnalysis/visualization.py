# visualization.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load Yelp reviews
df = pd.read_csv('data/raw/yelp_reviews.csv')

# Add sentiment (you know this!)
df['sentiment'] = df['Rating'].apply(lambda x: 'positive' if x >= 4 else 'negative' if x <= 2 else 'neutral')

# Fix dates
df['Date'] = pd.to_datetime(df['Date'])

#Create 4-box layout:
# Make 4 boxes (2x2)
fig, axes = plt.subplots(2, 2, figsize=(15, 12))
fig.suptitle('Sidney Dairy Barn - Complete Analysis Dashboard', fontsize=18, fontweight='bold')

#Add PIE CHART (Box 1):
# PIE CHART - Top Left Box
ax1 = axes[0, 0]
sentiment_counts = df['sentiment'].value_counts()
colors = ['#2ecc71', '#e74c3c', '#f39c12']  # green, red, orange
ax1.pie(sentiment_counts.values, labels=sentiment_counts.index, autopct='%1.1f%%', 
        colors=colors, startangle=90)
ax1.set_title('Overall Sentiment Distribution')

#Add BAR CHART (Box 2):
# BAR CHART - Top Right Box  
ax2 = axes[0, 1]
rating_counts = df['Rating'].value_counts().sort_index()
bars = ax2.bar(rating_counts.index, rating_counts.values, color='skyblue')
ax2.set_xlabel('Rating (Stars)')
ax2.set_ylabel('Number of Reviews')
ax2.set_title('Rating Distribution')

# Add numbers on bars
for bar in bars:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
            f'{int(height)}', ha='center')
    
#Add TIME CHART (Box 3):
# REVIEWS OVER TIME - Bottom Left Box
ax3 = axes[1, 0]
monthly_reviews = df.groupby(pd.Grouper(key='Date', freq='M')).size()
ax3.plot(monthly_reviews.index, monthly_reviews.values, 'b-o', linewidth=2)
ax3.set_title('Reviews Over Time')
ax3.set_ylabel('Number of Reviews')
ax3.tick_params(axis='x', rotation=45)
ax3.grid(True, alpha=0.3)

#Add WEEKDAY CHART (Box 4):
# WEEKDAY ANALYSIS - Bottom Right Box
ax4 = axes[1, 1]
df['Weekday'] = df['Date'].dt.day_name()
weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
weekday_counts = df['Weekday'].value_counts().reindex(weekday_order, fill_value=0)

bars = ax4.bar(range(7), weekday_counts.values)
# Color weekends differently
bars[5].set_color('orange')  # Saturday
bars[6].set_color('orange')  # Sunday
ax4.set_xticks(range(7))
ax4.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
ax4.set_title('Reviews by Day of Week')
ax4.set_ylabel('Number of Reviews')

#Save and show:
# Adjust layout and save
plt.tight_layout()
plt.savefig('outputs/complete_dashboard.png', dpi=300, bbox_inches='tight')
plt.show()

# Print summary
print("\n📊 DASHBOARD CREATED!")
print(f"Total Reviews: {len(df)}")
print(f"Date Range: {df['Date'].min().date()} to {df['Date'].max().date()}")
print(f"Average Rating: {df['Rating'].mean():.2f}/5")
print(f"Most Reviews on: {weekday_counts.idxmax()}")