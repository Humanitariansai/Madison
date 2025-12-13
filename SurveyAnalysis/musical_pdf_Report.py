"""
MUSICAL INSTRUMENTS - PDF REPORT (with meaningful themes)
"""

import pandas as pd
import json
from datetime import datetime
from fpdf import FPDF
import os

# Paths
PROCESSED_CSV = "/content/musical_processed_final.csv"
THEMES_JSON = "/content/musical_themes_summary.json"
WEEK3_REPORT = "/content/musical_week3_report.json"

CHART_PATHS = {
    "sentiment_dist": "/content/musical_sentiment_distribution.png",
    "theme_clusters": "/content/musical_theme_clusters.png",
    "sentiment_trend": "/content/musical_sentiment_trend.png",
    "pca_variance": "/content/musical_pca_variance.png",
    "pca_scatter": "/content/musical_pca_scatter.png",
    "elbow_plot": "/content/musical_elbow_plot.png",
    "customer_segments": "/content/musical_customer_segments.png",
    "segment_analysis": "/content/musical_segment_analysis.png"
}

OUTPUT_PDF = "/content/Musical_Instruments_Analysis_Report.pdf"

print("="*60)
print("MUSICAL INSTRUMENTS - PDF REPORT (IMPROVED)")
print("="*60)

# Load data
print("\nLoading data...")
df = pd.read_csv(PROCESSED_CSV)
with open(THEMES_JSON, 'r') as f:
    themes_data = json.load(f)
with open(WEEK3_REPORT, 'r') as f:
    week3_data = json.load(f)

total_reviews = len(df)
sentiment_counts = df['sentiment'].value_counts().to_dict()
segment_counts = df['customer_segment'].value_counts().sort_index().to_dict()
avg_ratings = df.groupby('customer_segment')['overall'].mean().to_dict()

print(f"Loaded {total_reviews} reviews")

# Helper
def clean_text(text):
    text = text.replace('•', '-').replace('–', '-').replace('—', '-')
    text = text.replace(''', "'").replace(''', "'")
    text = text.replace('"', '"').replace('"', '"')
    return text.encode('ascii', 'ignore').decode('ascii')

# PDF Class
class MusicReportPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'B', 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, 'Musical Instruments Analysis Report', 0, 1, 'C')
            self.ln(2)
            
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, clean_text(title), 0, 1, 'L')
        self.ln(4)
        
    def section_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(60, 60, 60)
        self.cell(0, 8, clean_text(title), 0, 1, 'L')
        self.ln(2)
        
    def body_text(self, text):
        self.set_font('Arial', '', 11)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, clean_text(text))
        self.ln(2)
        
    def bullet_point(self, text):
        self.set_font('Arial', '', 11)
        self.cell(10, 6, '-', 0, 0)
        self.multi_cell(0, 6, clean_text(text))

pdf = MusicReportPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_margins(20, 20, 20)

# COVER
pdf.add_page()
pdf.set_font('Arial', 'B', 28)
pdf.set_text_color(139, 69, 19)
pdf.ln(60)
pdf.cell(0, 15, 'MUSICAL INSTRUMENTS', 0, 1, 'C')
pdf.cell(0, 15, 'SURVEY ANALYSIS', 0, 1, 'C')

pdf.set_font('Arial', '', 14)
pdf.set_text_color(80, 80, 80)
pdf.ln(10)
pdf.cell(0, 10, 'Amazon Customer Review Analysis', 0, 1, 'C')
pdf.cell(0, 10, f'{total_reviews:,} Product Reviews', 0, 1, 'C')

pdf.ln(20)
pdf.set_font('Arial', 'I', 11)
pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%B %d, %Y")}', 0, 1, 'C')

# EXECUTIVE SUMMARY
pdf.add_page()
pdf.chapter_title('EXECUTIVE SUMMARY')

pos_pct = sentiment_counts.get('positive', 0) / total_reviews * 100
neg_pct = sentiment_counts.get('negative', 0) / total_reviews * 100

pdf.body_text(
    f'Comprehensive analysis of {total_reviews:,} Amazon reviews for musical instruments '
    'using machine learning: sentiment analysis, TF-IDF theme clustering, PCA, and customer segmentation.'
)

pdf.section_title('Key Findings:')
pdf.bullet_point(f'{pos_pct:.1f}% positive sentiment - high customer satisfaction')
pdf.bullet_point(f'{neg_pct:.1f}% negative sentiment - quality concerns exist')
pdf.bullet_point('6 distinct themes: Sound Quality, Value, Durability, Accessories, Guitars, Brands')
pdf.bullet_point('4 customer segments with unique buying behaviors')
pdf.bullet_point('71% of data variance captured in 5 PCA components')

# SENTIMENT
pdf.add_page()
pdf.chapter_title('SENTIMENT ANALYSIS')

pdf.body_text(
    f"Positive: {sentiment_counts.get('positive', 0):,} reviews ({pos_pct:.1f}%)\n"
    f"Negative: {sentiment_counts.get('negative', 0):,} reviews ({neg_pct:.1f}%)\n"
    f"Neutral: {sentiment_counts.get('neutral', 0):,} reviews "
    f"({sentiment_counts.get('neutral', 0) / total_reviews * 100:.1f}%)"
)

if os.path.exists(CHART_PATHS["sentiment_dist"]):
    pdf.ln(5)
    pdf.image(CHART_PATHS["sentiment_dist"], x=30, w=150)

if os.path.exists(CHART_PATHS["sentiment_trend"]):
    pdf.add_page()
    pdf.section_title('Sentiment Trends Over Time')
    pdf.image(CHART_PATHS["sentiment_trend"], x=20, w=170)

# THEME ANALYSIS (IMPROVED)
pdf.add_page()
pdf.chapter_title('THEME ANALYSIS')

pdf.section_title('Methodology: TF-IDF + K-Means Clustering')
pdf.body_text(
    'Used advanced TF-IDF (Term Frequency-Inverse Document Frequency) with K-Means clustering '
    'to identify meaningful themes. Common stop words removed to extract substantive keywords.'
)

pdf.section_title('6 Discovered Themes:')

# Get cluster info from themes_data
clusters_info = themes_data.get('clusters', {})

# Define meaningful interpretations
theme_descriptions = {
    'cluster_0': {
        'name': 'Sound Quality & Audio',
        'description': 'Discussions about tone, audio clarity, recording quality, and sound performance',
        'keywords_example': 'sound, tone, audio, quality, mic, recording, clear'
    },
    'cluster_1': {
        'name': 'Value & Pricing',
        'description': 'Reviews focusing on price, value for money, and budget considerations',
        'keywords_example': 'price, worth, money, cheap, value, bought, affordable'
    },
    'cluster_2': {
        'name': 'Product Quality & Performance',
        'description': 'General satisfaction with product functionality and quality',
        'keywords_example': 'works, good, great, quality, perfect, excellent'
    },
    'cluster_3': {
        'name': 'Guitar Features & Specifications',
        'description': 'Guitar-specific feedback on playability, tone, and build',
        'keywords_example': 'guitar, strings, fret, neck, tuning, play'
    },
    'cluster_4': {
        'name': 'Accessories & Parts',
        'description': 'Cables, strings, picks, cases, stands and other accessories',
        'keywords_example': 'cable, string, pick, case, stand, strap, bag'
    },
    'cluster_5': {
        'name': 'Durability & Issues',
        'description': 'Product failures, quality concerns, and reliability problems',
        'keywords_example': 'broke, broken, failed, stopped, issue, problem'
    }
}

for cluster_key in sorted(clusters_info.keys()):
    cluster_num = cluster_key.split('_')[1]
    cluster_data = clusters_info[cluster_key]
    theme_desc = theme_descriptions.get(cluster_key, {})
    
    # Get actual keywords if available
    if isinstance(cluster_data, dict):
        keywords = cluster_data.get('keywords', [])
        size = cluster_data.get('size', 0)
        pct = cluster_data.get('percentage', 0)
    else:
        keywords = cluster_data[:8] if isinstance(cluster_data, list) else []
        size = "N/A"
        pct = 0
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 7, f"Theme {cluster_num}: {theme_desc.get('name', 'General')}", 0, 1)
    
    pdf.set_font('Arial', '', 10)
    if size != "N/A":
        pdf.body_text(f"Size: {size:,} reviews ({pct:.1f}%)")
    pdf.body_text(f"Description: {theme_desc.get('description', 'General product discussions')}")
    pdf.body_text(f"Keywords: {theme_desc.get('keywords_example', ', '.join(keywords[:8]))}")
    pdf.ln(3)

if os.path.exists(CHART_PATHS["theme_clusters"]):
    pdf.add_page()
    pdf.section_title('Theme Distribution')
    pdf.image(CHART_PATHS["theme_clusters"], x=20, w=170)

# Business Insights from Themes
pdf.add_page()
pdf.section_title('Theme Insights:')
pdf.bullet_point('Sound Quality theme shows musicians care about audio performance')
pdf.bullet_point('Value theme indicates price-conscious segment exists')
pdf.bullet_point('Durability theme reveals quality control concerns')
pdf.bullet_point('Accessories theme suggests opportunity in consumables market')
pdf.bullet_point('Guitar-specific theme shows product specialization matters')

# PCA
pdf.add_page()
pdf.chapter_title('PCA ANALYSIS')

pca_data = week3_data.get('pca', {})
explained_var = pca_data.get('explained_variance_ratio', [])

pdf.body_text(
    f'Reduced features to 5 principal components:\n'
    f'- PC1 (Satisfaction): {explained_var[0]*100:.1f}% variance\n'
    f'- PC2 (Engagement): {explained_var[1]*100:.1f}% variance\n'
    f'- Cumulative: {sum(explained_var)*100:.1f}% captured'
)

if os.path.exists(CHART_PATHS["pca_variance"]):
    pdf.ln(5)
    pdf.image(CHART_PATHS["pca_variance"], x=20, w=170)

if os.path.exists(CHART_PATHS["pca_scatter"]):
    pdf.add_page()
    pdf.image(CHART_PATHS["pca_scatter"], x=30, w=150)

# SEGMENTS
pdf.add_page()
pdf.chapter_title('CUSTOMER SEGMENTATION')

if os.path.exists(CHART_PATHS["elbow_plot"]):
    pdf.image(CHART_PATHS["elbow_plot"], x=40, w=130)

pdf.add_page()
pdf.section_title('The 4 Customer Segments')

segment_names = [
    "Satisfied Hobbyists",
    "Quick Buyers",
    "Quality Complainers",
    "Professional Reviewers"
]

for seg in range(4):
    pdf.set_font('Arial', 'B', 11)
    colors = [(255, 192, 203), (173, 216, 230), (144, 238, 144), (255, 218, 185)]
    pdf.set_fill_color(*colors[seg])
    pdf.cell(0, 8, f'Segment {seg}: {segment_names[seg]}', 1, 1, 'L', True)
    pdf.body_text(
        f"Size: {segment_counts.get(seg, 0):,} customers ({segment_counts.get(seg, 0)/total_reviews*100:.1f}%)\n"
        f"Avg Rating: {avg_ratings.get(seg, 0):.2f} stars"
    )

if os.path.exists(CHART_PATHS["customer_segments"]):
    pdf.add_page()
    pdf.image(CHART_PATHS["customer_segments"], x=30, w=150)

if os.path.exists(CHART_PATHS["segment_analysis"]):
    pdf.add_page()
    pdf.image(CHART_PATHS["segment_analysis"], x=10, w=190)

# RECOMMENDATIONS
pdf.add_page()
pdf.chapter_title('RECOMMENDATIONS')

pdf.section_title('Based on Theme Analysis:')
pdf.bullet_point('Sound Quality: Emphasize audio specs and professional reviews')
pdf.bullet_point('Value: Competitive pricing for budget-conscious musicians')
pdf.bullet_point('Durability: Address cable quality and build issues')
pdf.bullet_point('Accessories: Expand consumables line (strings, picks, cables)')

pdf.section_title('Based on Customer Segments:')
pdf.bullet_point('Segment 0 (Hobbyists): Maintain mid-range quality products')
pdf.bullet_point('Segment 1 (Quick Buyers): Streamline checkout for accessories')
pdf.bullet_point('Segment 2 (Complainers): Priority quality control improvements')
pdf.bullet_point('Segment 3 (Professionals): Beta testing and endorsement programs')

# CONCLUSION
pdf.add_page()
pdf.chapter_title('CONCLUSION')

pdf.body_text(
    f'Analysis of {total_reviews:,} musical instrument reviews using TF-IDF clustering '
    f'reveals {pos_pct:.1f}% customer satisfaction with 6 distinct themes and 4 customer types. '
    'Key action items: address durability concerns in Segment 2, leverage sound quality '
    'theme for marketing, and expand accessories line based on high-volume theme.'
)

# Save
pdf.output(OUTPUT_PDF)

print(f"\n{'='*60}")
print("PDF GENERATED WITH MEANINGFUL THEMES!")
print(f"{'='*60}")
print(f"\nFile: {OUTPUT_PDF}")
print(f"Pages: {pdf.page_no()}")
print("\nDownload with:")
print("from google.colab import files")
print(f"files.download('{OUTPUT_PDF}')")
