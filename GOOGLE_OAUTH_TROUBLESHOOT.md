# 🔴 Google OAuth 오류 해결 가이드

## 등록된 Google OAuth 설정 확인

현재 `auth.py`에 hardcoded된 Google OAuth 정보:

```
Client ID: 403626382842-512spe9nk3dvj2omjj2iqe1880k39btu.apps.googleusercontent.com
Redirect URI: 
  - http://localhost:8501
  - https://appstore-review-analyzer.streamlit.app/
```

## ❌ 문제 원인

`"앱 실행 중 오류가 발생했습니다"` 메시지가 나오면 다음 중 하나일 수 있습니다:

1. **Google OAuth 클라이언트 ID/시크릿이 만료됨** ✗
2. **Redirect URI가 Google Cloud Console에 미등록됨** ✗
3. **OAuth 동의 화면에서 테스트 사용자 미등록** ✗
4. **네트워크 연결 오류** ✗

---

## 🔧 임시 해결 방법: 개발자 우회 로그인

로그인 오류를 건너뛰고 앱을 테스트하려면:

### 방법 1: URL에 dev 파라미터 추가

1. 터미널에서 앱 실행:
   ```bash
   streamlit run app.py
   ```

2. 브라우저에서 다음 URL로 접속:
   ```
   http://localhost:8501/?dev=1231
   ```

3. **자동으로 개발자 모드로 로그인됩니다** ✅

### 방법 2: 개발자 모드 확인 문구

로그인 페이지에 다음 메시지가 나타나면 성공:
```
🔧 개발자 모드로 로그인되었습니다.
```

---

## 🆕 Google OAuth 새로 설정하기 (권장)

### Step 1: Google Cloud Console 접속

1. https://console.cloud.google.com 로 이동
2. 새 프로젝트 생성 (또는 기존 프로젝트 선택)
3. **"OAuth 2.0 클라이언트 ID"** 검색

### Step 2: OAuth 동의 화면 설정

1. OAuth 동의 화면 탭에서 **"외부"** 선택
2. 필수 정보 입력:
   ```
   앱 이름: App Store Review Analyzer
   사용자 지원 이메일: [본인 이메일]
   개발자 연락처: [본인 이메일]
   ```
3. **범위 추가**: `openid`, `email`, `profile` 선택
4. 테스트 사용자에 본인 이메일 추가

### Step 3: 클라이언트 ID 생성

1. **"사용자 인증 정보"** → **"+ 사용자 인증 정보 만들기"**
2. **"OAuth 2.0 클라이언트 ID"** 선택
3. 애플리케이션 유형: **"웹 애플리케이션"**
4. 리디렉션 URI 추가:
   ```
   http://localhost:8501
   http://localhost:8502
   http://localhost:8503
   https://appstore-review-analyzer.streamlit.app/
   (배포 시 도메인)
   ```
5. **"만들기"** → 클라이언트 ID와 시크릿 복사

### Step 4: 코드에 적용

#### 옵션 A: `.streamlit/secrets.toml` 사용 (권장 - 프로덕션)

```toml
GOOGLE_CLIENT_ID = "YOUR_CLIENT_ID_HERE"
GOOGLE_CLIENT_SECRET = "YOUR_CLIENT_SECRET_HERE"
REDIRECT_URI = "http://localhost:8501"
```

#### 옵션 B: `.env` 파일 사용 (개발)

```env
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
REDIRECT_URI=http://localhost:8501
```

#### 옵션 C: `auth.py` 직접 수정 (임시)

`auth.py`의 CLIENT_CONFIG 수정:
```python
CLIENT_CONFIG = {
    "web": {
        "client_id": "YOUR_CLIENT_ID_HERE",
        "client_secret": "YOUR_CLIENT_SECRET_HERE",
        ...
    }
}
```

---

## ✅ 설정 완료 후 테스트

1. 터미널 재시작
2. 앱 재시작:
   ```bash
   streamlit run app.py
   ```
3. `http://localhost:8501` 접속
4. **"Google로 로그인"** 버튼 클릭
5. Google 계정 선택 및 승인

---

## 📝 즉시 사용하려면

개발자 우회 로그인으로 즉시 테스트:
```
http://localhost:8501/?dev=1231
```

비밀번호: `1231` (`.streamlit/secrets.toml`에서 설정 가능)

---

## 🆘 계속 오류가 나타나면

터미널 로그를 확인하세요:
```
❌ 토큰  획득 실패: [오류 메시지]
❌ 사용자 정보 조회 실패
❌ 인증 중 오류 발생: [상세 오류]
```

이 메시지들이 Streamlit 앱에 표시되므로, 정확한 오류 원인을 파악할 수 있습니다.

---

## 💡 Streamlit Cloud 배포 시

`.streamlit/secrets.toml`에 다음을 추가:
```toml
# Streamlit Cloud 대시보드 → Secrets
GOOGLE_CLIENT_ID = "YOUR_CLIENT_ID"
GOOGLE_CLIENT_SECRET = "YOUR_CLIENT_SECRET"  
REDIRECT_URI = "https://YOUR-APP-NAME.streamlit.app/"
```
