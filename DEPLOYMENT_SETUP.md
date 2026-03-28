# 🚀 배포 환경 설정 가이드

## ✅ 완료된 작업

코드가 배포 환경(Streamlit Cloud)과 로컬 환경을 자동으로 감지하도록 수정되었습니다.

## ⚠️ 필수: Google Cloud Console 설정

배포된 앱에서 Google 로그인이 작동하려면 **반드시** Google Cloud Console에서 배포된 도메인의 리디렉션 URI를 추가해야 합니다.

### 1. 리디렉션 URI 추가

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. **API 및 서비스** > **사용자 인증 정보** 이동
3. 클라이언트 ID (`403626382842-512spe9nk3dvj2omjj2iqe1880k39btu.apps.googleusercontent.com`) 클릭
4. **"승인된 리디렉션 URI"** 섹션에서:
   - **"URI 추가"** 버튼 클릭
   - 다음 URI를 추가:
     ```
     https://appstore-review-analyzer.streamlit.app/
     ```
   - **저장** 클릭

### 2. JavaScript 원본 추가 (선택사항이지만 권장)

1. **"승인된 JavaScript 원본"** 섹션에서:
   - **"URI 추가"** 버튼 클릭
   - 다음 URI를 추가:
     ```
     https://appstore-review-analyzer.streamlit.app
     ```
   - **저장** 클릭

## 📋 최종 확인 사항

Google Cloud Console에 다음 URI들이 모두 등록되어 있어야 합니다:

### 승인된 리디렉션 URI:
- ✅ `http://localhost:8501` (로컬 개발용)
- ✅ `https://appstore-review-analyzer.streamlit.app/` (배포 환경용)

### 승인된 JavaScript 원본 (선택사항):
- ✅ `http://localhost:8501` (로컬 개발용)
- ✅ `https://appstore-review-analyzer.streamlit.app` (배포 환경용)

## 🔄 코드 변경 사항

1. **자동 환경 감지**: 로컬과 배포 환경을 자동으로 감지
2. **동적 리디렉션 URI**: 환경에 따라 적절한 URI 사용
3. **HTTPS 지원**: 배포 환경에서는 HTTPS 사용 (보안 요구사항 준수)
4. **로컬 HTTP 허용**: 로컬 환경에서만 HTTP 허용 (개발 편의성)

## 🧪 테스트

### 로컬 테스트:
```bash
streamlit run app.py
```
- `http://localhost:8501`에서 작동해야 합니다

### 배포 환경 테스트:
- `https://appstore-review-analyzer.streamlit.app/`에서 작동해야 합니다
- Google Cloud Console 설정 후 몇 분 정도 기다려야 할 수 있습니다

## ❌ 문제 해결

### "리디렉션 URI 불일치" 오류 (배포 환경)
→ Google Cloud Console에서 `https://appstore-review-analyzer.streamlit.app/`가 정확히 추가되었는지 확인

### "insecure_transport" 오류 (배포 환경)
→ 배포 환경에서는 HTTPS를 사용하므로 이 오류가 발생하지 않아야 합니다. 발생한다면 Google Cloud Console 설정을 확인하세요.

### 로컬에서만 작동하고 배포 환경에서 작동하지 않음
→ Google Cloud Console에 배포된 도메인의 리디렉션 URI가 추가되었는지 확인

## 📝 참고

- 배포 환경에서는 자동으로 HTTPS를 사용합니다
- 로컬 환경에서는 HTTP를 사용하며, `OAUTHLIB_INSECURE_TRANSPORT` 환경 변수가 자동으로 설정됩니다
- 코드 변경 후 Streamlit Cloud에 다시 배포해야 합니다



