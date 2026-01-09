# Google OAuth 설정 완료 ✅

클라이언트 ID와 시크릿이 코드에 설정되었습니다.

## ✅ 완료된 작업

1. ✅ Google OAuth 클라이언트 정보 설정 완료
   - 클라이언트 ID: `403626382842-512spe9nk3dvj2omjj2iqe1880k39btu.apps.googleusercontent.com`
   - 클라이언트 시크릿: `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`

2. ✅ `auth.py`에 기본값으로 설정됨

## ⚠️ 중요: Google Cloud Console 설정 확인

Google Cloud Console에서 다음 설정을 확인하세요:

### 1. 리디렉션 URI 확인
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. **API 및 서비스** > **사용자 인증 정보** 이동
3. 클라이언트 ID 클릭하여 편집
4. **승인된 리디렉션 URI**에 다음이 추가되어 있는지 확인:
   ```
   http://localhost:8501
   ```
   - 없으면 추가하고 저장

### 2. OAuth 동의 화면 확인
1. **API 및 서비스** > **OAuth 동의 화면** 이동
2. 앱이 "테스트 중" 또는 "프로덕션" 상태인지 확인
3. 테스트 중인 경우, 테스트 사용자로 본인 이메일이 추가되어 있는지 확인

## 🚀 실행 방법

1. **패키지 설치** (아직 안 했다면):
   ```bash
   pip install -r requirements.txt
   ```

2. **앱 실행**:
   ```bash
   streamlit run app.py
   ```

3. **로그인 테스트**:
   - 브라우저에서 `http://localhost:8501` 접속
   - "Google로 로그인" 버튼 클릭
   - Google 계정 선택 및 권한 승인
   - 로그인 완료 후 앱 사용 가능

## 🔒 보안 참고사항

현재 클라이언트 정보가 코드에 하드코딩되어 있습니다. 프로덕션 환경에서는:

1. `.env` 파일 생성 (프로젝트 루트에):
   ```
   GOOGLE_CLIENT_ID=403626382842-512spe9nk3dvj2omjj2iqe1880k39btu.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=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
   ```

2. `auth.py`에서 기본값 제거하고 환경 변수만 사용하도록 수정

3. `.gitignore`에 `.env`가 이미 포함되어 있으므로 안전합니다.

## ❓ 문제 해결

### "리디렉션 URI 불일치" 오류
- Google Cloud Console에서 리디렉션 URI가 정확히 `http://localhost:8501`로 설정되어 있는지 확인

### "접근 거부됨" 오류
- OAuth 동의 화면에서 테스트 사용자로 본인 이메일이 추가되어 있는지 확인

### "인증 오류" 발생
- 클라이언트 ID와 시크릿이 올바른지 확인
- Google Cloud Console에서 OAuth 클라이언트가 활성화되어 있는지 확인


