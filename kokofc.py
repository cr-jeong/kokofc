import streamlit as st
import random
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from PIL import Image

# [1. 기본 설정 및 포지션 딕셔너리]
POS_CONFIG = {
    'PIVO (공격)': {'emoji': '🔱', 'label': '🔱 PIVO', 'color': '#EF4444', 'bg': 'rgba(254, 226, 226, 0.15)', 'border': 'rgba(239, 68, 68, 0.3)'},
    'ALA_L (좌윙)': {'emoji': '◀️', 'label': '◀️ ALA_L', 'color': '#38BDF8', 'bg': 'rgba(224, 242, 254, 0.15)', 'border': 'rgba(56, 189, 248, 0.3)'},
    'ALA_R (우윙)': {'emoji': '▶️', 'label': '▶️ ALA_R', 'color': '#FBBF24', 'bg': 'rgba(254, 243, 199, 0.15)', 'border': 'rgba(251, 191, 36, 0.3)'},
    'FIXO (수비)': {'emoji': '🛡️', 'label': '🛡️ FIXO', 'color': '#4ADE80', 'bg': 'rgba(220, 252, 231, 0.15)', 'border': 'rgba(74, 222, 128, 0.3)'},
    'GOLEIRO (키퍼)': {'emoji': '🧤', 'label': '🧤 GOLEIRO', 'color': '#9CA3AF', 'bg': 'rgba(243, 244, 246, 0.15)', 'border': 'rgba(156, 163, 175, 0.3)'}
}
FIELD_POSITIONS = ['PIVO (공격)', 'ALA_L (좌윙)', 'ALA_R (우윙)', 'FIXO (수비)']
GK_POSITION = 'GOLEIRO (키퍼)'
ALL_POSITIONS = FIELD_POSITIONS + [GK_POSITION]

st.set_page_config(page_title="⚽ KOKO FC 😈 라인업 매니저", layout="centered")

# [2. 토스 & 카카오 스타일 최적화 CSS 인젝션]
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
        width: 100% !important;
        background-color: var(--background-color);
    }
    
    /* 컴포넌트 라운딩 및 카드 스타일 디자인 */
    [data-testid="stExpander"] {
        border-radius: 16px !important;
        border: 1px solid rgba(0, 0, 0, 0.05) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02) !important;
        background-color: var(--background-color) !important;
    }
    @media (prefers-color-scheme: dark) {
        [data-testid="stExpander"] {
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        }
    }
    
    /* 선수 등록 Form의 기본 테두리 및 그림자 흔적 완전 박멸 */
    .stForm {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
        padding: 0 !important;
    }
    
    /* 메인 설정창(Expander) 타이틀 글자 크기 15px로 최적화 */
    [data-testid="stExpander"] details summary p {
        font-size: 15px !important;
        font-weight: 700 !important;
        color: var(--text-color) !important;
    }
    
    /* 명단 체크박스 테두리 UI 정리 */
    div:has(> [data-testid="stCheckbox"]) {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    [data-testid="stCheckbox"] {
        border: none !important;
        padding: 4px 0 !important;
    }
    .stCheckbox p {
        font-size: 16px !important;
        font-weight: 700 !important;
    }
    .stCheckbox [aria-checked="false"] ~ div p {
        opacity: 0.3 !important;
        text-decoration: line-through !important;
    }
    
    @media (max-width: 768px) {
        .stExpander [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 16px !important;
        }
    }
    
    /* 가로 스크롤 반응형 테이블 최적화 */
    .toss-table-container {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        width: 100%;
        margin: 16px 0;
        border-radius: 16px;
        border: 1px solid rgba(0, 0, 0, 0.06);
        box-shadow: 0 4px 166px rgba(0, 0, 0, 0.02);
    }
    @media (prefers-color-scheme: dark) {
        .toss-table-container { border: 1px solid rgba(255, 255, 255, 0.08); }
    }
    
    .toss-table {
        width: 100%;
        min-width: 600px;
        border-collapse: collapse;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 13px;
        text-align: center;
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    .toss-table th, .toss-table td {
        padding: 10px 8px;
        white-space: nowrap;
        position: relative;
        z-index: 1;
    }
    
    .toss-table th {
        color: var(--text-color);
        font-weight: 600;
        border-bottom: 1px solid rgba(0, 0, 0, 0.06);
    }
    
    .toss-table td { border-bottom: 1px solid rgba(0, 0, 0, 0.04); }
    .toss-table tr:last-child td { border-bottom: none; }
    .toss-table tr:hover { background-color: rgba(0, 0, 0, 0.015); }
    
    /* 클래스 기반 첫 번째 열 절대 방어벽 */
    .sticky-col {
        position: sticky !important;
        left: 0 !important;
        z-index: 99999 !important;
        font-weight: 600;
        box-shadow: 2px 0 8px rgba(0, 0, 0, 0.06);
    }
    
    /* 테마별 테이블 라인 및 스티키 열 불투명 배경색 지정 */
    @media (prefers-color-scheme: dark) {
        .toss-table th { background-color: #1a1c23; }
        .toss-table td { background-color: #0e1117; }
        th.sticky-col { background-color: #1a1c23 !important; }
        td.sticky-col { background-color: #0e1117 !important; }
        .toss-table th, .toss-table td { border-right: 1px solid rgba(255, 255, 255, 0.04); }
        .toss-table th:last-child, .toss-table td:last-child { border-right: none; }
    }
    @media (prefers-color-scheme: light) {
        .toss-table th { background-color: #f0f2f6; }
        .toss-table td { background-color: #ffffff; }
        th.sticky-col { background-color: #f0f2f6 !important; }
        td.sticky-col { background-color: #ffffff !important; }
        .toss-table th, .toss-table td { border-right: 1px solid rgba(0, 0, 0, 0.04); }
        .toss-table th:last-child, .toss-table td:last-child { border-right: none; }
    }
    </style>
""", unsafe_allow_html=True)

# [3. 타이틀 디자인 최적화: 사진+제목 가로 정렬]
col1, col2 = st.columns([1, 6])

with col1:
    try:
        img = Image.open("koko_logo.png")
        st.image(img, width=65)
    except FileNotFoundError:
        st.title("⚽")

with col2:
    st.markdown("<h1 style='margin: 0; padding-top: 5px; font-size: 40px;'>⚽ KOKO FC 😈 라인업 매니저</h1>", unsafe_allow_html=True)
    st.caption("KOKO 화이팅!! 버그 제보 환영")

# [4. 구글 시트 연동 및 데이터 로드]
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def load_players_from_db():
    try:
        df = conn.read(header=None, ttl=300)
        if df.empty: return {}
        players_dict = {}
        for _, row in df.iterrows():
            if len(row) >= 1 and pd.notna(row.iloc[0]):
                name = str(row.iloc[0]).strip()
                if not name or name.lower() == 'nan': continue
                pos_str = str(row.iloc[1]).strip() if len(row) >= 2 and pd.notna(row.iloc[1]) else ""
                if pos_str and pos_str.lower() != 'nan':
                    positions = [p.strip() for p in pos_str.split(',') if p.strip() in ALL_POSITIONS]
                else:
                    positions = ALL_POSITIONS.copy()
                players_dict[name] = positions if positions else ALL_POSITIONS.copy()
        return players_dict
    except Exception as e:
        st.error(f"구글 시트 로드 중 에러 발생: {e}")
        return {}

if 'players_dict' not in st.session_state:
    st.cache_data.clear()
    st.session_state.players_dict = load_players_from_db()
    st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}
    st.session_state.lineups = None  # 다시 원래의 안전한 내부 딕셔너리 구조로 롤백

for p in st.session_state.players_dict.keys():
    if p not in st.session_state.attendance:
        st.session_state.attendance[p] = True

# [5. 선수 관리 팝업 다이얼로그]
@st.dialog("🎯 선수 설정 및 포지션 관리")
def edit_position_dialog(player_name):
    st.write(f"🏃 **{player_name}** 선수의 설정을 변경합니다.")
    current_wishes = st.session_state.players_dict[player_name]
    new_wishes = st.multiselect(
        "희망 포지션 (복수 선택 가능)",
        options=ALL_POSITIONS,
        default=[p for p in current_wishes if p in ALL_POSITIONS],
        format_func=lambda x: POS_CONFIG[x]['label']
    )
    
    st.write("")
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        if st.button("💾 변경사항 저장", use_container_width=True, type="primary"):
            st.session_state.players_dict[player_name] = new_wishes if new_wishes else ALL_POSITIONS.copy()
            st.success(f"{player_name} 선수의 정보가 수정되었습니다!")
            st.rerun()
    with d_col2:
        if st.button("🗑️ 선수 삭제하기", use_container_width=True, type="secondary"):
            del st.session_state.players_dict[player_name]
            st.session_state.attendance.pop(player_name, None)
            st.cache_data.clear()
            st.rerun()

# [6. 경기 설정 및 신규 등록]
with st.expander("⚙️ 설정 및 선수 등록 (터치해서 열기)", expanded=False):
    with st.container(border=True):
        st.write("**① 경기 설정**")
        total_quarters = st.number_input("오늘 경기 쿼터 수 입력", min_value=1, max_value=12, value=7)
        st.write("") 
        if st.button("🔄 구글 시트 수동 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.session_state.players_dict = load_players_from_db()
            st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}
            st.session_state.lineups = None
            st.success("구글 시트에서 명단을 다시 불러왔습니다!")
            st.rerun()

    st.write("<div style='margin: 8px 0;'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.write("**② 선수 등록 (실시간 반영)**")
        with st.form(key="player_add_form", clear_on_submit=True, border=False):
            name_input = st.text_input("1. 선수 이름 입력", placeholder="예: 홍길동(용병)")
            wished_input = st.multiselect("2. 희망 포지션 선택 (생략 가능)", options=ALL_POSITIONS, format_func=lambda x: POS_CONFIG[x]['label'])
            st.write("")
            if st.form_submit_button("🏃 선수 등록하기", use_container_width=True):
                name = name_input.strip()
                if name:
                    if name in st.session_state.players_dict: 
                        st.warning(f"'{name}' 선수는 이미 등록되어 있습니다.")
                    else:
                        st.session_state.players_dict[name] = wished_input if wished_input else ALL_POSITIONS.copy()
                        st.session_state.attendance[name] = True
                        st.cache_data.clear()
                        st.success(f"'{name}' 선수가 명단에 등록되었습니다!")
                        st.rerun()

# [7. 출석 및 명단 관리 UI]
st.markdown(f"### 👥 전체 명단 ({len(st.session_state.players_dict)}명)")
if st.session_state.players_dict:
    with st.container(border=True):
        for player in list(st.session_state.players_dict.keys()):
            positions = st.session_state.players_dict[player]
            is_active = st.session_state.attendance.get(player, True)
            
            tag_htmls = [
                f"<span style='padding: 3px 8px; margin-right: 4px; border-radius: 8px; font-size: 11px; font-weight: 600; white-space: nowrap; background-color: {POS_CONFIG[p]['bg']}; color: {POS_CONFIG[p]['color']}; border: 1px solid {POS_CONFIG[p]['border']};'>{POS_CONFIG[p]['label']}</span>"
                for p in positions if p in POS_CONFIG
            ]
            tags_inline = "".join(tag_htmls)
            
            selected = st.checkbox(f"🏃 {player}", value=is_active, key=f"att_v15_{player}")
            st.session_state.attendance[player] = selected
            
            st.write(
                f"""<div style='padding-left: 28px; margin-top: 2px; margin-bottom: 8px; opacity: {1.0 if selected else 0.35};'>
                    <div style='display: flex; flex-wrap: wrap; gap: 4px; align-items: center;'>
                        {tags_inline}
                    </div>
                </div>""", 
                unsafe_allow_html=True
            )
            
            if st.button(f"⚙️ 포지션 설정/선수 삭제", key=f"edit_btn_{player}", use_container_width=True):
                edit_position_dialog(player)
            
            st.write("<div style='margin: 4px 0; border-bottom: 1px dashed var(--secondary-background-color);'></div>", unsafe_allow_html=True)
else:
    st.info("등록된 선수가 없습니다.")
    
st.markdown("---")

# [8. 균등 분배 알고리즘 핵심 엔진]
def generate_fair_lineups(players_pool, attendance_dict, total_q):
    active_players = [p for p, att in attendance_dict.items() if att and p in players_pool]
    if len(active_players) < 5: return None
    
    lineups_dict = {}
    field_counts = {name: 0 for name in active_players} 
    gk_counts = {name: 0 for name in active_players}    
    player_pos_history = {name: {pos: 0 for pos in FIELD_POSITIONS} for name in active_players}
    last_quarter_gk = None
    
    for q in range(1, total_q + 1):
        starters = {pos: None for pos in ALL_POSITIONS}
        remaining = active_players.copy()
        
        # 골키퍼 배정
        gk_candidates = [p for p in remaining if GK_POSITION in players_pool[p]]
        if not gk_candidates: gk_candidates = remaining.copy()
        if last_quarter_gk in gk_candidates and len(gk_candidates) > 1: gk_candidates.remove(last_quarter_gk)
        random.shuffle(gk_candidates)
        gk_candidates.sort(key=lambda name: gk_counts[name])
        chosen_gk = gk_candidates[0]
        starters[GK_POSITION] = chosen_gk
        gk_counts[chosen_gk] += 1  
        remaining.remove(chosen_gk)
        
        # 필드 포지션 균등 배정
        random.shuffle(remaining)
        remaining.sort(key=lambda name: field_counts[name])
        shuffled_positions = FIELD_POSITIONS.copy()
        random.shuffle(shuffled_positions)
        for pos in shuffled_positions:
            wished_candidates = [p for p in remaining if pos in players_pool[p]]
            if wished_candidates: chosen_player = wished_candidates[0]
            else:
                remaining.sort(key=lambda name: (field_counts[name], player_pos_history[name][pos]))
                chosen_player = remaining[0]
            starters[pos] = chosen_player
            remaining.remove(chosen_player)
            field_counts[chosen_player] += 1
            player_pos_history[chosen_player][pos] += 1
            
        lineups_dict[q] = starters
        last_quarter_gk = chosen_gk
        
    return lineups_dict

st.write("")
st.caption("✨ 모든 인원의 출전 횟수와 포지션 밸런스를 고려합니다.")
if st.button("🚀 KOKO FC 라인업 자동 생성", type="primary", use_container_width=True):
    active_count = sum(1 for att in st.session_state.attendance.values() if att)
    if active_count < 5: st.error("오늘 경기 참석자가 최소 5명 이상이어야 라인업을 짜 수 있습니다!")
    else: 
        st.session_state.lineups = generate_fair_lineups(st.session_state.players_dict, st.session_state.attendance, total_quarters)

# [9. 📋 안전한 원래 방식의 결과 출력 및 공유 섹션]
if st.session_state.lineups:
    st.markdown("### 📋 경기 라인업 결과")
    
    tbody_rows = ""
    kakao_text = "⚽ KOKO FC 경기 라인업 ⚽\\n\\n"
    
    for q, roster in st.session_state.lineups.items():
        pivo, ala_l, ala_r, fixo, gk = roster['PIVO (공격)'], roster['ALA_L (좌윙)'], roster['ALA_R (우윙)'], roster['FIXO (수비)'], roster['GOLEIRO (키퍼)']
        
        # HTML 가독성 높은 읽기 전용 테이블 누적
        tbody_rows += f"""
        <tr>
            <td class="sticky-col">{q}쿼터</td>
            <td>{pivo}</td>
            <td>{ala_l}</td>
            <td>{ala_r}</td>
            <td>{fixo}</td>
            <td>{gk}</td>
        </tr>
        """
        # 카톡 복사용 텍스트 포맷 빌드
        kakao_text += f"-----[{q}쿼터]-----\\n🔱 PIVO : {pivo}\\n◀️ ALA_L : {ala_l}\\n▶️ ALA_R : {ala_r}\\n🛡️ FIXO : {fixo}\\n🧤 GOLEIRO : {gk}\\n\\n"

    main_table_html = f"""
    <div class="toss-table-container">
        <table class="toss-table">
            <thead>
                <tr>
                    <th class="sticky-col">쿼터</th>
                    <th><span style="color:{POS_CONFIG['PIVO (공격)']['color']}">🔱 PIVO</span></th>
                    <th><span style="color:{POS_CONFIG['ALA_L (좌윙)']['color']}">◀️ ALA_L</span></th>
                    <th><span style="color:{POS_CONFIG['ALA_R (우윙)']['color']}">▶️ ALA_R</span></th>
                    <th><span style="color:{POS_CONFIG['FIXO (수비)']['color']}">🛡️ FIXO</span></th>
                    <th><span style="color:{POS_CONFIG['GOLEIRO (키퍼)']['color']}">🧤 GOLEIRO</span></th>
                </tr>
            </thead>
            <tbody>{tbody_rows}</tbody>
        </table>
    </div>
    """
    st.html(main_table_html)

    # 카카오톡 복사 전용 클립보드 버튼 디자인
    html_button_code = f"""<button onclick="copyToClipboard()" style="width: 100%; background-color: #FEE500; color: #191919; border: none; padding: 14px; font-size: 15px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, sans-serif; border-radius: 14px; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.02); transition: background 0.2s; margin-top: 5px; margin-bottom: 20px;">💬 카카오톡 공유용 라인업 복사하기</button>
<script>
function copyToClipboard() {{
    var textToCopy = `{kakao_text}`;
    var textArea = document.createElement("textarea");
    textArea.value = textToCopy; textArea.style.position = "fixed";
    document.body.appendChild(textArea); textArea.select();
    try {{ if(document.execCommand('copy')) alert('📋 [KOKO FC] 카톡 공유용 텍스트가 복사되었습니다!'); }} 
    catch (err) {{ navigator.clipboard.writeText(textToCopy).then(function() {{ alert('📋 [KOKO FC] 카톡 공유용 텍스트가 복사되었습니다!'); }}); }}
    document.body.removeChild(textArea);
}}
</script>"""
    st.components.v1.html(html_button_code, height=65)
    
    # [10. 📊 통계 테이블 세션]
    st.markdown("### 📊 포지션별 상세 출전 통계")
    
    active_players_current = [p for p, att in st.session_state.attendance.items() if att and p in st.session_state.players_dict]
    stats_data = {
        name: {"GK": 0, "필드 합계": 0, "PIVO": 0, "ALA_L": 0, "ALA_R": 0, "FIXO": 0} 
        for name in active_players_current
    }
    
    for q, roster in st.session_state.lineups.items():
        pivo, ala_l, ala_r, fixo, gk = roster['PIVO (공격)'], roster['ALA_L (좌윙)'], roster['ALA_R (우윙)'], roster['FIXO (수비)'], roster['GOLEIRO (키퍼)']
        
        if gk in stats_data: stats_data[gk]["GK"] += 1
        if pivo in stats_data: 
            stats_data[pivo]["PIVO"] += 1
            stats_data[pivo]["필드 합계"] += 1
        if ala_l in stats_data: 
            stats_data[ala_l]["ALA_L"] += 1
            stats_data[ala_l]["필드 합계"] += 1
        if ala_r in stats_data: 
            stats_data[ala_r]["ALA_R"] += 1
            stats_data[ala_r]["필드 합계"] += 1
        if fixo in stats_data: 
            stats_data[fixo]["FIXO"] += 1
            stats_data[fixo]["필드 합계"] += 1

    stats_tbody_rows = ""
    for name, s in stats_data.items():
        stats_tbody_rows += f"""
        <tr>
            <td class="sticky-col">{name}</td>
            <td>{s['GK']}회</td>
            <td style="background-color: rgba(34, 197, 94, 0.05); color: #22C55E; font-weight: 700;">{s['필드 합계']}회</td>
            <td>{s['PIVO']}회</td>
            <td>{s['ALA_L']}회</td>
            <td>{s['ALA_R']}회</td>
            <td>{s['FIXO']}회</td>
        </tr>
        """

    stats_table_html = f"""
    <div class="toss-table-container">
        <table class="toss-table">
            <thead>
                <tr>
                    <th rowspan="2" class="sticky-col" style="vertical-align: middle;">선수명</th>
                    <th rowspan="2" style="vertical-align: middle;"><span style="color:{POS_CONFIG['GOLEIRO (키퍼)']['color']}">🧤 GK</span></th>
                    <th rowspan="2" style="vertical-align: middle;">🏃 필드 합계</th>
                    <th colspan="4" style="border-bottom: 1px solid rgba(0,0,0,0.06);">포지션별 출전 상세</th>
                </tr>
                <tr>
                    <th><span style="color:{POS_CONFIG['PIVO (공격)']['color']}">🔱 PIVO</span></th>
                    <th><span style="color:{POS_CONFIG['ALA_L (좌윙)']['color']}">◀️ ALA_L</span></th>
                    <th><span style="color:{POS_CONFIG['ALA_R (우윙)']['color']}">▶️ ALA_R</span></th>
                    <th><span style="color:{POS_CONFIG['FIXO (수비)']['color']}">🛡️ FIXO</span></th>
                </tr>
            </thead>
            <tbody>{stats_tbody_rows}</tbody>
        </table>
    </div>
    """
    st.html(stats_table_html)
