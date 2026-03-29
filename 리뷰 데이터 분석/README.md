# 📱 앱스토어 리뷰 분석 도구

앱스토어의 리뷰 데이터를 수집하고 분석하는 웹 애플리케이션입니다. Streamlit을 사용하여 직관적인 인터페이스를 제공하며, 다국가 리뷰 데이터를 비교 분석할 수 있습니다.

## ✨ 주요 기능

- 🌍 **다국가 지원**: 29개 국가의 리뷰 데이터 수집 및 분석
- 📊 **실시간 분석**: iTunes RSS API를 통한 실시간 리뷰 수집
- 📈 **시각화**: 평점 분포, 년도별 추이, 국가별 비교 차트
- 📅 **년도별 분석**: 시계열 데이터 분석 및 트렌드 파악
- 📋 **데이터 내보내기**: Excel, CSV, JSON 형식으로 데이터 다운로드
- 🤖 **AI 분석 연동**: ChatGPT, Gemini 웹사이트 연동

## 🚀 빠른 시작

### 사전 요구사항

- Python 3.8 이상
- pip (Python 패키지 관리자)

### 설치 방법

1. **저장소 클론**
   ```bash
   git clone <your-repository-url>
   cd 리뷰-데이터-분석
   ```

2. **가상 환경 생성 (선택사항)**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **필요한 패키지 설치**
   ```bash
   pip install -r requirements.txt
   ```

### 실행 방법

```bash
streamlit run app.py
```

브라우저가 자동으로 열리며, `http://localhost:8501`에서 애플리케이션에 접근할 수 있습니다.

## 📖 사용 방법

1. **앱 ID 입력**
   - 앱스토어에서 앱 페이지를 열고 URL에서 ID를 확인
   - 예: `https://apps.apple.com/app/id1510564828` → ID는 `1510564828`

2. **분석 설정**
   - 분석할 국가 선택 (최대 2개까지 비교 분석 가능)
   - 최대 페이지 수 설정 (각 페이지당 최대 50개 리뷰)

3. **분석 시작**
   - '분석 시작' 버튼을 클릭하여 리뷰 데이터 수집 및 분석

4. **결과 확인**
   - 통계 정보, 평점 분포, 년도별 분석 등 다양한 인사이트 확인
   - Excel, CSV, JSON 형식으로 데이터 다운로드

## 🌍 지원 국가

미국, 한국, 일본, 중국, 영국, 캐나다, 호주, 독일, 프랑스, 이탈리아, 스페인, 브라질, 인도, 멕시코, 러시아, 네덜란드, 스웨덴, 스위스, 싱가포르, 홍콩, 대만, 태국, 인도네시아, 필리핀, 말레이시아, 베트남, 폴란드, 터키, 사우디아라비아, UAE

## 📁 프로젝트 구조

```
.
├── app.py                 # Streamlit 메인 애플리케이션
├── analyze_reviews.py     # 리뷰 수집 및 분석 스크립트
├── detailed_analysis.py   # 상세 분석 스크립트
├── requirements.txt       # Python 패키지 의존성
├── README.md             # 프로젝트 문서
└── .gitignore            # Git 무시 파일 목록
```

## 🚢 배포하기

### Streamlit Cloud 배포

1. GitHub에 저장소 업로드
2. [Streamlit Cloud](https://streamlit.io/cloud)에 로그인
3. "New app" 클릭
4. GitHub 저장소 선택
5. 메인 파일 경로: `app.py`
6. "Deploy!" 클릭

### Render 배포

1. GitHub에 저장소 업로드
2. [Render](https://render.com)에 로그인
3. "New Web Service" 선택
4. GitHub 저장소 연결
5. 설정:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
6. "Create Web Service" 클릭

## 🔧 환경 변수

현재 이 프로젝트는 외부 API 키를 사용하지 않습니다. 향후 API 키가 필요한 경우:

### Streamlit Cloud
`.streamlit/secrets.toml` 파일 생성:
```toml
OPENAI_API_KEY = "your-api-key"
GEMINI_API_KEY = "your-api-key"
```

### Render
Dashboard > Environment Variables에서 설정

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **Data Processing**: Pandas
- **Data Export**: OpenPyXL
- **API**: iTunes RSS API
- **Language**: Python 3.8+

## 📝 라이선스

이 프로젝트는 개인/교육용으로 사용됩니다.

## 👤 개발자

**Chang Dong Wook**  
Email: okdongzang@gmail.com

## 🤝 기여

이슈나 개선 사항이 있다면 Pull Request를 환영합니다!

## 📄 라이선스

MIT License
