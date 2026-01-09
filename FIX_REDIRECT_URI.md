# 🔧 리디렉션 URI 오류 해결 방법

## ❌ 문제
- **오류**: `redirect_uri_mismatch`
- **원인**: Google Cloud Console에 등록된 URI와 코드에서 사용하는 URI가 다름
  - 코드에서 사용: `http://localhost:8501`
  - Google Cloud Console에 등록됨: `http://localhost:850` (포트 번호 불일치!)

## ✅ 해결 방법

### Google Cloud Console에서 URI 추가

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. **API 및 서비스** > **사용자 인증 정보** 이동
3. 클라이언트 ID (`403626382842-512spe9nk3dvj2omjj2iqe1880k39btu.apps.googleusercontent.com`) 클릭

4. **"승인된 리디렉션 URI"** 섹션에서:
   - 현재 `http://localhost:850`이 등록되어 있음
   - **"URI 추가"** 버튼 클릭
   - 다음 URI를 추가:
     ```
     http://localhost:8501
     ```
   - 저장 클릭

5. **"승인된 JavaScript 원본"** 섹션에서도 (선택사항이지만 권장):
   - `http://localhost:8501` 추가

## 📝 확인 사항

설정 후 다음 URI들이 모두 등록되어 있어야 합니다:
- ✅ `http://localhost:850` (기존)
- ✅ `http://localhost:8501` (새로 추가)

## 🚀 테스트

1. Google Cloud Console에서 저장 완료 후 몇 초 대기
2. 앱을 다시 실행:
   ```bash
   streamlit run app.py
   ```
3. "Google로 로그인" 버튼 클릭
4. 이제 정상적으로 로그인되어야 합니다!

## 💡 참고

Streamlit의 기본 포트는 **8501**입니다. 따라서 `http://localhost:8501`을 사용하는 것이 맞습니다.


