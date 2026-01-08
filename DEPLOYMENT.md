# 배포 가이드

이 문서는 GitHub 및 Streamlit Cloud/Render 배포를 위한 가이드입니다.

## GitHub 업로드 전 체크리스트

- [x] 하드코딩된 경로 제거
- [x] .gitignore 파일 생성
- [x] requirements.txt 업데이트
- [x] README.md 작성
- [x] 불필요한 파일 제거 (fix_indent.py 등)

## Git 명령어

### 1. Git 저장소 초기화 (처음 한 번만)

```bash
git init
```

### 2. 모든 파일 추가

```bash
git add .
```

### 3. 첫 커밋

```bash
git commit -m "Initial commit: 앱스토어 리뷰 분석 도구"
```

### 4. GitHub 저장소 생성

1. GitHub에서 새 저장소 생성 (예: `app-review-analyzer`)
2. 저장소 URL 확인 (예: `https://github.com/your-username/app-review-analyzer.git`)

### 5. 원격 저장소 연결

```bash
git remote add origin https://github.com/your-username/app-review-analyzer.git
```

### 6. 브랜치 이름 변경 (필요시)

```bash
git branch -M main
```

### 7. GitHub에 푸시

```bash
git push -u origin main
```

## 전체 명령어 시퀀스 (한 번에 실행)

```bash
# 1. Git 초기화
git init

# 2. 파일 추가
git add .

# 3. 커밋
git commit -m "Initial commit: 앱스토어 리뷰 분석 도구"

# 4. 원격 저장소 추가 (URL은 본인의 GitHub 저장소 URL로 변경)
git remote add origin https://github.com/your-username/app-review-analyzer.git

# 5. 메인 브랜치로 이름 변경
git branch -M main

# 6. GitHub에 푸시
git push -u origin main
```

## Streamlit Cloud 배포

1. GitHub에 코드 업로드 완료
2. [Streamlit Cloud](https://share.streamlit.io/) 접속
3. "Sign in with GitHub" 클릭
4. "New app" 클릭
5. 설정:
   - **Repository**: 본인의 GitHub 저장소 선택
   - **Branch**: `main`
   - **Main file path**: `app.py`
6. "Deploy!" 클릭

## Render 배포

1. GitHub에 코드 업로드 완료
2. [Render](https://render.com) 접속 및 GitHub 로그인
3. "New +" > "Web Service" 클릭
4. GitHub 저장소 연결
5. 설정:
   - **Name**: `app-review-analyzer` (원하는 이름)
   - **Region**: 선택
   - **Branch**: `main`
   - **Root Directory**: (비워두기)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
6. "Create Web Service" 클릭

## 주의사항

- `.gitignore`에 포함된 파일은 GitHub에 업로드되지 않습니다
- API 키 등 민감한 정보는 환경 변수로 관리하세요
- Streamlit Cloud는 자동으로 HTTPS를 제공합니다



