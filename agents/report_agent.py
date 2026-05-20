import os
import re
import tempfile

from fpdf import FPDF
from fpdf.enums import XPos, YPos

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    from matplotlib import font_manager as fm
    _FONT_PATH = os.path.join(os.path.dirname(__file__), '..', 'fonts', 'NanumGothic.ttf')
    if os.path.exists(_FONT_PATH):
        fm.fontManager.addfont(_FONT_PATH)
        plt.rcParams['font.family'] = 'NanumGothic'
    plt.rcParams['axes.unicode_minus'] = False
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False

# ── RGB 색상 ────────────────────────────────────────────────────────
_D  = (27,  67,  50)
_M  = (45, 106,  79)
_L  = (64, 145, 108)
_AC = (116, 198, 157)
_WH = (255, 255, 255)
_TX = (44,  62,  48)
_GR = (120, 140, 125)
_LG = (200, 220, 205)
_RA = (240, 247, 242)
_DK2 = (36, 80, 58)   # 카드 배경용 (다크 그린보다 살짝 밝음)


# ── PDF 클래스 ──────────────────────────────────────────────────────

class _PDF(FPDF):
    def __init__(self, company: str):
        super().__init__()
        self.company = company
        self._has_bold = False
        base = os.path.join(os.path.dirname(__file__), '..', 'fonts')
        self.add_font('N', '', os.path.join(base, 'NanumGothic.ttf'))
        bold = os.path.join(base, 'NanumGothicBold.ttf')
        try:
            if os.path.exists(bold):
                self.add_font('N', 'B', bold)
                self._has_bold = True
        except Exception:
            self._has_bold = False
        self.set_auto_page_break(True, margin=18)
        self.set_margins(15, 15, 15)

    def nb(self, size: float):
        """볼드 폰트 (없으면 일반 폰트로 fallback)."""
        self.set_font('N', 'B' if self._has_bold else '', size=size)

    def nr(self, size: float):
        """일반 폰트."""
        self.set_font('N', '', size=size)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*_D)
        self.rect(0, 0, 210, 11, 'F')
        self.set_font('N', size=7)
        self.set_text_color(*_WH)
        self.set_xy(15, 2.5)
        self.cell(90, 6, 'SDIC AI 기업 재무 분석 리포트', align='L')
        self.set_xy(105, 2.5)
        self.cell(90, 6, self.company, align='R')
        self.set_text_color(*_TX)
        self.set_xy(15, 14)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-13)
        self.set_draw_color(*_LG)
        self.set_line_width(0.3)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(2)
        self.set_font('N', size=7)
        self.set_text_color(*_GR)
        self.cell(
            0, 5,
            f'© 2026 SDIC AI Team 2  ·  DART 공시 데이터 기반 AI 분석  |  {self.page_no()}',
            align='C',
        )
        self.set_text_color(*_TX)

    def sec(self, title: str):
        self.ln(5)
        y = self.get_y()
        self.set_fill_color(*_M)
        self.rect(15, y, 3, 8, 'F')
        self.set_font('N', size=12)
        self.set_text_color(*_D)
        self.set_xy(21, y)
        self.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*_LG)
        self.set_line_width(0.3)
        self.line(15, self.get_y(), 195, self.get_y())
        self.set_text_color(*_TX)
        self.ln(4)


# ── 헬퍼 ────────────────────────────────────────────────────────────

def _fmt(v: int) -> str:
    return f'{v/10000:.1f}조원' if v >= 10000 else f'{v:,}억원'

def _delta(cur: int, prv) -> str:
    if prv is None or prv == 0:
        return ''
    p = (cur - prv) / abs(prv) * 100
    return f'{p:+.1f}%'


# ── 1. 표지 ─────────────────────────────────────────────────────────

def _cover(pdf: _PDF, company: str, years: list, financials: dict):
    pdf.add_page()

    # 살짝 연한 다크 그린 배경
    pdf.set_fill_color(38, 82, 60)
    pdf.rect(0, 0, 210, 297, 'F')

    # ── 상단 얇은 액센트 바 ──
    pdf.set_fill_color(*_AC)
    pdf.rect(0, 0, 210, 3, 'F')

    # ── 전체 내용 수직 중앙 정렬 (총 높이 ≈ 135mm, 시작 y = (297-135)/2 ≈ 81) ──
    y = 75

    # 타이틀
    pdf.nr(28)
    pdf.set_text_color(*_WH)
    pdf.set_xy(20, y)
    pdf.cell(170, 16, 'SDIC AI', align='C')
    y += 16

    pdf.nr(26)
    pdf.set_xy(20, y)
    pdf.cell(170, 15, '기업 재무 분석 리포트', align='C')
    y += 15

    # 팀 정보 (흰색)
    pdf.nb(13)
    pdf.set_text_color(*_WH)
    pdf.set_xy(20, y + 6)
    pdf.cell(170, 9, 'SDIC Team 2', align='C')
    y += 15

    pdf.nr(11)
    pdf.set_text_color(*_WH)
    pdf.set_xy(20, y + 2)
    pdf.cell(170, 8, '김경민  ·  주희진  ·  오하영  ·  신지우', align='C')
    y += 10

    # 구분선
    pdf.set_draw_color(*_AC)
    pdf.set_line_width(0.8)
    pdf.line(40, y + 6, 170, y + 6)
    y += 14

    # 기업명 (흰색에 가깝게)
    pdf.nb(24)
    pdf.set_text_color(235, 250, 245)
    pdf.set_xy(20, y)
    pdf.cell(170, 14, company, align='C')
    y += 14

    # 분석 기간 (흰색에 가깝게)
    pdf.nr(11)
    pdf.set_text_color(220, 242, 235)
    pdf.set_xy(20, y + 2)
    pdf.cell(170, 8, f'분석 기간: {min(years)}년 ~ {max(years)}년  ·  2026년 5월', align='C')
    y += 12

    # 출처 + 면책
    pdf.nr(9)
    pdf.set_text_color(200, 230, 220)
    pdf.set_xy(20, y + 4)
    pdf.cell(170, 6, '금융감독원 DART 공시 데이터 기반  ·  dart.fss.or.kr', align='C')
    y += 10

    pdf.nr(8.5)
    pdf.set_text_color(185, 218, 208)
    pdf.set_xy(20, y + 2)
    pdf.cell(170, 6, '본 보고서는 AI 분석 도구로 생성되었으며 투자 조언을 구성하지 않습니다.', align='C')

    # 하단 얇은 액센트 바
    pdf.set_fill_color(*_AC)
    pdf.rect(0, 294, 210, 3, 'F')


# ── 2. 목차 + 분석 방법론 페이지 ────────────────────────────────────

def _toc(pdf: _PDF, has_competitors: bool):
    # 목차 헤더 배너
    pdf.set_fill_color(*_D)
    pdf.rect(0, 14, 210, 28, 'F')
    pdf.nr(14)
    pdf.set_text_color(*_WH)
    pdf.set_xy(15, 22)
    pdf.cell(0, 12, '목  차', align='L')
    pdf.set_xy(15, 44)

    toc_items = [
        ('I.',    '핵심 지표 요약 및 분석 방법론'),
        ('II.',   '연도별 재무 현황 (매출액 · 영업이익 · 순이익 · 이익률)'),
        ('III.',  '전년 대비 성장률 (YoY)'),
        ('IV.',   '재무 지표 추이 차트'),
        ('V.',    'Claude AI 재무 분석'),
        ('VI.',   '산업 동향 분석'),
        ('VII.',  '산업별 맞춤 분석'),
    ]
    if has_competitors:
        toc_items.append(('VIII.', '경쟁사 비교 분석'))

    pdf.ln(6)  # 헤더 박스 아래 여백

    for i, (num, title) in enumerate(toc_items):
        y = pdf.get_y()
        bg = _RA if i % 2 == 0 else _WH
        pdf.set_fill_color(*bg)
        pdf.rect(15, y, 180, 11, 'F')
        pdf.set_fill_color(*_M)
        pdf.rect(15, y, 3, 11, 'F')
        pdf.nb(11)
        pdf.set_text_color(*_M)
        pdf.set_xy(21, y + 2)
        pdf.cell(16, 7, num)
        pdf.nr(11)
        pdf.set_text_color(*_TX)
        pdf.set_xy(39, y + 2)
        pdf.cell(153, 7, title)
        pdf.ln(12)

    pdf.set_text_color(*_TX)


# ── 분석 방법론 (테이블) ─────────────────────────────────────────────

def _methodology_compact(pdf: _PDF):
    pdf.sec('분석 방법론')

    items = [
        ('재무 데이터',   'DART 전자공시 연결 재무제표 기준  ·  SQLite 캐시'),
        ('AI 분석',       'Anthropic Claude (claude-haiku-4-5)  ·  할루시네이션 방지 프롬프트'),
        ('RAG 검색',      'TF-IDF 벡터화 + 코사인 유사도 기반 문서 검색  ·  joblib 캐시'),
        ('시각화',        '매출·이익 추이 꺾은선 + 영업이익률 막대 차트 자동 생성'),
        ('경쟁사 비교',   'Claude 경쟁사 식별 → DART API 재무 데이터 자동 수집 및 비교'),
        ('산업 동향',     '시장 규모·성장률 추세, 핵심 기술 변화, 정책·규제 환경 분석'),
        ('산업별 맞춤',   '업종 특화 KPI · 규제 리스크 · 산업 사이클 위치 분석'),
    ]

    lw, rw = 35, 145  # 분류 열, 내용 열

    # 헤더
    y0, x0 = pdf.get_y(), 15
    pdf.set_fill_color(*_D)
    pdf.set_text_color(*_WH)
    pdf.nr(8)
    for header, w in [('분류', lw), ('내용', rw)]:
        pdf.set_draw_color(*_LG)
        pdf.set_line_width(0.3)
        pdf.set_xy(x0, y0)
        pdf.cell(w, 7, header, border=1, align='C', fill=True)
        x0 += w
    pdf.ln(7)

    for idx, (label, desc) in enumerate(items):
        y0, x0 = pdf.get_y(), 15
        bg = _RA if idx % 2 == 0 else _WH
        pdf.set_fill_color(*bg)
        pdf.set_draw_color(*_LG)
        pdf.set_line_width(0.3)
        pdf.set_text_color(*_TX)
        pdf.nb(8)
        pdf.set_xy(x0, y0)
        pdf.cell(lw, 7, label, border=1, align='C', fill=True)
        pdf.nr(8)
        pdf.set_xy(x0 + lw, y0)
        pdf.cell(rw, 7, desc, border=1, align='L', fill=True)
        pdf.ln(7)

    pdf.set_text_color(*_TX)
    pdf.ln(4)


# ── 3. KPI 핵심 지표 ─────────────────────────────────────────────────

def _kpi_section(pdf: _PDF, financials: dict):
    # 방법론↔KPI 구분 — 여백 사이 가운데 구분선
    pdf.ln(3)
    pdf.set_draw_color(*_LG)
    pdf.set_line_width(0.5)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(3)
    pdf.sec('I.  핵심 지표 요약')

    sorted_f = sorted(financials.items())
    latest_year, latest = sorted_f[-1]
    prev = sorted_f[-2][1] if len(sorted_f) >= 2 else None

    rev    = latest['매출액']
    op     = latest['영업이익']
    net    = latest['순이익']
    margin = round(op / rev * 100, 1) if rev else 0
    p_rev    = prev['매출액']   if prev else None
    p_op     = prev['영업이익'] if prev else None
    p_net    = prev['순이익']   if prev else None
    p_margin = round(p_op / p_rev * 100, 1) if (prev and p_rev) else None
    d_margin = f'{margin - p_margin:+.1f}%p (YoY)' if p_margin is not None else ''

    kpis = [
        (f'매출액 ({latest_year})',      _fmt(rev),         _delta(rev, p_rev) + ' (YoY)' if _delta(rev, p_rev) else ''),
        (f'영업이익 ({latest_year})',    _fmt(op),          _delta(op,  p_op)  + ' (YoY)' if _delta(op,  p_op)  else ''),
        (f'순이익 ({latest_year})',      _fmt(net),         _delta(net, p_net) + ' (YoY)' if _delta(net, p_net) else ''),
        (f'영업이익률 ({latest_year})', f'{margin:.1f}%',  d_margin),
    ]

    bw, gap, x0, y0 = 42, 3, 15, pdf.get_y()
    for i, (label, value, d) in enumerate(kpis):
        x = x0 + i * (bw + gap)
        pdf.set_fill_color(*_RA)
        pdf.set_draw_color(*_LG)
        pdf.set_line_width(0.3)
        pdf.rect(x, y0, bw, 28, 'FD')
        pdf.set_fill_color(*_L)
        pdf.rect(x, y0, bw, 2, 'F')
        pdf.nr(7)
        pdf.set_text_color(*_GR)
        pdf.set_xy(x + 2, y0 + 4)
        pdf.cell(bw - 4, 5, label)
        pdf.nr(10)
        pdf.set_text_color(*_D)
        pdf.set_xy(x + 2, y0 + 11)
        pdf.cell(bw - 4, 7, value)
        if d:
            pdf.nr(7)
            if d.startswith('+'):
                pdf.set_text_color(40, 130, 80)
            else:
                pdf.set_text_color(180, 60, 60)
            pdf.set_xy(x + 2, y0 + 20)
            pdf.cell(bw - 4, 5, d)

    pdf.set_text_color(*_TX)
    pdf.set_xy(15, y0 + 32)
    pdf.ln(4)


# ── 3. 재무 테이블 ───────────────────────────────────────────────────

def _financial_table(pdf: _PDF, financials: dict):
    pdf.sec('I.  연도별 재무 현황 (단위: 억원)')

    col_w   = [20, 37, 37, 37, 29, 30]
    headers = ['연도', '매출액', '영업이익', '순이익', '영업이익률', '순이익률']

    def _row(cells, fill, tc=_TX):
        if pdf.get_y() > 262:
            pdf.add_page()
        y0, x0 = pdf.get_y(), 15
        pdf.set_fill_color(*fill)
        for val, w in zip(cells, col_w):
            pdf.set_text_color(*tc)
            pdf.nr(8)
            pdf.set_draw_color(*_LG)
            pdf.set_line_width(0.3)
            pdf.set_xy(x0, y0)
            pdf.cell(w, 7, val, border=1, align='C', fill=True)
            x0 += w
        pdf.ln(7)

    _row(headers, _D, _WH)

    for idx, (year, v) in enumerate(sorted(financials.items())):
        rev    = v['매출액']
        op     = v['영업이익']
        net    = v['순이익']
        op_m   = round(op  / rev * 100, 1) if rev else 0
        net_m  = round(net / rev * 100, 1) if rev else 0
        _row(
            [str(year), f'{rev:,}', f'{op:,}', f'{net:,}',
             f'{op_m:.1f}%', f'{net_m:.1f}%'],
            _RA if idx % 2 else _WH,
        )

    # 데이터 출처 주석
    pdf.nr(7)
    pdf.set_text_color(*_GR)
    pdf.cell(0, 5, '※ 출처: 금융감독원 전자공시시스템 (DART)  ·  연결 재무제표 기준',
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*_TX)
    pdf.ln(3)


# ── 3. YoY 성장률 테이블 ─────────────────────────────────────────────

def _yoy_table(pdf: _PDF, financials: dict):
    pdf.sec('II.  전년 대비 성장률 (YoY)')

    sorted_f = sorted(financials.items())
    if len(sorted_f) < 2:
        pdf.nr(9)
        pdf.cell(0, 7, '비교 데이터 부족', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        return

    col_w   = [20, 40, 40, 40, 30, 20]
    headers = ['연도', '매출액 YoY', '영업이익 YoY', '순이익 YoY', '이익률 변화', '성장 평가']

    def _hdr():
        y0, x0 = pdf.get_y(), 15
        pdf.set_fill_color(*_D)
        pdf.nr(8)
        for h, w in zip(headers, col_w):
            pdf.set_text_color(*_WH)
            pdf.set_xy(x0, y0)
            pdf.cell(w, 7, h, border=1, align='C', fill=True)
            x0 += w
        pdf.ln(7)

    _hdr()

    def pct(c, p):
        if p == 0:
            return '—'
        return f'{(c - p) / abs(p) * 100:+.1f}%'

    def grade(rev_yoy: str, op_yoy: str) -> str:
        try:
            rv = float(rev_yoy.replace('%', ''))
            ov = float(op_yoy.replace('%', ''))
            if rv > 10 and ov > 10:
                return '우수'
            if rv > 0 and ov > 0:
                return '양호'
            if rv > 0:
                return '보통'
            return '부진'
        except Exception:
            return '—'

    for idx in range(1, len(sorted_f)):
        yr, cur = sorted_f[idx]
        _,  prv = sorted_f[idx - 1]
        cur_m   = round(cur['영업이익'] / cur['매출액'] * 100, 1) if cur['매출액'] else 0
        prv_m   = round(prv['영업이익'] / prv['매출액'] * 100, 1) if prv['매출액'] else 0
        rev_yoy = pct(cur['매출액'],   prv['매출액'])
        op_yoy  = pct(cur['영업이익'], prv['영업이익'])
        net_yoy = pct(cur['순이익'],   prv['순이익'])
        m_chg   = f'{cur_m - prv_m:+.1f}%p'
        g       = grade(rev_yoy, op_yoy)
        row     = [str(yr), rev_yoy, op_yoy, net_yoy, m_chg, g]

        if pdf.get_y() > 262:
            pdf.add_page()
            _hdr()

        y0, x0 = pdf.get_y(), 15
        bg = _RA if idx % 2 else _WH
        pdf.set_fill_color(*bg)
        for val, w in zip(row, col_w):
            if val.startswith('+'):
                tc = (40, 130, 80)
            elif val.startswith('-'):
                tc = (180, 60, 60)
            elif val in ('우수', '양호'):
                tc = (40, 130, 80)
            elif val == '부진':
                tc = (180, 60, 60)
            else:
                tc = _TX
            pdf.set_text_color(*tc)
            pdf.nr(8)
            pdf.set_draw_color(*_LG)
            pdf.set_line_width(0.3)
            pdf.set_xy(x0, y0)
            pdf.cell(w, 7, val, border=1, align='C', fill=True)
            x0 += w
        pdf.ln(7)

    pdf.set_text_color(*_TX)
    pdf.ln(4)


# ── 5. 경쟁사 비교 섹션 ──────────────────────────────────────────────

def _competitor_section(pdf: _PDF, company: str, financials: dict,
                        competitors: dict, competitor_analysis: str):
    if not competitors and not competitor_analysis:
        return

    if pdf.get_y() > 200:
        pdf.add_page()
    pdf.sec('V.  경쟁사 비교 분석')

    def _latest(d: dict):
        if not d:
            return '—', {}
        key = max(d.keys(), key=lambda x: int(x))
        return str(key), d[key]

    if competitors:
        main_year, main_data = _latest(financials)
        all_companies = [(company, main_year, main_data)] + [
            (comp, *_latest(data)) for comp, data in competitors.items()
        ]

        col_w   = [38, 14, 33, 33, 28, 28]
        headers = ['기업명', '연도', '매출액(억원)', '영업이익(억원)', '영업이익률', '순이익(억원)']

        if pdf.get_y() > 262:
            pdf.add_page()
        y0, x0 = pdf.get_y(), 15
        pdf.set_fill_color(*_D)
        for h, w in zip(headers, col_w):
            pdf.set_text_color(*_WH)
            pdf.nr(7.5)
            pdf.set_draw_color(*_LG)
            pdf.set_line_width(0.3)
            pdf.set_xy(x0, y0)
            pdf.cell(w, 7, h, border=1, align='C', fill=True)
            x0 += w
        pdf.ln(7)

        for idx, (name, year, data) in enumerate(all_companies):
            rev    = data.get('매출액', 0)
            op     = data.get('영업이익', 0)
            net    = data.get('순이익', 0)
            margin = round(op / rev * 100, 1) if rev else 0
            is_main = (idx == 0)
            row = [name, year,
                   f'{rev:,}' if rev else '—',
                   f'{op:,}'  if op  else '—',
                   f'{margin:.1f}%' if rev else '—',
                   f'{net:,}' if net else '—']

            if pdf.get_y() > 262:
                pdf.add_page()
            y0, x0 = pdf.get_y(), 15
            pdf.set_fill_color(*(_RA if idx % 2 else _WH))
            for val, w in zip(row, col_w):
                pdf.set_text_color(*(_D if is_main else _TX))
                pdf.nr(7.5)
                pdf.set_draw_color(*_LG)
                pdf.set_line_width(0.5 if is_main else 0.3)
                pdf.set_xy(x0, y0)
                pdf.cell(w, 7, val, border=1, align='C', fill=True)
                x0 += w
            pdf.ln(7)

        pdf.nr(7)
        pdf.set_text_color(*_GR)
        pdf.cell(0, 5, '※ 각 기업의 가장 최근 공시 연도 기준  ·  DART 연결 재무제표',
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*_TX)
        pdf.ln(4)

    if competitor_analysis and competitor_analysis not in ('경쟁사 데이터가 없습니다.', '회사명이 없습니다.'):
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', competitor_analysis)
        clean = re.sub(r'\*(.+?)\*',     r'\1', clean)
        token_pat = re.compile(
            r'(\d[\d,\.]*\s*(?:조원|억원|%p|%|만원|원|배|년|분기)?)'
        )
        for para in clean.split('\n'):
            if not para.strip():
                pdf.ln(3)
                continue
            pdf.set_xy(15, pdf.get_y())
            for tok in token_pat.split(para):
                if not tok:
                    continue
                if token_pat.fullmatch(tok):
                    pdf.nb(10.5)
                    pdf.set_text_color(*_D)
                else:
                    pdf.nr(10.5)
                    pdf.set_text_color(*_TX)
                pdf.write(6.5, tok)
            pdf.ln(6.5)
        pdf.ln(3)


# ── 4. 차트 ─────────────────────────────────────────────────────────

def _trend_png(financials: dict, company: str):
    if not MATPLOTLIB_OK:
        return None
    sf  = sorted(financials.items())
    yrs = [y for y, _ in sf]
    rev = [v['매출액']   / 10000 for _, v in sf]
    op  = [v['영업이익'] / 10000 for _, v in sf]
    net = [v['순이익']   / 10000 for _, v in sf]

    fig, ax = plt.subplots(figsize=(9.5, 3.6))
    ax.plot(yrs, rev, 'o-', color='#1b4332', lw=2.2, label='매출액',   ms=6)
    ax.plot(yrs, op,  's-', color='#40916c', lw=2.2, label='영업이익', ms=6)
    ax.plot(yrs, net, '^-', color='#74c69d', lw=2.2, label='순이익',   ms=6)
    for xs, ys, clr in [(yrs, rev, '#1b4332'), (yrs, op, '#40916c'), (yrs, net, '#74c69d')]:
        for x, y in zip(xs, ys):
            ax.annotate(f'{y:.1f}', (x, y), textcoords='offset points',
                        xytext=(0, 6), ha='center', fontsize=6.5, color=clr)

    ax.set_title(f'{company} 매출액 / 영업이익 / 순이익 추이', fontsize=10, pad=10, color='#1b4332')
    ax.set_ylabel('금액 (조원)', fontsize=8)
    ax.legend(fontsize=8, loc='upper left', framealpha=0.7)
    ax.grid(axis='y', linestyle='--', alpha=0.4, color='#c8e6c9')
    ax.set_facecolor('#f8fdf9')
    fig.patch.set_facecolor('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(labelsize=7)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}조'))
    ax.set_xticks(yrs)
    plt.tight_layout()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    tmp.close()
    fig.savefig(tmp.name, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return tmp.name


def _margin_png(financials: dict, company: str):
    if not MATPLOTLIB_OK:
        return None
    sf      = sorted(financials.items())
    yrs     = [y for y, _ in sf]
    margins = [round(v['영업이익'] / v['매출액'] * 100, 1) if v['매출액'] else 0 for _, v in sf]

    fig, ax = plt.subplots(figsize=(9.5, 3.0))
    colors  = ['#40916c' if m >= 0 else '#e57373' for m in margins]
    bars    = ax.bar(yrs, margins, color=colors, alpha=0.85, width=0.5,
                     edgecolor='white', linewidth=0.8)
    for bar, val in zip(bars, margins):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + (0.3 if val >= 0 else -1.5),
                f'{val:.1f}%', ha='center', va='bottom', fontsize=7.5, color='#1b4332')

    ax.set_title(f'{company} 영업이익률 추이', fontsize=10, pad=10, color='#1b4332')
    ax.set_ylabel('영업이익률 (%)', fontsize=8)
    ax.set_xticks(yrs)
    ax.axhline(0, color='#1b4332', linewidth=0.8)
    ax.grid(axis='y', linestyle='--', alpha=0.4, color='#c8e6c9')
    ax.set_facecolor('#f8fdf9')
    fig.patch.set_facecolor('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(labelsize=7)
    plt.tight_layout()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    tmp.close()
    fig.savefig(tmp.name, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return tmp.name


def _charts_section(pdf: _PDF, financials: dict, company: str):
    c1 = _trend_png(financials, company)
    c2 = _margin_png(financials, company)

    if c1:
        pdf.sec('III.  재무 지표 추이')
        pdf.image(c1, x=15, w=180)
        pdf.ln(4)
        os.unlink(c1)

    if c2:
        if pdf.get_y() > 200:
            pdf.add_page()
        pdf.sec('영업이익률 추이')
        pdf.image(c2, x=15, w=180)
        pdf.ln(4)
        os.unlink(c2)

    if not c1 and not c2:
        pdf.nr(9)
        pdf.set_text_color(*_GR)
        pdf.cell(0, 7, '(matplotlib 미설치 — 차트 생략)',
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*_TX)


# ── 5. AI 분석 섹션 ──────────────────────────────────────────────────

def _parse_numbered(text: str) -> list[tuple[str, str]]:
    """'1. 제목\n내용' 형태를 (제목, 내용) 리스트로 파싱. 번호 앞 프리앰블 제거."""
    clean = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    clean = re.sub(r'\*(.+?)\*',     r'\1', clean)
    clean = re.sub(r'#+\s*',         '',    clean)
    clean = re.sub(r'^\s*---+\s*$',  '',    clean, flags=re.MULTILINE)
    clean = re.sub(r'\.\.\.',        '',    clean)
    clean = re.sub(r'\n{3,}',        '\n\n', clean)
    # 첫 번째 '1.' 이전 내용 제거
    first = re.search(r'(?m)^1\.', clean)
    if first:
        clean = clean[first.start():]
    parts = re.split(r'\n(?=\d+\.)', clean.strip())
    result = []
    for p in parts:
        lines = p.strip().splitlines()
        if not lines:
            continue
        header = re.sub(r'^\d+\.\s*', '', lines[0]).strip()
        body   = '\n'.join(l.strip() for l in lines[1:] if l.strip())
        if header:
            result.append((header, body))
    return result


def _render_analysis_block(pdf: _PDF, sec_title: str, text: str, subtitle: str = ''):
    """산업 분석 블록 — 카드 스타일 (테두리만, 채움 없음)."""
    pdf.sec(sec_title)

    # 산업명 — 2줄 가능한 큰 박스
    if subtitle:
        lines_needed = max(1, len(subtitle) // 52 + 1)
        box_h = 10 + lines_needed * 8
        y = pdf.get_y()
        pdf.set_fill_color(*_RA)
        pdf.rect(15, y, 180, box_h, 'F')
        pdf.set_draw_color(*_L)
        pdf.set_line_width(0.8)
        pdf.rect(15, y, 180, box_h, 'D')
        pdf.set_fill_color(*_M)
        pdf.rect(15, y, 4, box_h, 'F')
        pdf.nb(11)
        pdf.set_text_color(*_D)
        pdf.set_xy(22, y + (box_h - lines_needed * 8) / 2 + 1)
        pdf.multi_cell(170, 8, subtitle, align='L')
        pdf.set_xy(15, y + box_h + 4)
        pdf.ln(0)

    # 마크다운 제거 (# 헤더, **볼드**, *이탤릭*, --- 구분선, ... 생략 표시)
    clean_text = re.sub(r'#+\s*',          '',  text)
    clean_text = re.sub(r'\*\*(.+?)\*\*',  r'\1', clean_text)
    clean_text = re.sub(r'\*(.+?)\*',      r'\1', clean_text)
    clean_text = re.sub(r'^\s*---+\s*$',   '',  clean_text, flags=re.MULTILINE)
    clean_text = re.sub(r'\.\.\.',         '',  clean_text)
    clean_text = re.sub(r'\n{3,}',         '\n\n', clean_text)

    sections = _parse_numbered(clean_text)
    if not sections:
        pdf.nr(9.5)
        pdf.set_text_color(*_TX)
        pdf.set_xy(15, pdf.get_y())
        pdf.multi_cell(180, 6, clean_text.strip(), align='L')
        return

    def _est_h(body_text: str, body_w: float = 172, line_h: float = 6) -> float:
        """한국어 문자 단위 줄 수 계산."""
        pdf.nr(9)
        h = 0.0
        for para in (body_text.strip().split('\n') if body_text else []):
            if not para.strip():
                h += line_h * 0.5
                continue
            lw, lines = 0.0, 1
            for ch in para:
                cw = pdf.get_string_width(ch)
                if lw + cw > body_w and lw > 0:
                    lines += 1
                    lw = cw
                else:
                    lw += cw
            h += lines * line_h
        return 13 + h + 10  # header + body + bottom padding

    for i, (header, body) in enumerate(sections):
        est = _est_h(body) * 1.3   # 30% 여유

        # 남은 공간이 부족하면 새 페이지
        if pdf.get_y() + est > 268:
            pdf.add_page()

        y_start  = pdf.get_y()
        pg_start = pdf.page_no()

        # ① 헤더 (항상 고정 높이)
        pdf.set_fill_color(*_RA)
        pdf.rect(15, y_start, 180, 11, 'F')
        pdf.set_fill_color(*_M)
        pdf.rect(15, y_start, 11, 11, 'F')
        pdf.nb(8.5)
        pdf.set_text_color(*_WH)
        pdf.set_xy(15, y_start + 2)
        pdf.cell(11, 7, str(i + 1), align='C')
        pdf.nb(9)
        pdf.set_text_color(*_D)
        pdf.set_xy(29, y_start + 2)
        pdf.cell(163, 7, header, align='L')

        # ② 본문 — auto_page_break ON 유지 (내용이 길어도 잘리지 않음)
        if body:
            pdf.nr(9)
            pdf.set_text_color(*_TX)
            pdf.set_xy(19, y_start + 13)
            pdf.multi_cell(172, 6, body.strip(), align='L')

        pdf.ln(3)
        y_end   = pdf.get_y()
        pg_end  = pdf.page_no()

        # ③ 테두리: 페이지 전환 없을 때만 박스, 페이지 걸치면 좌측 선만
        if pg_end == pg_start:
            pdf.set_draw_color(*_L)
            pdf.set_line_width(0.8)
            pdf.rect(15, y_start, 180, y_end - y_start, 'D')
        else:
            # 현재 페이지 좌측 선만 표시
            pdf.set_draw_color(*_L)
            pdf.set_line_width(1.5)
            pdf.line(15, 14, 15, y_end)

        pdf.ln(4)

    pdf.ln(2)


def _industry_section(pdf: _PDF, industry: str, trend: str, specific: str):
    if not trend and not specific:
        return

    subtitle = industry if industry else ''

    if trend:
        pdf.add_page()
        _render_analysis_block(pdf, 'VI.  산업 동향 분석', trend, subtitle)

    if specific:
        pdf.add_page()
        _render_analysis_block(pdf, 'VII.  산업별 맞춤 분석', specific, subtitle)


def _analysis_section(pdf: _PDF, analysis: str):
    if pdf.get_y() > 220:
        pdf.add_page()
    pdf.sec('IV.  Claude AI 재무 분석')

    if not analysis:
        pdf.nr(9)
        pdf.cell(0, 7, '분석 결과 없음', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        return

    clean = re.sub(r'\*\*(.+?)\*\*', r'\1', analysis)
    clean = re.sub(r'\*(.+?)\*',     r'\1', clean)
    clean = re.sub(r'^#{1,6}\s+',    '',    clean, flags=re.MULTILINE)

    # 숫자/퍼센트/단위 패턴을 볼드로 렌더링
    token_pat = re.compile(
        r'(\d[\d,\.]*\s*(?:조원|억원|%p|%|만원|원|배|년|분기)?)'
    )
    for para in clean.split('\n'):
        if not para.strip():
            pdf.ln(3)
            continue
        tokens = token_pat.split(para)
        x_start = 15
        pdf.set_xy(x_start, pdf.get_y())
        line_w = 180
        for tok in tokens:
            if not tok:
                continue
            is_num = bool(token_pat.fullmatch(tok))
            if is_num:
                pdf.nb(10)
                pdf.set_text_color(*_D)
            else:
                pdf.nr(10)
                pdf.set_text_color(*_TX)
            # multi_cell로 줄바꿈 처리 (마지막 토큰이면 줄바꿈)
            pdf.write(6, tok)
        pdf.ln(6)

    pdf.ln(4)
    pdf.nr(7)
    pdf.set_text_color(*_GR)
    pdf.multi_cell(
        0, 5,
        '* 본 분석은 Claude AI(claude-haiku-4-5)가 DART 재무 데이터를 기반으로 생성한 결과입니다.\n'
        '  투자 의사결정의 근거로 사용하지 마십시오.',
        align='L',
    )
    pdf.set_text_color(*_TX)


# ── 최종 생성 ────────────────────────────────────────────────────────

def generate_pdf(company: str, financials: dict, analysis: str,
                 competitors: dict = None, competitor_analysis: str = '',
                 industry: str = '', industry_trend: str = '',
                 industry_specific: str = '') -> str:
    pdf   = _PDF(company)
    sf    = sorted(financials.items())
    years = [y for y, _ in sf]

    has_comp = bool(competitors)

    # 1페이지: 표지
    _cover(pdf, company, years, financials)

    # 2페이지: 목차
    pdf.add_page()
    _toc(pdf, has_comp)

    # 3페이지: 분석 방법론 + KPI + 재무 테이블 + YoY
    pdf.add_page()
    _methodology_compact(pdf)
    _kpi_section(pdf, financials)
    _financial_table(pdf, financials)
    _yoy_table(pdf, financials)

    # 4페이지: 차트 + AI 분석
    pdf.add_page()
    _charts_section(pdf, financials, company)
    _analysis_section(pdf, analysis)

    # 산업 동향 + 산업별 맞춤 분석
    _industry_section(pdf, industry, industry_trend, industry_specific)

    # 마지막: 경쟁사 비교
    _competitor_section(pdf, company, financials,
                        competitors or {}, competitor_analysis)

    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix='.pdf', prefix=f'report_{company}_'
    )
    tmp.close()
    pdf.output(tmp.name)
    return tmp.name


def run_report_agent(state: dict) -> dict:
    pdf_path = generate_pdf(
        company=state['company'],
        financials=state['financials'],
        analysis=state['analysis'],
        competitors=state.get('competitors', {}),
        competitor_analysis=state.get('competitor_analysis', ''),
        industry=state.get('industry', ''),
        industry_trend=state.get('industry_trend', ''),
        industry_specific=state.get('industry_specific', ''),
    )
    state['pdf_path'] = pdf_path
    return state


if __name__ == '__main__':
    mock_state = {
        'company': '삼성전자',
        'financials': {
            2020: {'매출액': 2368069, '영업이익': 359938, '순이익': 264078},
            2021: {'매출액': 2796048, '영업이익': 516338, '순이익': 399074},
            2022: {'매출액': 3022314, '영업이익': 433766, '순이익': 556541},
            2023: {'매출액': 2589354, '영업이익': 65669,  '순이익': 154871},
            2024: {'매출액': 3000000, '영업이익': 320000, '순이익': 280000},
        },
        'analysis': (
            '삼성전자는 2022년 매출 302조원으로 역대 최대 실적을 기록한 이후 '
            '2023년 반도체 업황 악화로 영업이익이 전년 대비 84.9% 급감하였습니다.\n\n'
            'DRAM·NAND 메모리 가격 하락이 주요 원인이며, HBM(고대역폭 메모리) 및 '
            '파운드리 경쟁력 강화가 향후 수익성 회복의 핵심 과제입니다.\n\n'
            '2024년 하반기부터 반도체 업황 반등이 관측되며, AI 서버 수요 증가에 따른 '
            'HBM 공급 확대로 수익성 개선이 기대됩니다.'
        ),
    }
    result = run_report_agent(mock_state)
    print(f'PDF 생성 완료: {result["pdf_path"]}')
