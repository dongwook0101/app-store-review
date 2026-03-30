"""
VOC 키워드 추출 모듈
- 확장된 불용어 사전
- Bigram 우선 추출
- 앱 리뷰 도메인 가중치
- 부정/긍정 모드별 분리 추출
"""

import re
from collections import Counter

# ── 불용어 사전 ─────────────────────────────────────────────────────────────────

KO_STOPWORDS = frozenset({
    # 조사
    '이', '가', '을', '를', '은', '는', '에', '의', '도', '로', '과', '와',
    '에서', '으로', '이나', '이랑', '랑', '한테', '한테서', '께', '에게',
    '에서는', '에서도', '으로는', '로는', '에는', '에도', '이고', '이며',
    # 대명사
    '그', '이거', '저', '제', '나', '너', '우리', '저희', '그것', '이것',
    '그게', '이게', '저게', '그거', '이거', '저거', '여기', '거기', '저기',
    # 수량/정도
    '수', '것', '좀', '더', '너무', '진짜', '정말', '아주', '매우', '약간',
    '조금', '그냥', '많이', '적게', '거의', '완전', '엄청', '되게', '꽤',
    # 연결/접속
    '그래도', '하지만', '근데', '그리고', '그러나', '또한', '또', '다시',
    '이미', '이제', '지금', '그때', '항상', '계속', '항상', '여전히', '아직',
    '해서', '하면', '해도', '하고', '하니', '하는', '하면서', '하여',
    '그래서', '그러면', '그러니', '그러다', '그러므로', '왜냐하면',
    # 어미/종결
    '합니다', '했습니다', '됩니다', '있습니다', '없습니다', '같습니다',
    '같아요', '이에요', '예요', '어요', '아요', '네요', '죠', '요',
    '습니다', '입니다', '이다', '한다', '된다', '있다', '없다', '같다',
    '하다', '됩니다', '이고', '이며', '이라', '해요', '했어요',
    # 감탄/잡어
    '와', '우와', '오', '아', '음', '흠', '헉', '어머', '이야', '진짜로',
    # 범용 단어
    '앱', '어플', '어플리케이션', '리뷰', '업데이트', '사용', '사용자',
    '서비스', '기업', '회사', '이후', '후', '부터', '전', '다음', '이전',
    '경우', '때문', '이유', '방법', '내용', '부분', '점', '때', '곳',
    '분', '번', '개', '가지', '종류', '정도', '수준', '상태',
    # 일반 형용사
    '좋은', '나쁜', '좋아요', '나빠요', '좋네요', '별로예요', '최고예요',
    '괜찮아요', '편해요', '불편해요',
})

EN_STOPWORDS = frozenset({
    # 대명사
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
    'you', 'your', 'yours', 'yourself', 'he', 'him', 'his', 'she', 'her',
    'it', 'its', 'they', 'them', 'their', 'theirs',
    'this', 'that', 'these', 'those', 'who', 'whom', 'what', 'which',
    # be/have/do
    'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
    # 조동사
    'can', 'could', 'will', 'would', 'shall', 'should', 'may', 'might',
    'must', 'ought', 'dare', 'need',
    # 전치사/접속사
    'the', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'so', 'yet',
    'for', 'of', 'in', 'on', 'at', 'by', 'with', 'from', 'to', 'into',
    'through', 'during', 'before', 'after', 'above', 'below', 'between',
    'out', 'off', 'over', 'under', 'about', 'up', 'as', 'nor', 'both',
    'either', 'neither', 'each', 'every', 'all', 'any', 'few', 'more',
    'most', 'other', 'some', 'such', 'than', 'also', 'here', 'there',
    'when', 'where', 'why', 'how', 'again', 'once',
    # 부사
    'very', 'really', 'just', 'too', 'even', 'still', 'now', 'then',
    'always', 'never', 'ever', 'only', 'already', 'yet', 'again', 'once',
    # 리뷰 보일러플레이트
    'app', 'apps', 'application', 'review', 'update', 'version',
    'please', 'try', 'make', 'made', 'get', 'got', 'use', 'used', 'using',
    'since', 'like', 'bit', 'lot', 'one', 'two', 'three', 'first', 'last',
    'new', 'old', 'well', 'back', 'want', 'need', 'know', 'think', 'feel',
    'look', 'come', 'go', 'see', 'say', 'said', 'tell', 'let', 'put',
    'give', 'take', 'keep', 'show', 'find', 'seem', 'ask', 'call',
    # 일반 감성어 (VOC에선 의미 낮음)
    'good', 'great', 'nice', 'bad', 'love', 'loved', 'hate', 'hated',
    'amazing', 'awesome', 'excellent', 'perfect', 'terrible', 'horrible',
    'worst', 'best', 'better', 'worse', 'okay', 'fine', 'ok',
})

# ── 도메인 가중치 사전 ────────────────────────────────────────────────────────

DOMAIN_BONUS: dict[str, float] = {
    # 계정/로그인 (한국어)
    '로그인': 1.8, '로그인 오류': 2.2, '로그인 문제': 2.2, '로그아웃': 1.8,
    '계정': 1.8, '비밀번호': 1.8, '인증': 1.8, '인증번호': 2.0,
    '문자 인증': 2.2, '인증 오류': 2.2, '본인인증': 2.0,
    '회원가입': 1.8, '탈퇴': 1.8, '계정 삭제': 2.0,
    # 결제/구독 (한국어)
    '결제': 1.8, '결제 오류': 2.2, '결제 실패': 2.2, '결제 문제': 2.2,
    '구독': 1.8, '환불': 2.0, '자동결제': 2.0, '과금': 2.0,
    '유료': 1.6, '요금': 1.6, '가격': 1.6,
    # 성능/안정성 (한국어)
    '오류': 1.8, '버그': 1.8, '에러': 1.8, '크래시': 2.0, '튕김': 2.2,
    '앱 튕김': 2.5, '강제종료': 2.2, '먹통': 2.2, '멈춤': 2.0,
    '느림': 1.8, '느려': 1.8, '로딩': 1.8, '로딩 속도': 2.2,
    '렉': 1.8, '버벅': 1.8, '속도': 1.6, '배터리': 1.8, '발열': 1.8,
    # UI/UX (한국어)
    '불편': 1.8, '인터페이스': 1.8, '화면': 1.6, '디자인': 1.6,
    '버튼': 1.6, '레이아웃': 1.8, '사용성': 1.8, 'UI': 1.8, 'UX': 1.8,
    # 광고 (한국어)
    '광고': 1.8, '팝업': 1.8, '광고 팝업': 2.2, '강제 광고': 2.2,
    # 고객지원 (한국어)
    '고객센터': 2.0, '문의': 1.6, '응답': 1.6, '답변': 1.6,
    '고객지원': 2.0, '지원': 1.4,
    # 알림/동기화 (한국어)
    '알림': 1.6, '푸시알림': 1.8, '동기화': 1.8, '동기화 오류': 2.2,
    '백업': 1.8,
    # 계정/로그인 (영어)
    'login': 1.8, 'login error': 2.2, 'login issue': 2.2,
    'logout': 1.8, 'sign in': 1.8, 'sign up': 1.8,
    'account': 1.8, 'password': 1.8, 'verification': 1.8,
    'verification code': 2.2, 'otp': 2.0, 'two factor': 2.0,
    'authentication': 2.0, 'auth': 1.8,
    # 결제/구독 (영어)
    'payment': 1.8, 'payment error': 2.2, 'payment failed': 2.2,
    'subscription': 1.8, 'refund': 2.0, 'billing': 1.8, 'charge': 1.8,
    'purchase': 1.8, 'premium': 1.6, 'price': 1.6, 'expensive': 1.6,
    # 성능/안정성 (영어)
    'crash': 2.0, 'crashes': 2.0, 'crashing': 2.0, 'app crash': 2.5,
    'freeze': 2.0, 'frozen': 2.0, 'bug': 1.8, 'error': 1.8,
    'lag': 2.0, 'laggy': 2.0, 'slow': 1.8, 'slow loading': 2.2,
    'loading': 1.8, 'load': 1.6, 'battery': 1.8, 'drain': 1.8,
    'glitch': 2.0, 'broken': 1.8, 'not working': 2.2,
    # UI/UX (영어)
    'interface': 1.8, 'design': 1.6, 'ui': 1.8, 'ux': 1.8,
    'layout': 1.8, 'navigation': 1.8, 'button': 1.6,
    # 광고 (영어)
    'ads': 1.8, 'advertisement': 1.8, 'popup': 1.8, 'pop up': 1.8,
    # 고객지원 (영어)
    'customer service': 2.2, 'customer support': 2.2, 'support': 1.6,
    'response': 1.6, 'help': 1.4,
    # 알림/동기화 (영어)
    'notification': 1.8, 'notifications': 1.8, 'sync': 1.8,
    'synchronization': 1.8, 'backup': 1.8,
}

# ── 감성 시그널 (모드별 추가 가중치) ──────────────────────────────────────────

NEG_SIGNAL = frozenset({
    'crash', 'crashes', 'crashing', 'error', 'bug', 'bugs', 'broken',
    'freeze', 'frozen', 'lag', 'laggy', 'slow', 'glitch', 'not working',
    '오류', '버그', '에러', '크래시', '튕김', '멈춤', '느림', '렉', '버벅',
    'payment failed', 'payment error', 'login error', 'login issue',
    '결제 오류', '결제 실패', '로그인 오류', '인증 오류',
    'annoying', 'terrible', 'awful', 'useless', 'disappointing',
    '불편', '짜증', '실망', '최악', '별로',
})

POS_SIGNAL = frozenset({
    'fast', 'quick', 'smooth', 'easy', 'clean', 'intuitive', 'helpful',
    'reliable', 'stable', 'efficient', 'convenient',
    '빠름', '편리', '직관적', '안정적', '깔끔', '빠른', '편한',
    'customer service', 'quick response', 'fast response',
    '빠른 응답', '친절한', '빠른 처리',
})


# ── 정규화 ──────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r'https?://\S+', ' ', text)
    text = re.sub(r'v\d+[\.\d]*', ' ', text)         # 버전 표기
    text = re.sub(r'\bver\.?\s*\d+', ' ', text)
    text = re.sub(r'[^\w\s가-힣]', ' ', text)         # 특수문자 제거
    text = re.sub(r'([ㄱ-ㅎㅏ-ㅣ])\1+', '', text)    # 깨진 한글 자모 제거
    text = re.sub(r'(\w)\1{3,}', r'\1\1', text)       # 반복 문자 축소
    text = re.sub(r'\d+', ' ', text)                   # 숫자 제거
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ── 토크나이저 ──────────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    text = _normalize(text)
    tokens = re.findall(r'[가-힣]{2,}|[a-z]{3,}', text)
    return [t for t in tokens if t not in KO_STOPWORDS and t not in EN_STOPWORDS]


# ── Bigram 생성 ─────────────────────────────────────────────────────────────

def _make_bigrams(tokens: list[str]) -> list[str]:
    bigrams = []
    for i in range(len(tokens) - 1):
        a, b = tokens[i], tokens[i + 1]
        # 한국어+한국어 or 영어+영어 bigram만 허용
        a_ko = bool(re.search(r'[가-힣]', a))
        b_ko = bool(re.search(r'[가-힣]', b))
        if a_ko == b_ko:
            bigrams.append(f'{a} {b}')
    return bigrams


# ── 점수 계산 ────────────────────────────────────────────────────────────────

def _score_candidates(
    unigram_counter: Counter,
    bigram_counter: Counter,
    total: int,
    mode: str | None,
) -> dict[str, float]:
    if total == 0:
        return {}

    scores: dict[str, float] = {}

    def _apply(candidate: str, count: int, length_mult: float) -> None:
        tf = count / total
        domain = DOMAIN_BONUS.get(candidate, 1.0)
        sentiment_mult = 1.0
        if mode == 'neg' and candidate in NEG_SIGNAL:
            sentiment_mult = 1.3
        elif mode == 'pos' and candidate in POS_SIGNAL:
            sentiment_mult = 1.3
        scores[candidate] = tf * domain * length_mult * sentiment_mult

    for cand, cnt in bigram_counter.items():
        if cnt >= 2:
            _apply(cand, cnt, 1.4)

    for cand, cnt in unigram_counter.items():
        if cnt >= 2:
            _apply(cand, cnt, 1.0)

    return scores


# ── 중복 제거 및 품질 필터 ───────────────────────────────────────────────────

def _deduplicate(scores: dict[str, float], top_n: int) -> list[tuple[str, int]]:
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    consumed_words: set[str] = set()
    results: list[tuple[str, float]] = []

    for candidate, score in sorted_items:
        if len(results) >= top_n * 3:
            break
        words = candidate.split()
        # bigram이면 구성 단어가 이미 소비됐으면 스킵
        if len(words) == 2:
            if words[0] in consumed_words or words[1] in consumed_words:
                continue
            results.append((candidate, score))
            consumed_words.add(words[0])
            consumed_words.add(words[1])
        else:
            if candidate in consumed_words:
                continue
            results.append((candidate, score))
            consumed_words.add(candidate)

    # 상위 top_n 반환, count 자리에 백분율 기반 정수로 변환 (UI 호환)
    final = results[:top_n]
    # UI에서 (word, cnt) 형태로 사용하므로 score → 임의 표시 숫자로 변환
    # 가장 높은 점수를 100으로 정규화해 상대적 수치 표시
    if not final:
        return []
    max_score = final[0][1]
    return [(w, round(s / max_score * 100)) for w, s in final]


# ── 공개 API ─────────────────────────────────────────────────────────────────

def extract_keywords(
    texts: list[str],
    top_n: int = 5,
    mode: str | None = None,
) -> list[tuple[str, int]]:
    """
    texts: 리뷰 텍스트 리스트
    top_n: 반환할 키워드 수
    mode: 'neg' | 'pos' | None
    returns: [(keyword, score), ...] score는 최고=100 기준 상대값
    """
    all_unigrams: list[str] = []
    all_bigrams: list[str] = []

    for text in texts:
        if not isinstance(text, str) or not text.strip():
            continue
        tokens = _tokenize(text)
        all_unigrams.extend(tokens)
        all_bigrams.extend(_make_bigrams(tokens))

    if not all_unigrams:
        return []

    total = len(all_unigrams)
    unigram_counter = Counter(all_unigrams)
    bigram_counter = Counter(all_bigrams)

    # 도메인 사전에 있는 phrase를 bigram으로 추가 집계
    for phrase, bonus in DOMAIN_BONUS.items():
        if ' ' in phrase and bonus >= 1.8:
            # phrase가 실제 텍스트에 등장하는 빈도 집계
            cnt = sum(1 for text in texts if isinstance(text, str) and phrase in text.lower())
            if cnt >= 2:
                bigram_counter[phrase] = max(bigram_counter.get(phrase, 0), cnt)

    scores = _score_candidates(unigram_counter, bigram_counter, total, mode)
    return _deduplicate(scores, top_n)
