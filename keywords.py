"""
VOC 키워드 추출 모듈 v3
파이프라인:
  1. 정규화
  2. 도메인 phrase 직접 스캔 (raw text → phrase counter)
  3. 토큰 분류 (DOMAIN / GENERIC_OBJECT / NEGATION / NOISE)
  4. bigram/trigram 생성 (DOMAIN_TERM 포함 시 우대)
  5. score = TF * domain_bonus * length_mult * mode_mult
  6. BANNED_SINGLE 후처리 필터
  7. bigram-first 중복 제거
"""

import re
from collections import Counter

# ─────────────────────────────────────────────────────────────────────────────
# 1. 불용어: 토크나이징에서 완전 제거
# ─────────────────────────────────────────────────────────────────────────────

KO_STOPWORDS = frozenset({
    # 조사
    '이','가','을','를','은','는','에','의','도','로','과','와',
    '에서','으로','이나','이랑','랑','한테','한테서','께','에게',
    '에서는','에서도','으로는','로는','에는','에도','이고','이며',
    # 대명사
    '그','이거','저','제','나','너','우리','저희','그것','이것',
    '그게','이게','저게','그거','이거','저거','여기','거기','저기',
    # 정도/부사
    '수','것','좀','더','너무','진짜','정말','아주','매우','약간',
    '조금','그냥','많이','적게','거의','완전','엄청','되게','꽤',
    # 연결어
    '그래도','하지만','근데','그리고','그러나','또한','또','다시',
    '이미','이제','지금','그때','항상','계속','여전히','아직',
    '해서','하면','해도','하고','하니','하는','하면서','하여',
    '그래서','그러면','그러니','그러다','그러므로',
    # 어미
    '합니다','했습니다','됩니다','있습니다','없습니다','같습니다',
    '같아요','이에요','예요','어요','아요','네요','죠','요',
    '습니다','입니다','이다','한다','된다','있다','없다','같다',
    '하다','이고','이며','이라','해요','했어요',
    # 감탄
    '와','우와','오','아','음','흠','헉','어머','이야','진짜로',
    # 시간/순서
    '이후','후','부터','전','다음','이전','경우','때문','이유',
    '방법','내용','부분','점','때','곳','분','번','개','가지',
    '종류','정도','수준','상태',
    # 일반 형용사 (단독 감성어)
    '좋은','나쁜','좋아요','나빠요','좋네요','별로예요','최고예요',
    '괜찮아요','편해요','불편해요',
})

EN_STOPWORDS = frozenset({
    # 대명사
    'i','me','my','myself','we','our','ours','ourselves',
    'you','your','yours','yourself','he','him','his','she','her',
    'it','its','they','them','their','theirs',
    'this','that','these','those','who','whom','what','which',
    # be/have/do
    'is','are','was','were','be','been','being',
    'have','has','had','having','do','does','did','doing',
    # 조동사
    'can','could','will','would','shall','should','may','might',
    'must','ought','dare',
    # 전치사/접속사
    'the','a','an','and','or','but','if','then','so','yet',
    'for','of','in','on','at','by','with','from','to','into',
    'through','during','before','after','above','below','between',
    'out','off','over','under','about','up','as','nor','both',
    'either','neither','each','every','all','any','few','more',
    'most','other','some','such','than','also','here','there',
    'when','where','why','how','again','once',
    # 부사
    'very','really','just','too','even','still','now','then',
    'always','ever','only','already','yet',
    # 리뷰 보일러플레이트
    'app','apps','application','review','update','version',
    'please','make','made','get','got','use','used','using',
    'since','bit','lot','one','two','three','first','last',
    'new','old','well','back','want','know','think','feel',
    'look','come','go','see','say','said','tell','let','put',
    'give','take','keep','show','find','seem','ask','call',
    # 일반 감성어
    'good','great','nice','bad','love','loved','hate','hated',
    'amazing','awesome','excellent','perfect','terrible','horrible',
    'worst','best','better','worse','okay','fine','ok',
})

# ─────────────────────────────────────────────────────────────────────────────
# 2. BANNED_SINGLE: phrase 내부는 허용, 단독 Top 출력은 금지
# ─────────────────────────────────────────────────────────────────────────────

BANNED_SINGLE = frozenset({
    # 부정어
    'not','no','never','cannot','cant',"don't","doesn't","didn't",
    "won't","isn't","aren't","wasn't","weren't",
    # 동사 (맥락 없으면 무의미)
    'send','sent','receive','received','work','working','works','worked',
    'try','tried','trying','fail','failed','fix','fixed',
    'open','close','download','install','installed',
    # generic object / 개체명 단독
    'friend','friends','people','person','user','users','number','numbers',
    'account','service','feature','features','thing','things','stuff',
    'way','time','times','day','days','week','month','year',
    'phone','device','screen','button','menu','page','list',
    # 브랜드/앱명
    'kakao','kakaotalk','kakaobank','line','telegram','instagram',
    'facebook','twitter','youtube','google','apple','android','ios',
    # generic sentiment
    'nice','love','hate','amazing','perfect','awesome','terrible',
    'horrible','useless','disappointing','annoying',
    # 한국어 banned single
    '친구','사람','번호','계정','서비스','기능','사용','이모티콘',
    '소리','화면','버튼','메뉴','페이지','방식','방법',
    '카카오','라인','텔레그램','인스타','페이스북','유튜브',
    '안됨','안돼','안되','못함','없음','모름',
})

# ─────────────────────────────────────────────────────────────────────────────
# 3. ALLOWED_SINGLE: 단독으로도 의미 충분한 고특이성 도메인 단어
# ─────────────────────────────────────────────────────────────────────────────

ALLOWED_SINGLE = frozenset({
    # 영어
    'crash','crashes','crashing','freeze','frozen','lag','laggy',
    'glitch','error','bug','bugs','refund','otp','spam',
    'notification','notifications','ads','advertisement',
    'payment','subscription','billing','verification','authentication',
    'login','logout','password','backup','sync',
    # 한국어
    '튕김','크래시','렉','버벅','먹통','멈춤','오류','버그','에러',
    '환불','결제','구독','로그인','로그아웃','인증','비밀번호',
    '광고','팝업','알림','동기화','백업','불편','발열','배터리',
})

# ─────────────────────────────────────────────────────────────────────────────
# 4. 도메인 phrase 사전 + 가중치
#    — raw text에서 직접 스캔하므로 단어 분리 관계없이 매칭됨
# ─────────────────────────────────────────────────────────────────────────────

DOMAIN_PHRASES: dict[str, float] = {
    # ── 계정/인증 (영어) ──
    'verification code': 2.5, 'verification code not received': 3.0,
    'verification not received': 2.8, 'sms verification': 2.5,
    'phone verification': 2.5, 'otp not received': 2.8,
    'login error': 2.5, 'login issue': 2.5, 'login failed': 2.8,
    'login not working': 2.8, 'cannot login': 2.8, "can't login": 2.8,
    'sign in error': 2.5, 'sign in issue': 2.5,
    'account deleted': 2.5, 'account suspended': 2.5, 'account banned': 2.5,
    'password reset': 2.2, 'forgot password': 2.2,
    'two factor': 2.2, 'two step': 2.2,
    # ── 결제/구독 (영어) ──
    'payment failed': 2.8, 'payment error': 2.8, 'payment issue': 2.5,
    'payment not processed': 2.8, 'charge failed': 2.5,
    'refund request': 2.5, 'refund denied': 2.5, 'no refund': 2.5,
    'subscription issue': 2.5, 'subscription not cancelled': 2.8,
    'auto renewal': 2.2, 'auto charge': 2.2,
    'billing error': 2.5, 'double charged': 2.8,
    'in app purchase': 2.2, 'purchase failed': 2.5,
    # ── 성능/안정성 (영어) ──
    'app crash': 2.8, 'keeps crashing': 3.0, 'crashing constantly': 3.0,
    'app freezes': 2.5, 'app frozen': 2.5, 'app not responding': 2.8,
    'slow loading': 2.5, 'loading issue': 2.5, 'takes forever': 2.5,
    'not working': 2.5, 'stopped working': 2.5, 'no longer works': 2.5,
    'network error': 2.5, 'connection error': 2.5, 'connection issue': 2.5,
    'battery drain': 2.5, 'drains battery': 2.5,
    'too slow': 2.2, 'very slow': 2.2,
    # ── UI/UX (영어) ──
    'too many ads': 2.8, 'ads everywhere': 2.8, 'forced ads': 2.8,
    'notification sound': 2.2, 'sound issue': 2.2, 'sound not working': 2.5,
    'dark mode': 2.0, 'ui issue': 2.2, 'bad ui': 2.2,
    # ── 고객지원 (영어) ──
    'customer service': 2.5, 'customer support': 2.5,
    'no response': 2.5, 'slow response': 2.5, 'no reply': 2.5,
    # ── 계정/인증 (한국어) ──
    '인증번호 미수신': 3.0, '인증번호 안옴': 3.0, '인증 문자': 2.5,
    '문자 인증': 2.5, '본인 인증': 2.5, '인증 오류': 2.8,
    '로그인 오류': 2.8, '로그인 실패': 2.8, '로그인 안됨': 2.8,
    '계정 삭제': 2.5, '계정 정지': 2.5, '비밀번호 분실': 2.2,
    '비밀번호 변경': 2.2, '회원 탈퇴': 2.2,
    # ── 결제/구독 (한국어) ──
    '결제 오류': 2.8, '결제 실패': 2.8, '결제 안됨': 2.8,
    '결제 취소': 2.5, '환불 요청': 2.5, '환불 거절': 2.8,
    '자동 결제': 2.2, '자동결제 취소': 2.5,
    '이중 결제': 2.8, '중복 결제': 2.8,
    '구독 해지': 2.5, '구독 취소': 2.5,
    # ── 성능/안정성 (한국어) ──
    '앱 튕김': 2.8, '계속 튕김': 3.0, '강제 종료': 2.8,
    '로딩 지연': 2.5, '로딩 느림': 2.5, '속도 느림': 2.5,
    '네트워크 오류': 2.5, '연결 오류': 2.5, '접속 오류': 2.5,
    '배터리 소모': 2.5, '발열 심함': 2.5,
    # ── UI/UX (한국어) ──
    '광고 너무 많음': 2.8, '광고 과다': 2.8, '강제 광고': 2.8,
    '광고 팝업': 2.5, '알림 소리': 2.2, '소리 오류': 2.5,
    '다크 모드': 2.0, '사용 불편': 2.5, '인터페이스 불편': 2.5,
    # ── 고객지원 (한국어) ──
    '고객센터 응답': 2.5, '답변 없음': 2.5, '응답 없음': 2.5,
    '고객 지원': 2.2,
    # ── 긍정 phrase ──
    'easy to use': 2.2, 'user friendly': 2.2, 'works great': 2.0,
    'fast response': 2.2, 'quick response': 2.2, 'great design': 2.0,
    'smooth experience': 2.2, 'clean interface': 2.2,
    '사용 편리': 2.2, '빠른 응답': 2.2, '깔끔한 디자인': 2.2,
    '안정적': 2.0, '편리한': 2.0, '직관적': 2.2,
}

# domain bonus for unigram scoring
DOMAIN_UNIGRAM_BONUS: dict[str, float] = {
    'crash': 2.0, 'crashes': 2.0, 'crashing': 2.0,
    'freeze': 2.0, 'frozen': 2.0, 'lag': 2.0, 'laggy': 2.0,
    'glitch': 2.0, 'error': 1.8, 'bug': 1.8, 'bugs': 1.8,
    'refund': 2.0, 'otp': 2.0, 'spam': 1.8,
    'notification': 1.8, 'notifications': 1.8,
    'ads': 1.8, 'advertisement': 1.8,
    'payment': 1.8, 'subscription': 1.8, 'billing': 1.8,
    'verification': 1.8, 'authentication': 1.8,
    'login': 1.8, 'logout': 1.8, 'password': 1.8,
    'backup': 1.8, 'sync': 1.8,
    '튕김': 2.2, '크래시': 2.0, '렉': 2.0, '버벅': 2.0,
    '먹통': 2.2, '멈춤': 2.0, '오류': 1.8, '버그': 1.8, '에러': 1.8,
    '환불': 2.0, '결제': 1.8, '구독': 1.8, '로그인': 1.8, '인증': 1.8,
    '광고': 1.8, '팝업': 1.8, '알림': 1.6, '동기화': 1.8,
    '불편': 1.8, '발열': 1.8, '배터리': 1.8,
}

# 감성 시그널
NEG_SIGNAL = frozenset({
    'crash','crashes','crashing','error','bug','bugs','broken',
    'freeze','frozen','lag','laggy','slow','glitch','not working',
    '오류','버그','에러','크래시','튕김','멈춤','느림','렉','버벅',
    'payment failed','payment error','login error','login issue',
    '결제 오류','결제 실패','로그인 오류','인증 오류',
    '앱 튕김','계속 튕김','강제 종료',
    'keeps crashing','app crash','too many ads',
})

POS_SIGNAL = frozenset({
    'fast','quick','smooth','easy','clean','intuitive','helpful',
    'reliable','stable','efficient','convenient',
    'easy to use','user friendly','fast response','quick response',
    'smooth experience','clean interface','great design',
    '빠름','편리','직관적','안정적','깔끔','빠른','편한',
    '빠른 응답','사용 편리','깔끔한 디자인',
})


# ─────────────────────────────────────────────────────────────────────────────
# 5. 정규화
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r'https?://\S+', ' ', text)
    text = re.sub(r'v\d+[\.\d]*', ' ', text)
    text = re.sub(r'\bver\.?\s*\d+', ' ', text)
    text = re.sub(r'[^\w\s가-힣]', ' ', text)
    text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ]+', ' ', text)   # 깨진 자모 제거
    text = re.sub(r'(\w)\1{3,}', r'\1\1', text)  # 반복 문자 축소
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ─────────────────────────────────────────────────────────────────────────────
# 6. 도메인 phrase 직접 스캔 (raw text 기반)
# ─────────────────────────────────────────────────────────────────────────────

def _scan_domain_phrases(texts: list[str]) -> Counter:
    """DOMAIN_PHRASES 사전의 phrase를 원문에서 직접 카운트."""
    counter: Counter = Counter()
    for text in texts:
        if not isinstance(text, str):
            continue
        norm = _normalize(text)
        for phrase in DOMAIN_PHRASES:
            if phrase in norm:
                counter[phrase] += 1
    return counter


# ─────────────────────────────────────────────────────────────────────────────
# 7. 토크나이징 + bigram/trigram
# ─────────────────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    norm = _normalize(text)
    tokens = re.findall(r'[가-힣]{2,}|[a-z]{3,}', norm)
    return [t for t in tokens
            if t not in KO_STOPWORDS and t not in EN_STOPWORDS]


def _make_ngrams(tokens: list[str]) -> list[str]:
    ngrams: list[str] = []
    n = len(tokens)
    for i in range(n - 1):
        a, b = tokens[i], tokens[i + 1]
        a_ko = bool(re.search(r'[가-힣]', a))
        b_ko = bool(re.search(r'[가-힣]', b))
        if a_ko == b_ko:
            ngrams.append(f'{a} {b}')
            # trigram
            if i + 2 < n:
                c = tokens[i + 2]
                c_ko = bool(re.search(r'[가-힣]', c))
                if a_ko == c_ko:
                    ngrams.append(f'{a} {b} {c}')
    return ngrams


# ─────────────────────────────────────────────────────────────────────────────
# 8. 점수 계산
# ─────────────────────────────────────────────────────────────────────────────

def _compute_scores(
    phrase_counter: Counter,
    ngram_counter: Counter,
    unigram_counter: Counter,
    total_tokens: int,
    mode: str | None,
) -> dict[str, float]:
    if total_tokens == 0:
        return {}

    scores: dict[str, float] = {}

    def _sentiment(candidate: str) -> float:
        if mode == 'neg' and candidate in NEG_SIGNAL:
            return 1.4
        if mode == 'pos' and candidate in POS_SIGNAL:
            return 1.4
        return 1.0

    # ① domain phrase (최우선, 원문 스캔 기반)
    for phrase, cnt in phrase_counter.items():
        if cnt < 2:
            continue
        bonus = DOMAIN_PHRASES.get(phrase, 2.0)
        word_count = len(phrase.split())
        length_mult = 1.6 if word_count >= 3 else 1.4
        tf = cnt / max(len(phrase_counter), 1)
        scores[phrase] = tf * bonus * length_mult * _sentiment(phrase)

    # ② ngram (bigram/trigram)
    for ng, cnt in ngram_counter.items():
        if cnt < 2 or ng in scores:
            continue
        words = ng.split()
        # banned single이 모두인 bigram 금지
        non_banned = [w for w in words if w not in BANNED_SINGLE]
        if not non_banned:
            continue
        length_mult = 1.5 if len(words) >= 3 else 1.3
        bonus = DOMAIN_PHRASES.get(ng, DOMAIN_UNIGRAM_BONUS.get(words[0], 1.0))
        tf = cnt / total_tokens
        scores[ng] = tf * bonus * length_mult * _sentiment(ng)

    # ③ unigram fallback (BANNED_SINGLE 제외, ALLOWED_SINGLE 우대)
    for token, cnt in unigram_counter.items():
        if cnt < 2 or token in scores:
            continue
        if token in BANNED_SINGLE:
            continue
        bonus = DOMAIN_UNIGRAM_BONUS.get(token, 1.0)
        # ALLOWED_SINGLE이 아닌 일반 단어는 penalty
        if token not in ALLOWED_SINGLE:
            bonus *= 0.5
        tf = cnt / total_tokens
        scores[token] = tf * bonus * _sentiment(token)

    return scores


# ─────────────────────────────────────────────────────────────────────────────
# 9. 후처리: bigram-first 중복 제거 + banned single 최종 필터
# ─────────────────────────────────────────────────────────────────────────────

def _postfilter(scores: dict[str, float], top_n: int) -> list[tuple[str, int]]:
    # 길이 긴 것(phrase) 우선 → 점수 순
    sorted_items = sorted(
        scores.items(),
        key=lambda x: (len(x[0].split()), x[1]),
        reverse=True,
    )

    consumed: set[str] = set()
    results: list[tuple[str, float]] = []

    for candidate, score in sorted_items:
        if len(results) >= top_n:
            break
        words = candidate.split()

        # banned single 단독 금지 (최종 방어선)
        if len(words) == 1 and candidate in BANNED_SINGLE:
            continue

        # 이미 소비된 단어가 포함된 후보 스킵
        if any(w in consumed for w in words):
            continue

        results.append((candidate, score))
        for w in words:
            consumed.add(w)

    if not results:
        return []
    max_score = results[0][1]
    return [(w, max(1, round(s / max_score * 100))) for w, s in results]


# ─────────────────────────────────────────────────────────────────────────────
# 10. 공개 API
# ─────────────────────────────────────────────────────────────────────────────

def extract_keywords(
    texts: list[str],
    top_n: int = 5,
    mode: str | None = None,
) -> list[tuple[str, int]]:
    """
    texts : 리뷰 텍스트 리스트
    top_n : 반환할 키워드 수
    mode  : 'neg' | 'pos' | None
    returns: [(keyword, relative_score), ...]  최고=100 기준
    """
    if not texts:
        return []

    # ① 도메인 phrase 직접 스캔
    phrase_counter = _scan_domain_phrases(texts)

    # ② 토크나이징 + ngram
    all_tokens: list[str] = []
    all_ngrams: list[str] = []
    for text in texts:
        if not isinstance(text, str) or not text.strip():
            continue
        tokens = _tokenize(text)
        all_tokens.extend(tokens)
        all_ngrams.extend(_make_ngrams(tokens))

    if not all_tokens:
        return []

    scores = _compute_scores(
        phrase_counter,
        Counter(all_ngrams),
        Counter(all_tokens),
        len(all_tokens),
        mode,
    )
    return _postfilter(scores, top_n)
