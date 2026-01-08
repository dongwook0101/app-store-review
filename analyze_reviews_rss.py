"""
앱스토어 리뷰 데이터 수집 및 분석 스크립트 (iTunes RSS API 사용)
앱 ID: 1510564828
국가: 미국, 한국
"""

import json
import pandas as pd
import requests
from datetime import datetime
import os
import time

def fetch_reviews_rss(app_id, country='us', max_pages=10):
    """
    iTunes RSS API를 사용하여 리뷰 데이터를 수집합니다.
    
    Args:
        app_id: 앱 ID (숫자)
        country: 국가 코드 ('us' 또는 'kr')
        max_pages: 최대 페이지 수 (각 페이지당 50개 리뷰)
    """
    print(f"\n[{country.upper()}] 리뷰 수집 시작 (iTunes RSS API)...")
    
    all_reviews = []
    
    # 국가 코드 매핑 (iTunes RSS API용)
    country_code_map = {
        'us': 'us',
        'kr': 'kr',
        'ko': 'kr'  # 한국의 경우
    }
    cc = country_code_map.get(country.lower(), country.lower())
    
    # 언어 코드 매핑
    lang_map = {
        'us': 'en',
        'kr': 'ko'
    }
    lang = lang_map.get(country.lower(), 'en')
    
    try:
        for page in range(1, max_pages + 1):
            # iTunes RSS API URL
            url = f"https://itunes.apple.com/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json?l={lang}&cc={cc}"
            
            print(f"[{country.upper()}] 페이지 {page} 수집 중...")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                print(f"[{country.upper()}] 페이지 {page} 요청 실패: {response.status_code}")
                break
            
            try:
                data = response.json()
            except json.JSONDecodeError:
                print(f"[{country.upper()}] 페이지 {page} JSON 파싱 실패")
                break
            
            # RSS 피드에서 리뷰 추출
            if 'feed' not in data:
                break
            
            feed = data['feed']
            
            # entry가 없는 경우 중단
            if 'entry' not in feed:
                break
            
            entries = feed['entry']
            
            # 첫 번째 항목은 앱 정보일 수 있으므로 확인
            for entry in entries:
                # 앱 정보 항목은 건너뛰기 (im:name이 있으면 리뷰)
                if 'im:name' in entry:
                    continue
                
                # 리뷰 데이터 추출
                review_data = {}
                
                # 평점
                if 'im:rating' in entry:
                    review_data['rating'] = int(entry['im:rating']['label'])
                
                # 리뷰 제목
                if 'title' in entry:
                    review_data['title'] = entry['title']['label']
                
                # 리뷰 내용
                if 'content' in entry and 'label' in entry['content']:
                    review_data['review'] = entry['content']['label']
                elif 'content' in entry and isinstance(entry['content'], list) and len(entry['content']) > 0:
                    review_data['review'] = entry['content'][0].get('label', '')
                
                # 작성자
                if 'author' in entry and 'name' in entry['author']:
                    review_data['author'] = entry['author']['name']['label']
                
                # 날짜
                if 'updated' in entry:
                    review_data['date'] = entry['updated']['label']
                elif 'im:version' in entry:
                    # 대체 날짜 필드
                    pass
                
                # 버전
                if 'im:version' in entry:
                    review_data['version'] = entry['im:version']['label']
                
                if review_data:
                    all_reviews.append(review_data)
            
            # 리뷰가 더 없으면 중단
            if len(entries) < 50:  # 마지막 페이지
                break
            
            # API 호출 간 딜레이
            time.sleep(1)
        
        if not all_reviews:
            print(f"[{country.upper()}] 리뷰를 찾을 수 없습니다.")
            return None
        
        print(f"[{country.upper()}] {len(all_reviews)}개의 리뷰 수집 완료")
        return all_reviews
    
    except Exception as e:
        print(f"[{country.upper()}] 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def save_reviews(reviews, country):
    """리뷰 데이터를 JSON 파일로 저장"""
    if reviews is None:
        return
    
    filename = f'reviews_{country}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    print(f"[{country.upper()}] 리뷰 데이터 저장 완료: {filename}")

def analyze_reviews(reviews, country):
    """
    리뷰 데이터를 분석하고 DataFrame으로 변환합니다.
    """
    if reviews is None or len(reviews) == 0:
        return None
    
    # 리뷰 데이터를 DataFrame으로 변환
    df = pd.DataFrame(reviews)
    
    # 날짜 변환
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # 국가 정보 추가
    df['country'] = country.upper()
    
    return df

def basic_statistics(df, country):
    """기본 통계 정보 출력"""
    if df is None or len(df) == 0:
        print(f"\n[{country.upper()}] 분석할 데이터가 없습니다.")
        return
    
    print(f"\n=== [{country.upper()}] 기본 통계 ===")
    print(f"총 리뷰 수: {len(df)}")
    
    if 'rating' in df.columns:
        print(f"평균 평점: {df['rating'].mean():.2f}")
        print(f"평점 분포:")
        print(df['rating'].value_counts().sort_index())
    
    if 'date' in df.columns:
        valid_dates = df['date'].dropna()
        if len(valid_dates) > 0:
            print(f"\n리뷰 기간:")
            print(f"  최초: {valid_dates.min()}")
            print(f"  최신: {valid_dates.max()}")

def save_to_excel(df_us, df_kr):
    """미국과 한국 리뷰를 Excel 파일로 저장"""
    filename = 'reviews_analysis.xlsx'
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        if df_us is not None and len(df_us) > 0:
            df_us.to_excel(writer, sheet_name='US_Reviews', index=False)
        
        if df_kr is not None and len(df_kr) > 0:
            df_kr.to_excel(writer, sheet_name='KR_Reviews', index=False)
        
        # 통합 데이터
        if df_us is not None and df_kr is not None:
            df_combined = pd.concat([df_us, df_kr], ignore_index=True)
            df_combined.to_excel(writer, sheet_name='All_Reviews', index=False)
    
    print(f"\nExcel 파일 저장 완료: {filename}")

def main():
    # 작업 디렉토리를 스크립트 위치로 변경
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    app_id = 1510564828
    
    print("=" * 50)
    print("앱스토어 리뷰 데이터 수집 및 분석 (iTunes RSS API)")
    print(f"앱 ID: {app_id}")
    print(f"앱 이름: Murmur - Voice Diary")
    print("=" * 50)
    
    # 미국 리뷰 수집
    reviews_us = fetch_reviews_rss(app_id, 'us', max_pages=10)
    if reviews_us:
        save_reviews(reviews_us, 'us')
        df_us = analyze_reviews(reviews_us, 'us')
        basic_statistics(df_us, 'us')
    else:
        df_us = None
    
    # 한국 리뷰 수집
    reviews_kr = fetch_reviews_rss(app_id, 'kr', max_pages=10)
    if reviews_kr:
        save_reviews(reviews_kr, 'kr')
        df_kr = analyze_reviews(reviews_kr, 'kr')
        basic_statistics(df_kr, 'kr')
    else:
        df_kr = None
    
    # Excel 파일로 저장
    if df_us is not None or df_kr is not None:
        save_to_excel(df_us, df_kr)
    
    print("\n" + "=" * 50)
    print("분석 완료!")
    print("=" * 50)

if __name__ == "__main__":
    main()





