# Google OAuth 설정 가이드

앱스토어 리뷰 분석 도구에서 Google 로그인을 사용하려면 Google OAuth 2.0 클라이언트를 설정해야 합니다.

## 1. Google Cloud Console에서 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. 프로젝트 이름 입력 후 생성

## 2. OAuth 동의 화면 설정

1. 왼쪽 메뉴에서 **"API 및 서비스"** > **"OAuth 동의 화면"** 선택
2. 사용자 유형 선택 (외부 또는 내부)
3. 앱 정보 입력:
   - 앱 이름: "앱스토어 리뷰 분석 도구"
   - 사용자 지원 이메일: 본인 이메일
   - 개발자 연락처 정보: 본인 이메일
4. **저장 후 계속** 클릭

## 3. OAuth 2.0 클라이언트 ID 생성

1. 왼쪽 메뉴에서 **"API 및 서비스"** > **"사용자 인증 정보"** 선택
2. 상단의 **"+ 사용자 인증 정보 만들기"** > **"OAuth 클라이언트 ID"** 선택
3. 애플리케이션 유형: **"웹 애플리케이션"** 선택
4. 이름 입력 (예: "Streamlit App")
5. **승인된 리디렉션 URI** 추가:
   - `http://localhost:8501`
   - (배포 시 실제 도메인도 추가)
6. **만들기** 클릭
7. **클라이언트 ID**와 **클라이언트 보안 비밀번호** 복사

## 4. 환경 변수 설정

### Windows (PowerShell)
```powershell
$env:GOOGLE_CLIENT_ID="여기에_클라이언트_ID_입력"
$env:GOOGLE_CLIENT_SECRET="여기에_클라이언트_시크릿_입력"
```

### Windows (명령 프롬프트)
```cmd
set GOOGLE_CLIENT_ID=여기에_클라이언트_ID_입력
set GOOGLE_CLIENT_SECRET=여기에_클라이언트_시크릿_입력
```

### 영구 설정 (Windows)
1. 시스템 속성 > 고급 > 환경 변수
2. 사용자 변수 또는 시스템 변수에 추가:
   - 변수 이름: `GOOGLE_CLIENT_ID`
   - 변수 값: 클라이언트 ID
   - 변수 이름: `GOOGLE_CLIENT_SECRET`
   - 변수 값: 클라이언트 시크릿

### .env 파일 사용 (권장)

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용 추가:

```
GOOGLE_CLIENT_ID=여기에_클라이언트_ID_입력
GOOGLE_CLIENT_SECRET=여기에_클라이언트_시크릿_입력
```

그리고 `python-dotenv` 패키지를 설치하고 `auth.py`를 수정하여 `.env` 파일을 로드하도록 설정할 수 있습니다.

## 5. 필요한 API 활성화

1. Google Cloud Console에서 **"API 및 서비스"** > **"라이브러리"** 선택
2. 다음 API를 검색하여 활성화:
   - **Google+ API** (사용자 정보 가져오기용)
   - 또는 **Google Identity API**

## 6. 앱 실행

환경 변수를 설정한 후 앱을 실행하면:

1. 앱 시작 시 로그인 페이지가 표시됩니다
2. "Google로 로그인" 버튼을 클릭합니다
3. Google 계정 선택 및 권한 승인
4. 로그인 완료 후 앱스토어 리뷰 분석 도구 사용 가능

## 문제 해결

### "인증 오류"가 발생하는 경우
- 클라이언트 ID와 시크릿이 올바르게 설정되었는지 확인
- 리디렉션 URI가 정확히 `http://localhost:8501`인지 확인
- 환경 변수가 제대로 로드되었는지 확인

### "리디렉션 URI 불일치" 오류
- Google Cloud Console에서 리디렉션 URI가 정확히 `http://localhost:8501`로 설정되어 있는지 확인
- 포트 번호가 다르면 해당 포트로 변경

## 보안 참고사항

- 클라이언트 시크릿은 절대 공개 저장소에 커밋하지 마세요
- `.env` 파일을 `.gitignore`에 추가하세요
- 프로덕션 환경에서는 HTTPS를 사용하세요


