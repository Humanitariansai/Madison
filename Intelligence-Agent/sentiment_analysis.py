# Complete Brand Intelligence Dashboard with All Features
# Includes: All original visualizations + Enhanced drift analysis + GPT integration

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import re
from collections import Counter
from scipy import stats
import json
import requests
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# ============================================
# CONFIGURATION
# ============================================

# Your actual, legitimate OpenAI API key
# NOTE: The 401 Unauthorized error indicates an issue with your OpenAI account's billing or key validity.
OPENAI_API_KEY = 'sk-your_actual_key_here'
SPREADSHEET_ID = '1Uc8ZT586FafrP38p8grNuhP5_lz5wfExqfHrnlvdfQM'

# Colors for visualizations
COLORS = {
    'Apple': '#000000',
    'Samsung': '#1428A0',
    'Google': '#4285F4',
    'Microsoft': '#00BCF2'
}

SENTIMENT_COLORS = {
    'Positive': '#00C851',
    'Neutral': '#FFBB33',
    'Negative': '#FF3547'
}

# Drift detection thresholds
DRIFT_THRESHOLD = 0.10

# Helper function for wrapping long text strings
def wrap_text(text, width=70):
    """Wraps text string into lines of a maximum width."""
    if not isinstance(text, str):
        return text

    # Simple word wrap logic
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 > width:
            lines.append(current_line)
            current_line = word
        else:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
    lines.append(current_line)
    return '\n'.join(lines)


# ============================================
# GPT ANALYZER UTILITY CLASS
# ============================================

class GPTAnalyzer:
    """Utility class to manage OpenAI API calls."""

    def __init__(self, api_key: str):
        if api_key:
            self.api_key = api_key
            self.model = "gpt-4o-mini"
            self.enabled = True
            print("✅ GPT Analysis Enabled.")
        else:
            self.api_key = None
            self.enabled = False
            print("⚠️ GPT API key not provided. GPT analysis is disabled.")

    def analyze_cause(self, prompt: str) -> Optional[Dict]:
        """Calls the OpenAI API to get a structured JSON response."""
        if not self.enabled:
            return None

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a Senior Brand Intelligence Analyst. Your output MUST be a single, valid JSON object."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
            "max_tokens": 500
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()

            content_text = response.json()['choices'][0]['message']['content'].strip()
            return json.loads(content_text)

        except requests.exceptions.RequestException as e:
            print(f"❌ Error calling OpenAI API: {e}")
            return None
        except json.JSONDecodeError:
            print(f"❌ Error decoding JSON from OpenAI response. Content: {content_text[:100]}...")
            return None
        except Exception as e:
            print(f"❌ An unexpected error occurred during GPT analysis: {e}")
            return None

# ============================================
# ENHANCED DRIFT ANALYZER CLASS
# ============================================

class EnhancedDriftAnalyzer:
    """Advanced drift analyzer with proper root cause detection"""

    def __init__(self, df: pd.DataFrame, brand: str = 'Apple', openai_api_key: str = None):
        self.df = df[df['brand'] == brand].copy()
        self.brand = brand
        self.gpt_analyzer = GPTAnalyzer(openai_api_key)

        if not self.df.empty:
            self.df['date'] = pd.to_datetime(self.df['date'])
            self.df = self.df.sort_values('date')

        self.theme_patterns = {
            'Product Launch': r'\b(launch|announce|unveil|introduce|reveal|debut|release)\b',
            'Product Issues': r'\b(issue|problem|bug|defect|recall|failure|flaw|malfunction|battery|overheat|screen)\b',
            'Innovation': r'\b(AI|artificial intelligence|machine learning|innovation|breakthrough|patent|vision|quantum)\b',
            'Financial': r'\b(earnings|revenue|profit|loss|sales|quarter|stock|shares|market|invest)\b',
            'Legal/Regulatory': r'\b(lawsuit|legal|court|sue|litigation|regulatory|fine|penalty|monopoly)\b',
            'Privacy/Security': r'\b(privacy|data|security|breach|hack|leak|vulnerability|encryption)\b',
            'Competition': r'\b(samsung|google|microsoft|android|competitor|rival)\b',
            'Leadership': r'\b(CEO|executive|leadership|management|board|Tim Cook|Satya Nadella)\b',
            'Customer Issues': r'\b(complaint|dissatisf|anger|frustrat|disappoint|service|support)\b',
        }

    def detect_drift_periods(self, window_days: int = 7) -> List[Dict]:
        """Detect significant drift periods"""
        if self.df.empty or len(self.df) < window_days * 2:
            return []

        daily = self.df.groupby('date')['score'].agg(['mean', 'count']).reset_index()
        daily = daily.sort_values('date')
        drift_periods = []

        daily['current_ma'] = daily['mean'].rolling(window=window_days, min_periods=1).mean()
        daily['previous_ma'] = daily['mean'].shift(window_days).rolling(window=window_days, min_periods=1).mean()

        for i in range(window_days * 2, len(daily)):
            current = daily.iloc[i]['current_ma']
            previous = daily.iloc[i]['previous_ma']

            if pd.isna(current) or pd.isna(previous):
                continue

            drift = current - previous

            if abs(drift) > DRIFT_THRESHOLD:
                drift_start_date = daily.iloc[i - window_days + 1]['date']

                drift_periods.append({
                    'date': drift_start_date,
                    'drift': drift,
                    'drift_pct': (drift / previous * 100) if previous != 0 else 0,
                    'direction': 'up' if drift > 0 else 'down'
                })

        return drift_periods

    def analyze_drift_cause(self, drift_date: pd.Timestamp, window_days: int = 7) -> Dict:
        """Analyze root cause by comparing baseline to drift period"""
        drift_end = drift_date + pd.Timedelta(days=window_days - 1)
        drift_start = drift_date
        baseline_start = drift_start - pd.Timedelta(days=window_days)
        baseline_end = drift_start - pd.Timedelta(days=1)

        during_drift = self.df[(self.df['date'] >= drift_start) & (self.df['date'] <= drift_end)]
        baseline = self.df[(self.df['date'] >= baseline_start) & (self.df['date'] <= baseline_end)]

        if during_drift.empty:
            return {'error': 'No articles during drift period'}

        sentiment_shift = self._analyze_sentiment_shift(baseline, during_drift)
        theme_changes = self._analyze_theme_changes(baseline, during_drift)
        triggers = self._identify_triggers(during_drift)

        cause_analysis = self._determine_cause_gpt(sentiment_shift, theme_changes, triggers, window_days)

        if 'primary_cause' not in cause_analysis:
            cause_analysis = self._determine_cause_fallback(sentiment_shift, theme_changes)

        return {
            'primary_cause': cause_analysis['primary_cause'],
            'detailed_narrative': cause_analysis.get('detailed_narrative', cause_analysis['primary_cause']),
            'sentiment_shift': sentiment_shift,
            'theme_changes': theme_changes,
            'trigger_articles': triggers,
            'article_count': len(during_drift),
            'recommendations': self._generate_recommendations(cause_analysis['primary_cause'], sentiment_shift)
        }

    def _analyze_sentiment_shift(self, baseline: pd.DataFrame, drift: pd.DataFrame) -> Dict:
        baseline_sentiment = baseline['sentiment'].value_counts(normalize=True).mul(100).to_dict() if not baseline.empty else {}
        drift_sentiment = drift['sentiment'].value_counts(normalize=True).mul(100).to_dict()

        baseline_neg = baseline_sentiment.get('Negative', 0)
        drift_neg = drift_sentiment.get('Negative', 0)
        baseline_pos = baseline_sentiment.get('Positive', 0)
        drift_pos = drift_sentiment.get('Positive', 0)

        return {
            'negative_change': drift_neg - baseline_neg,
            'positive_change': drift_pos - baseline_pos,
            'drift_negative_pct': drift_neg,
            'drift_positive_pct': drift_pos
        }

    def _analyze_theme_changes(self, baseline: pd.DataFrame, drift: pd.DataFrame) -> List[Dict]:
        baseline_themes = self._extract_themes(baseline)
        drift_themes = self._extract_themes(drift)

        drift_negative = drift[drift['sentiment'] == 'Negative']
        drift_neg_themes = self._extract_themes(drift_negative) if not drift_negative.empty else {}

        changes = []
        all_themes = set(list(baseline_themes.keys()) + list(drift_themes.keys()))

        for theme in all_themes:
            base_rate = baseline_themes.get(theme, 0)
            drift_rate = drift_themes.get(theme, 0)
            change = drift_rate - base_rate

            if abs(change) > 3:
                changes.append({
                    'theme': theme,
                    'change': change,
                    'drift_rate': drift_rate,
                    'in_negative_coverage': drift_neg_themes.get(theme, 0)
                })

        return sorted(changes, key=lambda x: abs(x['change']), reverse=True)

    def _extract_themes(self, df: pd.DataFrame) -> Dict[str, float]:
        if df.empty:
            return {}

        counts = Counter()
        for _, row in df.iterrows():
            text = f"{row.get('title', '')} {row.get('description', '')}".lower()
            for theme, pattern in self.theme_patterns.items():
                if re.search(pattern, text, re.IGNORECASE):
                    counts[theme] += 1

        return {theme: (count/len(df)*100) for theme, count in counts.items()}

    def _identify_triggers(self, df: pd.DataFrame) -> List[Dict]:
        if df.empty:
            return []

        df = df.copy()
        df['impact'] = np.abs(df['score'] - 0.5) * 2

        triggers = []
        for _, row in df.nlargest(3, 'impact').iterrows():
            triggers.append({
                'title': row.get('title', 'Unknown')[:100],
                'sentiment': row.get('sentiment'),
                'score': round(row.get('score', 0.5), 3),
                'date': row.get('date').strftime('%Y-%m-%d') if pd.notna(row.get('date')) else 'Unknown'
            })

        return triggers

    def _create_gpt_prompt(self, sentiment: Dict, themes: List, triggers: List, window: int) -> str:
        """Constructs the prompt for the GPT model."""

        theme_str = "\n".join([
            f"- {t['theme']}: Change {t['change']:+.1f}pp (Drift Rate: {t['drift_rate']:.1f}%, Negative Coverage: {t['in_negative_coverage']:.1f}%)"
            for t in themes
        ])
        if not theme_str:
            theme_str = "No significant theme changes detected (all changes < 3pp)."

        trigger_str = "\n".join([
            f"- '{t['title']}' ({t['sentiment']} score: {t['score']} on {t['date']})"
            for t in triggers
        ])

        prompt = f"""
        Analyze the following Brand Intelligence data for {self.brand} to determine the primary root cause of a recent sentiment drift. The drift compares the last {window} days (Drift Period) against the previous {window} days (Baseline).

        Synthesize all three components (Sentiment, Theme Shifts, and Trigger Articles) into a single, cohesive narrative.

        ---
        1. SENTIMENT SHIFT (Drift Period vs. Baseline)
        - Negative Sentiment Change: {sentiment['negative_change']:+.1f} percentage points (pp)
        - Positive Sentiment Change: {sentiment['positive_change']:+.1f} pp
        - Drift Period Negative %: {sentiment['drift_negative_pct']:.1f}%
        - Drift Period Positive %: {sentiment['drift_positive_pct']:.1f}%

        ---
        2. THEME SHIFTS (Themes with >3% change in frequency)
        {theme_str}

        ---
        3. HIGH-IMPACT TRIGGER ARTICLES (Top 3 by score deviation from neutral)
        {trigger_str}

        ---
        ANALYST TASK:
        1. **PRIMARY CAUSE (One Sentence Summary):** State the single most likely primary cause in one succinct sentence.
        2. **DETAILED NARRATIVE (1-2 Paragraphs):** Explain *how* and *why* the drift occurred. Connect the sentiment change to the specific theme shifts and cite the most relevant trigger article(s) as evidence.

        OUTPUT FORMAT (MUST be JSON):
        {{
          "primary_cause": "A succinct, one-sentence summary of the root cause.",
          "detailed_narrative": "A 1-2 paragraph explanation and synthesis of the data."
        }}
        """
        return prompt

    def _determine_cause_gpt(self, sentiment: Dict, themes: List, triggers: List, window: int) -> Dict:
        """Determines root cause using GPT-4o for advanced synthesis."""
        prompt = self._create_gpt_prompt(sentiment, themes, triggers, window)

        gpt_result = self.gpt_analyzer.analyze_cause(prompt)

        if gpt_result:
            return gpt_result
        else:
            return self._determine_cause_fallback(sentiment, themes)

    def _determine_cause_fallback(self, sentiment: Dict, themes: List) -> Dict:
        """Fallback to the old rule-based system if GPT is disabled or fails."""

        if sentiment['negative_change'] > 15:
            for theme in themes:
                if theme['in_negative_coverage'] > 20:
                    return {
                        'primary_cause': f"CRITICAL: Surge in negative coverage due to {theme['theme']} (Fallback Rule)",
                        'detailed_narrative': f"The sentiment dropped sharply following a significant rise in articles concerning **{theme['theme']}** (up {theme['change']:+.1f}pp). This indicates a specific, damaging issue that requires immediate attention."
                    }
            return {
                'primary_cause': "Surge in generalized negative coverage (Fallback Rule)",
                'detailed_narrative': "A general increase in negative articles was detected, not strongly tied to a single major theme. Further manual review is required to pinpoint the cause."
            }

        if sentiment['positive_change'] > 15:
            if themes and themes[0]['change'] > 10 and themes[0]['theme'] == 'Product Launch':
                return {
                    'primary_cause': "Successful Product Launch coverage (Fallback Rule)",
                    'detailed_narrative': "The sentiment rose significantly, driven by successful press coverage of a recent **Product Launch** event."
                }
            return {
                'primary_cause': "Strong positive sentiment surge (Fallback Rule)",
                'detailed_narrative': "Positive sentiment saw a large increase, likely due to favorable news, but without a clear theme driver in the analysis."
            }

        return {
            'primary_cause': "Moderate sentiment fluctuation (Fallback Rule)",
            'detailed_narrative': "The drift magnitude was moderate. The underlying cause is likely a subtle shift in volume or a minor theme that did not cross the major rule thresholds."
        }

    def _generate_recommendations(self, cause: str, sentiment: Dict) -> List[str]:
        recs = []

        if "CRITICAL" in cause.upper() or "NEGATIVE" in cause.upper():
            recs.append("CRITICAL: Activate crisis management and prepare a comms response within 2 hours.")

        if "Product Issues" in cause:
            recs.append("HIGH: Product/Engineering team must issue a technical response or fix within 24 hours.")

        if "Product Launch" in cause:
            recs.append("ACTION: Amplify successful launch content through official channels.")

        if sentiment['drift_negative_pct'] > 30:
            recs.append("PRIORITY: Address top complaints from the identified trigger articles immediately.")

        if not recs:
             recs.append("INFO: Monitor the trend. No immediate crisis action required.")

        return recs[:3]

# ============================================
# DATA LOADING
# ============================================

print("Loading data from Google Sheets...")

try:
    from google.colab import auth
    auth.authenticate_user()
    import gspread
    from google.auth import default
    creds, _ = default()
    gc = gspread.authorize(creds)

    spreadsheet = gc.open_by_key(SPREADSHEET_ID)

    def load_sheet_data(sheet_name):
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            print(f"✅ Loaded {len(df)} rows from {sheet_name}")
            return df
        except Exception as e:
            print(f"⚠️ Could not load {sheet_name}: {e}")
            return pd.DataFrame()

    processed_links = load_sheet_data('Sheet1')
    drift_metrics = load_sheet_data('DriftMetrics')
    competitor_analysis = load_sheet_data('CompetitorAnalysis')

except ImportError:
    print("⚠️ Running outside Colab or missing libraries. Cannot load Google Sheets.")
    processed_links = pd.DataFrame()
    drift_metrics = pd.DataFrame()
    competitor_analysis = pd.DataFrame()
except Exception as e:
    print(f"⚠️ An error occurred during Colab/gspread setup: {e}")
    processed_links = pd.DataFrame()
    drift_metrics = pd.DataFrame()
    competitor_analysis = pd.DataFrame()


# ============================================
# DATA PREPROCESSING
# ============================================

if not processed_links.empty:
    processed_links['processedAt'] = pd.to_datetime(processed_links['processedAt'], errors='coerce')
    processed_links['date'] = processed_links['processedAt'].dt.date
    processed_links['score'] = pd.to_numeric(processed_links['score'], errors='coerce').fillna(0.5)
    processed_links['sentiment'] = processed_links['sentiment'].str.capitalize()
    processed_links['brand'] = processed_links['brand'].str.capitalize()
    processed_links = processed_links.sort_values('processedAt')

    def detect_source(url):
        if pd.isna(url) or url == 'N/A':
            return 'Other'
        url = str(url).lower()
        if 'apple.com' in url: return 'Apple Newsroom'
        elif 'reddit.com' in url: return 'Reddit'
        elif any(x in url for x in ['techcrunch', 'verge', 'arstechnica', '9to5mac', 'macrumors']):
            return 'Tech Media'
        elif any(x in url for x in ['bloomberg', 'wsj', 'ft.com', 'reuters', 'cnbc']):
            return 'Financial Media'
        elif 'news.google' in url: return 'Google News'
        else: return 'Other Sources'

    processed_links['source'] = processed_links['link'].apply(detect_source)

drift_analyzers = {}
drift_results = {}
for brand in ['Apple', 'Samsung', 'Google', 'Microsoft']:
    if not processed_links[processed_links['brand'] == brand].empty:
        analyzer = EnhancedDriftAnalyzer(processed_links, brand, OPENAI_API_KEY)
        drift_analyzers[brand] = analyzer

        drifts = analyzer.detect_drift_periods()
        if drifts:
            latest_drift = drifts[-1]
            analysis = analyzer.analyze_drift_cause(latest_drift['date'])
            drift_results[brand] = {
                'drifts': drifts,
                'latest_analysis': analysis,
                'latest_drift': latest_drift
            }

print("\n📊 Creating comprehensive visualizations...")

# ============================================
# VISUALIZATION 1: Apple Sentiment Timeline with Drift
# ============================================

# ... (Visualizations code is omitted for brevity but remains the same as before) ...
fig1 = go.Figure()
if not processed_links.empty:
    apple_data = processed_links[processed_links['brand'] == 'Apple'].copy()
    if not apple_data.empty:
        daily = apple_data.groupby('date').agg({'score': 'mean','title': 'count'}).reset_index()
        daily.columns = ['date', 'sentiment', 'volume']
        daily['date'] = pd.to_datetime(daily['date'])
        daily = daily.sort_values('date')
        daily['ma7'] = daily['sentiment'].rolling(7, min_periods=1).mean()
        fig1.add_trace(go.Scatter(x=daily['date'], y=daily['sentiment'], mode='lines', name='Daily Sentiment', line=dict(color=COLORS['Apple'], width=3), fill='tozeroy', fillcolor='rgba(0, 0, 0, 0.1)'))
        fig1.add_trace(go.Scatter(x=daily['date'], y=daily['ma7'], mode='lines', name='7-Day Average', line=dict(color='rgba(0, 0, 0, 0.5)', width=2, dash='dash')))
        if 'Apple' in drift_results:
            latest_drift = drift_results['Apple']['latest_drift']
            color = 'red' if latest_drift['direction'] == 'down' else 'green'
            sentiment_at_drift = daily[daily['date'] == latest_drift['date']]['sentiment']
            y_val = sentiment_at_drift.iloc[0] if not sentiment_at_drift.empty else 0.5
            fig1.add_trace(go.Scatter(x=[latest_drift['date']], y=[y_val], mode='markers', marker=dict(size=15, color=color, symbol='triangle-' + latest_drift['direction']), name=f"Latest Drift Start ({latest_drift['direction'].capitalize()})", hovertext=f"Drift Start: {latest_drift['date'].strftime('%Y-%m-%d')}<br>Drift: {latest_drift['drift']:+.3f}", showlegend=True))
        fig1.add_hline(y=0.72, line_dash="dot", line_color="green", annotation_text="Target: 0.72", annotation_position="right")
        fig1.add_hrect(y0=0.7, y1=1, fillcolor="green", opacity=0.05, annotation_text="Positive Zone", annotation_position="top left")
        fig1.add_hrect(y0=0, y1=0.3, fillcolor="red", opacity=0.05, annotation_text="Critical Zone", annotation_position="bottom left")
        fig1.update_layout(title="Apple Brand Sentiment Over Time with Drift Detection", xaxis_title="", yaxis_title="Sentiment Score", yaxis_range=[0, 1], height=500, template='plotly_white', hovermode='x unified')
fig1.show()

# VISUALIZATION 2: Brand Comparison
fig2 = go.Figure()
if not processed_links.empty:
    brand_sentiment = processed_links.groupby('brand').agg({'score': ['mean', 'std', 'count']}).round(3)
    brand_sentiment.columns = ['avg_sentiment', 'volatility', 'articles']
    main_brands = ['Apple', 'Samsung', 'Google', 'Microsoft']
    brand_sentiment = brand_sentiment[brand_sentiment.index.isin(main_brands)].sort_values('avg_sentiment', ascending=False)
    fig2.add_trace(go.Bar(x=brand_sentiment.index, y=brand_sentiment['avg_sentiment'], text=[f"{val:.3f}" for val in brand_sentiment['avg_sentiment']], textposition='outside', marker=dict(color=[COLORS.get(b, '#999') for b in brand_sentiment.index], line=dict(color='white', width=2)), error_y=dict(type='data', array=brand_sentiment['volatility'], visible=True, color='rgba(0,0,0,0.3)')))
    fig2.add_hline(y=0.72, line_dash="dash", line_color="gray", opacity=0.5, annotation_text="Target")
    fig2.update_layout(title="Brand Sentiment Comparison", xaxis_title="", yaxis_title="Average Sentiment Score", yaxis_range=[0, 1], height=500, template='plotly_white', showlegend=False)
    for i, (brand, row) in enumerate(brand_sentiment.iterrows()):
        fig2.add_annotation(x=i, y=0.02, text=f"{int(row['articles'])} articles", showarrow=False, font=dict(size=10, color='gray'))
fig2.show()

# VISUALIZATION 3: Sentiment Distribution
fig3 = make_subplots(rows=1, cols=4, subplot_titles=['Apple', 'Samsung', 'Google', 'Microsoft'], specs=[[{'type': 'pie'}, {'type': 'pie'}, {'type': 'pie'}, {'type': 'pie'}]])
if not processed_links.empty:
    brands = ['Apple', 'Samsung', 'Google', 'Microsoft']
    for i, brand in enumerate(brands, 1):
        brand_data = processed_links[processed_links['brand'] == brand]
        if not brand_data.empty:
            sentiment_counts = brand_data['sentiment'].value_counts()
            sentiment_order = ['Positive', 'Neutral', 'Negative']
            full_counts = pd.Series(0, index=sentiment_order)
            full_counts.update(sentiment_counts)
            fig3.add_trace(go.Pie(labels=full_counts.index, values=full_counts.values, marker=dict(colors=[SENTIMENT_COLORS.get(s, '#999') for s in full_counts.index], line=dict(color='white', width=2)), textinfo='percent', hole=0.4), row=1, col=i)
    fig3.update_layout(title="Sentiment Distribution by Brand", height=400, template='plotly_white', showlegend=False)
fig3.show()

# VISUALIZATION 4: Source Analysis
fig4 = go.Figure()
if not processed_links.empty:
    apple_sources = processed_links[processed_links['brand'] == 'Apple'].groupby('source').agg({'score': ['mean', 'count']}).round(3)
    apple_sources.columns = ['sentiment', 'articles']
    apple_sources = apple_sources[apple_sources['articles'] >= 3].sort_values('articles', ascending=True)
    fig4.add_trace(go.Bar(y=apple_sources.index, x=apple_sources['articles'], orientation='h', marker=dict(color=apple_sources['sentiment'], colorscale='RdYlGn', cmin=0.3, cmax=0.8, colorbar=dict(title="Sentiment", thickness=20, len=0.7), line=dict(color='white', width=1)), text=[f"{int(val)} articles<br>({apple_sources.loc[idx, 'sentiment']:.3f} sentiment)" for idx, val in zip(apple_sources.index, apple_sources['articles'])], textposition='outside'))
    fig4.update_layout(title="Apple News Sources - Volume & Sentiment", xaxis_title="Number of Articles", yaxis_title="", height=500, template='plotly_white', showlegend=False)
fig4.show()

# VISUALIZATION 5: Weekly Performance Heatmap
fig5 = go.Figure()
if not processed_links.empty:
    if 'week' not in processed_links.columns:
        processed_links['week'] = pd.to_datetime(processed_links['date']).dt.isocalendar().week.astype(int)
    heatmap_data = processed_links.pivot_table(values='score', index='brand', columns='week', aggfunc='mean').fillna(0.5)
    main_brands = ['Apple', 'Samsung', 'Google', 'Microsoft']
    heatmap_data = heatmap_data[heatmap_data.index.isin(main_brands)]
    fig5.add_trace(go.Heatmap(z=heatmap_data.values, x=[f"Week {w}" for w in heatmap_data.columns], y=heatmap_data.index, colorscale='RdYlGn', zmid=0.5, text=heatmap_data.values.round(2), texttemplate='%{text}', textfont={"size": 10}, colorbar=dict(title="Sentiment", thickness=20)))
    fig5.update_layout(title="Weekly Sentiment Heatmap", xaxis_title="", yaxis_title="", height=400, template='plotly_white')
fig5.show()
# ... (End of Visualizations code) ...

# ============================================
# KEY INSIGHTS SUMMARY (LINE-WRAPPED)
# ============================================

print("\n" + "="*80)
print(" " * 20 + "📊 KEY INSIGHTS WITH GPT-ENHANCED DRIFT ANALYSIS")
print("="*80)

if not processed_links.empty:
    apple_data = processed_links[processed_links['brand'] == 'Apple']

    if not apple_data.empty:
        current_sentiment = apple_data['score'].mean()
        total_articles = len(apple_data)
        positive_pct = (apple_data['sentiment'] == 'Positive').mean() * 100
        negative_pct = (apple_data['sentiment'] == 'Negative').mean() * 100

        print(f"\n🍎 APPLE PERFORMANCE SUMMARY")
        print("-" * 40)
        print(f"Overall Sentiment: {current_sentiment:.3f}")
        print(f"Target: 0.720 | Gap to Target: {current_sentiment - 0.72:+.3f}")
        print(f"Total Coverage: {total_articles} articles")
        print(f"Positive: {positive_pct:.1f}% | Negative: {negative_pct:.1f}%")

        # DRIFT ANALYSIS
        if 'Apple' in drift_results:
            print(f"\n📈 LATEST DRIFT ANALYSIS (GPT-Powered Synthesis)")
            print("-" * 40)

            latest = drift_results['Apple']['latest_drift']
            analysis = drift_results['Apple']['latest_analysis']

            # Check if GPT failed and is using the fallback
            if 'Fallback Rule' in analysis['primary_cause']:
                 print(f"⚠️ GPT FAILED: {analysis['primary_cause']} - The 401 error is causing this fallback.")
                 print("-" * 40)

            print(f"Drift Start Date: {latest['date'].strftime('%Y-%m-%d')} | Direction: {latest['direction'].upper()}")
            print(f"Magnitude: {latest['drift']:+.3f} ({latest['drift_pct']:+.1f}%)")

            print(f"\nROOT CAUSE: {wrap_text(analysis['primary_cause'])}") # WRAP
            print(f"--------------------------------------------------")
            print(f"DETAILED NARRATIVE:\n{wrap_text(analysis['detailed_narrative'], width=90)}") # WRAP with slightly wider width for narrative

            print(f"\nKey Metrics Behind Analysis:")
            print(f"  Negative Sentiment Change: {analysis['sentiment_shift']['negative_change']:+.1f}pp")
            if analysis['theme_changes']:
                print(f"  Top Theme Change: {analysis['theme_changes'][0]['theme']} ({analysis['theme_changes'][0]['change']:+.1f}pp)")

            print(f"\nTrigger Articles:")
            for i, article in enumerate(analysis['trigger_articles'][:2], 1):
                # WRAP Trigger Article Title
                wrapped_title = wrap_text(article['title'], width=65).replace('\n', '\n     ')
                print(f"  {i}. {wrapped_title}...")
                print(f"     Sentiment: {article['sentiment']} ({article['score']})")


        # COMPETITIVE POSITION (No changes, already concise)
        print(f"\n🏆 COMPETITIVE POSITION")
        print("-" * 40)
        brand_avg = processed_links.groupby('brand')['score'].mean().sort_values(ascending=False)
        main_brands = ['Apple', 'Samsung', 'Google', 'Microsoft']
        brand_avg = brand_avg[brand_avg.index.isin(main_brands)]
        for i, (brand, score) in enumerate(brand_avg.items(), 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            highlight = "<<<" if brand == 'Apple' else ""
            print(f"{emoji} #{i} {brand}: {score:.3f} {highlight}")
        print("-" * 40)

# ============================================
# DRIFT SUMMARY FOR ALL BRANDS (LINE-WRAPPED)
# ============================================

print("\n" + "="*80)
print(" " * 30 + "🔍 DRIFT SUMMARY REPORT")
print("="*80)

for brand in ['Apple', 'Samsung', 'Google', 'Microsoft']:
    if brand in drift_results:
        analysis = drift_results[brand]['latest_analysis']
        print(f"\n{brand.upper()}")
        print("-" * 40)
        print(f"Latest Drift Cause: {wrap_text(analysis['primary_cause'])}") # WRAP
        print(f"Drift Magnitude: {drift_results[brand]['latest_drift']['drift']:+.3f}")
        # WRAP Narrative Preview for summary
        preview = analysis['detailed_narrative'][:100]
        wrapped_preview = wrap_text(preview, width=75).replace('\n', '\n  ')
        print(f"Narrative Preview: {wrapped_preview}...")

print("\n" + "="*80)
print("Dashboard complete with all visualizations and enhanced drift analysis!")

if 'Apple' in drift_results and 'Fallback Rule' in drift_results['Apple']['latest_analysis']['primary_cause']:
    print("\n--- ❗ GPT TROUBLESHOOTING REQUIRED ---")
    print("The 401 Unauthorized error means your API key is not being accepted by OpenAI. Please check your OpenAI billing and account status.")
else:
    print("\n--- Dashboard run complete. ---")

print("="*80)