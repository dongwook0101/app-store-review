# 🚨 긴급: 리디렉션 URI 오류 해결

## 현재 오류
- **오류 코드**: `redirect_uri_mismatch`
- **요청된 URI**: `https://appstore-review-analyzer.streamlit.app/`
- **문제**: 이 URI가 Google Cloud Console에 등록되지 않음

## ✅ 즉시 해결 방법

### 1단계: Google Cloud Console 접속
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 올바른 프로젝트 선택

### 2단계: OAuth 클라이언트 설정 열기
1. 왼쪽 메뉴에서 **"API 및 서비스"** 클릭
2. **"사용자 인증 정보"** 클릭
3. 클라이언트 ID 목록에서 다음 클라이언트 찾기:
   ```
   403626382842-512spe9nk3dvj2omjj2iqe1880k39btu.apps.googleusercontent.com
   ```
4. 클라이언트 ID를 **클릭**하여 편집 모드로 진입

### 3단계: 리디렉션 URI 추가 (가장 중요!)
1. **"승인된 리디렉션 URI"** 섹션 찾기
2. **"+ URI 추가"** 버튼 클릭
3. 다음 URI를 **정확히** 입력:
   ```
   https://appstore-review-analyzer.streamlit.app/
   ```
   ⚠️ **주의사항**:
   - 끝에 슬래시(`/`) 포함 필수
   - `https://` 사용 (http 아님)
   - 대소문자 정확히 일치
4. **"저장"** 버튼 클릭

### 4단계: JavaScript 원본 추가 (선택사항이지만 권장)
1. **"승인된 JavaScript 원본"** 섹션 찾기
2. **"+ URI 추가"** 버튼 클릭
3. 다음 URI 입력 (슬래시 없음):
   ```
   https://appstore-review-analyzer.streamlit.app
   ```
4. **"저장"** 버튼 클릭

## 📋 최종 확인

설정 후 다음 URI들이 모두 등록되어 있어야 합니다:

### 승인된 리디렉션 URI:
- ✅ `http://localhost:8501` (로컬 개발용)
- ✅ `https://appstore-review-analyzer.streamlit.app/` (배포 환경용) ← **이것이 추가되어야 함!**

### 승인된 JavaScript 원본 (선택사항):
- ✅ `http://localhost:8501` (로컬 개발용)
- ✅ `https://appstore-review-analyzer.streamlit.app` (배포 환경용)

## ⏱️ 적용 시간

- 설정 저장 후 **1-2분** 정도 기다려야 할 수 있습니다
- Google의 서버에 변경사항이 전파되는 시간이 필요합니다

## 🧪 테스트

1. Google Cloud Console에서 저장 완료 후 1-2분 대기
2. 배포된 앱 새로고침: `https://appstore-review-analyzer.streamlit.app/`
3. "Google로 로그인" 버튼 클릭
4. 이제 정상적으로 로그인되어야 합니다!

## ❌ 여전히 오류가 발생하는 경우

1. **URI가 정확한지 확인**:
   - 끝에 슬래시(`/`)가 있는지 확인
   - `https://`인지 확인 (http 아님)
   - 대소문자가 정확한지 확인

2. **저장이 완료되었는지 확인**:
   - Google Cloud Console에서 저장 버튼을 클릭했는지 확인
   - 페이지를 새로고침하여 URI가 목록에 있는지 확인

3. **시간 대기**:
   - 설정 변경 후 최대 5분까지 기다려보세요

4. **브라우저 캐시 클리어**:
   - 브라우저 캐시를 지우고 다시 시도

## 📸 스크린샷 가이드

Google Cloud Console에서 다음과 같이 보여야 합니다:

```
승인된 리디렉션 URI
├── http://localhost:8501
└── https://appstore-review-analyzer.streamlit.app/  ← 이 줄이 있어야 함!
```



