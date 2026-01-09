"""
앱스토어 리뷰 데이터 상세 분석 스크립트
- 텍스트 분석
- 감정 분석 (기본)
- 키워드 추출
- 시각화
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import json
import re
from collections import Counter
import numpy as np

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
plt.rcParams['axes.unicode_minus'] = False

def load_reviews(country):
    """JSON 파일에서 리뷰 데이터 로드"""
    filename = f'reviews_{country}.json'
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
        return pd.DataFrame(reviews)
    except FileNotFoundError:
        print(f"[{country.upper()}] 파일을 찾을 수 없습니다: {filename}")
        return None

def clean_text(text):
    """텍스트 정제"""
    if pd.isna(text):
        return ""
    text = str(text)
    # 특수문자 제거 (공백으로 대체)
    text = re.sub(r'[^\w\s]', ' ', text)
    # 여러 공백을 하나로
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def analyze_text(df, country):
    """텍스트 분석"""
    if df is None or len(df) == 0:
        return
    
    print(f"\n=== [{country.upper()}] 텍스트 분석 ===")
    
    if 'review' in df.columns:
        reviews_text = df['review'].dropna().astype(str)
        
        # 리뷰 길이 분석
        review_lengths = reviews_text.apply(len)
        print(f"평균 리뷰 길이: {review_lengths.mean():.1f}자")
        print(f"최단 리뷰: {review_lengths.min()}자")
        print(f"최장 리뷰: {review_lengths.max()}자")
        
        # 긴 리뷰와 짧은 리뷰 샘플
        if len(reviews_text) > 0:
            longest_idx = review_lengths.idxmax()
            shortest_idx = review_lengths.idxmin()
            print(f"\n가장 긴 리뷰 샘플:")
            print(f"  {reviews_text.iloc[longest_idx][:200]}...")
            print(f"\n가장 짧은 리뷰 샘플:")
            print(f"  {reviews_text.iloc[shortest_idx]}")

def create_rating_distribution(df_us, df_kr):
    """평점 분포 시각화"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    if df_us is not None and 'rating' in df_us.columns:
        rating_counts_us = df_us['rating'].value_counts().sort_index()
        axes[0].bar(rating_counts_us.index, rating_counts_us.values, color='steelblue')
        axes[0].set_title('US - Rating Distribution', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Rating')
        axes[0].set_ylabel('Count')
        axes[0].set_xticks(range(1, 6))
        axes[0].grid(axis='y', alpha=0.3)
    
    if df_kr is not None and 'rating' in df_kr.columns:
        rating_counts_kr = df_kr['rating'].value_counts().sort_index()
        axes[1].bar(rating_counts_kr.index, rating_counts_kr.values, color='coral')
        axes[1].set_title('KR - Rating Distribution', fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Rating')
        axes[1].set_ylabel('Count')
        axes[1].set_xticks(range(1, 6))
        axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('rating_distribution.png', dpi=300, bbox_inches='tight')
    print("\n평점 분포 그래프 저장: rating_distribution.png")
    plt.close()

def create_timeline(df_us, df_kr):
    """리뷰 타임라인 시각화"""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    if df_us is not None and 'date' in df_us.columns:
        df_us['date'] = pd.to_datetime(df_us['date'])
        df_us_monthly = df_us.groupby(df_us['date'].dt.to_period('M')).size()
        axes[0].plot(df_us_monthly.index.astype(str), df_us_monthly.values, 
                    marker='o', linewidth=2, markersize=6, color='steelblue')
        axes[0].set_title('US - Reviews Over Time', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Date')
        axes[0].set_ylabel('Number of Reviews')
        axes[0].grid(alpha=0.3)
        axes[0].tick_params(axis='x', rotation=45)
    
    if df_kr is not None and 'date' in df_kr.columns:
        df_kr['date'] = pd.to_datetime(df_kr['date'])
        df_kr_monthly = df_kr.groupby(df_kr['date'].dt.to_period('M')).size()
        axes[1].plot(df_kr_monthly.index.astype(str), df_kr_monthly.values, 
                    marker='o', linewidth=2, markersize=6, color='coral')
        axes[1].set_title('KR - Reviews Over Time', fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Date')
        axes[1].set_ylabel('Number of Reviews')
        axes[1].grid(alpha=0.3)
        axes[1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('timeline.png', dpi=300, bbox_inches='tight')
    print("타임라인 그래프 저장: timeline.png")
    plt.close()

def create_wordcloud(df, country):
    """워드클라우드 생성"""
    if df is None or 'review' not in df.columns:
        return
    
    # 리뷰 텍스트 결합
    text = ' '.join(df['review'].dropna().astype(str))
    
    if not text or len(text.strip()) == 0:
        print(f"[{country.upper()}] 워드클라우드 생성 불가: 텍스트 없음")
        return
    
    # 한글인 경우 다른 폰트 필요
    if country == 'kr':
        try:
            wordcloud = WordCloud(
                width=800, 
                height=400,
                background_color='white',
                font_path='C:/Windows/Fonts/malgun.ttf',  # Windows 한글 폰트
                max_words=100
            ).generate(text)
        except:
            # 폰트를 찾을 수 없는 경우 기본 폰트 사용
            wordcloud = WordCloud(
                width=800, 
                height=400,
                background_color='white',
                max_words=100
            ).generate(text)
    else:
        wordcloud = WordCloud(
            width=800, 
            height=400,
            background_color='white',
            max_words=100
        ).generate(text)
    
    plt.figure(figsize=(12, 6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(f'{country.upper()} - Review Word Cloud', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(f'wordcloud_{country}.png', dpi=300, bbox_inches='tight')
    print(f"[{country.upper()}] 워드클라우드 저장: wordcloud_{country}.png")
    plt.close()

def compare_countries(df_us, df_kr):
    """국가별 비교 분석"""
    print("\n" + "=" * 50)
    print("국가별 비교 분석")
    print("=" * 50)
    
    comparison = {}
    
    if df_us is not None:
        comparison['US'] = {
            'count': len(df_us),
            'avg_rating': df_us['rating'].mean() if 'rating' in df_us.columns else None,
            'avg_review_length': df_us['review'].apply(len).mean() if 'review' in df_us.columns else None
        }
    
    if df_kr is not None:
        comparison['KR'] = {
            'count': len(df_kr),
            'avg_rating': df_kr['rating'].mean() if 'rating' in df_kr.columns else None,
            'avg_review_length': df_kr['review'].apply(len).mean() if 'review' in df_kr.columns else None
        }
    
    comparison_df = pd.DataFrame(comparison).T
    print(comparison_df)
    
    return comparison_df

def main():
    print("=" * 50)
    print("상세 분석 시작")
    print("=" * 50)
    
    # 데이터 로드
    df_us = load_reviews('us')
    df_kr = load_reviews('kr')
    
    if df_us is None and df_kr is None:
        print("분석할 데이터가 없습니다. 먼저 analyze_reviews.py를 실행하세요.")
        return
    
    # 텍스트 분석
    if df_us is not None:
        analyze_text(df_us, 'us')
        create_wordcloud(df_us, 'us')
    
    if df_kr is not None:
        analyze_text(df_kr, 'kr')
        create_wordcloud(df_kr, 'kr')
    
    # 시각화
    create_rating_distribution(df_us, df_kr)
    create_timeline(df_us, df_kr)
    
    # 국가별 비교
    compare_countries(df_us, df_kr)
    
    print("\n" + "=" * 50)
    print("상세 분석 완료!")
    print("=" * 50)

if __name__ == "__main__":
    main()






