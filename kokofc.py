import streamlit as st
import random
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 포지션 및 기본 설정
POS_CONFIG = {
    'PIVO (공격)': {'emoji': '🔱', 'label': '🔱 PIVO'},
    'ALA_L (좌윙)': {'emoji': '◀️', 'label': '◀️ ALA_L'},
    'ALA_R (우윙)': {'emoji': '▶️', 'label': '▶️ ALA_R'},
    'FIXO (수비)': {'emoji': '🛡️', 'label': '🛡️ FIXO'},
    'GOLEIRO (키퍼)': {'emoji': '🧤', 'label': '🧤 GOLEIRO'}
}
FIELD_POSITIONS = ['PIVO (공격)', 'ALA_L (좌윙)', 'ALA_R (우윙)', 'FIXO (수비)']
GK_POSITION = 'GOLEIRO (키퍼)'
ALL_POSITIONS = FIELD_POSITIONS + [GK_POSITION]

# 페이지 설정
st.set_page_config(page_title="⚽ KOKO FC 😈 라인업 매니저", layout="centered")

# --- 🎨 화면 제어 및 UI 최적화 CSS (레거시 코드 제거) ---
st.markdown("""
    <style>
    /* 모바일 브라우저 화면 전체 흔들림 차단 */
    html, body, [data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
        width: 100% !important;
    }
    
    /* 데스크탑의 st.columns(2) 설정창만 모바일에서 세로 전환 */
    @media (max-width: 768px) {
        .stExpander [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 16px !important;
        }
    }
    
    /* 명단 이름 폰트 스타일 최적화 */
    .stCheckbox p {
        font-size: 16px !important;
        font-weight: 800 !important;
        color: var(--text-color) !important;
    }
    
    /* 체크박스 해제 시 텍스트 흐려짐 및 취소선 효과 */
    .stCheckbox [aria-checked="false"] ~ div p {
        opacity: 0.35 !important;
        text-decoration: line-through !important;
    }
    
    /* 데스크톱에서 명단 영역이 지나치게 벌어지는 것 방지 */
    [data-testid="stMainBlock"] .stElementContainer:has(.stCheckbox) {
        max-width: 500px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ KOKO FC 😈 라인업 매니저")
st.caption("KOKO 화이팅!! 버그 제보 환영"\n"카톡 복사 추가, 기능 수정 중")

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
                    positions = [p.strip() for p in pos_str.split(',')]
                    positions = [p for p in positions if p in ALL_POSITIONS]
                else:
                    positions = ALL_POSITIONS.copy()
                if not positions: positions = ALL_POSITIONS.copy()
                players_dict[name] = positions
        return players_dict
    except Exception as e:
        st.error(f"구글 시트 로드 중 에러 발생: {e}")
        return {}

def save_players_to_db(players_dict):
    st.cache_data.clear()

if 'first_load_done' not in st.session_state:
    st.cache_data.clear()
    st.session_state.players_dict = load_players_from_db()
    st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}
    st.session_state.first_load_done = True

if 'players_dict' not in st.session_state: st.session_state.players_dict = {}
if 'lineups' not in st.session_state: st.session_state.lineups = None
if 'attendance' not in st.session_state: st.session_state.attendance = {}

for p in st.session_state.players_dict.keys():
    if p not in st.session_state.attendance:
        st.session_state.attendance[p] = True

# --- 🎯 희망 포지션 관리 및 삭제 다이얼로그 ---
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
            if player_name in st.session_state.attendance: del st.session_state.attendance[player_name]
            save_players_to_db(st.session_state.players_dict)
            st.rerun()

# --- ⚙️ 설정창 및 선수 등록 섹션 ---
with st.expander("⚙️ 설정 및 선수 등록 (터치해서 열기)", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.write("**① 경기 설정**")
            total_quarters = st.number_input("오늘 경기 쿼터 수 입력", min_value=1, max_value=12, value=7)
            st.write("") 
            if st.button("🔄 구글 시트 수동 새로고침", use_container_width=True):
                st.cache_data.clear()
                st.session_state.players_dict = load_players_from_db()
                st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}
                st.success("구글 시트에서 명단을 다시 불러왔습니다!")
                st.rerun()
    with col2:
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
                            save_players_to_db(st.session_state.players_dict)
                            st.success(f"'{name}' 선수가 명단에 등록되었습니다!")
                            st.rerun()

# 참여 명단 출력
st.write(f"### 👥 전체 명단 ({len(st.session_state.players_dict)}명)")
if st.session_state.players_dict:
    TAG_STYLES = {
        'PIVO (공격)': 'background-color: rgba(254, 226, 226, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3);', 
        'ALA_L (좌윙)': 'background-color: rgba(224, 242, 254, 0.15); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.3);', 
        'ALA_R (우윙)': 'background-color: rgba(254, 243, 199, 0.15); color: #FBBF24; border: 1px solid rgba(251, 191, 36, 0.3);', 
        'FIXO (수비)': 'background-color: rgba(220, 252, 231, 0.15); color: #4ADE80; border: 1px solid rgba(74, 222, 128, 0.3);', 
        'GOLEIRO (키퍼)': 'background-color: rgba(243, 244, 246, 0.15); color: #9CA3AF; border: 1px solid rgba(156, 163, 175, 0.3);' 
    }

    with st.container(border=True):
        for player in list(st.session_state.players_dict.keys()):
            positions = st.session_state.players_dict[player]
            is_active = st.session_state.attendance.get(player, True)
            
            tag_htmls = []
            for p in positions:
                if p in POS_CONFIG:
                    label = POS_CONFIG[p]['label']
                    tag_htmls.append(f"<span style='padding: 2px 6px; margin-right: 4px; border-radius: 6px; font-size: 11px; font-weight: 600; white-space: nowrap; {TAG_STYLES.get(p, '')}'>{label}</span>")
            tags_inline = "".join(tag_htmls)
            
            # 1. 순정 체크박스로 체크 처리
            selected = st.checkbox(f"🏃 {player}", value=is_active, key=f"att_v15_{player}")
            st.session_state.attendance[player] = selected
            
            # 2. 체크박스 하단 태그 배치 영역
            st.write(
                f"""<div style='padding-left: 28px; margin-top: 2px; margin-bottom: 6px; opacity: {1.0 if selected else 0.4};'>
                    <div style='display: flex; flex-wrap: wrap; gap: 4px; align-items: center;'>
                        {tags_inline}
                    </div>
                </div>""", 
                unsafe_allow_html=True
            )
            
            # 3. 미니멀 투명 슬림 버튼 스타일로 이름 하단 배치 (타협안 안착)
            if st.button(f"⚙️ 포지션 설정/선수 삭제", key=f"edit_btn_{player}", use_container_width=True):
                edit_position_dialog(player)
            
            st.write("<div style='margin: 4px 0; border-bottom: 1px dashed var(--secondary-background-color);'></div>", unsafe_allow_html=True)
else:
    st.info("등록된 선수가 없습니다.")
    
st.markdown("---")

# 알고리즘 (동일)
def generate_fair_lineups(players_pool, attendance_dict, total_q):
    active_players = [p for p, att in attendance_dict.items() if att and p in players_pool]
    if len(active_players) < 5: return None
    lineups = {}
    field_counts = {name: 0 for name in active_players} 
    gk_counts = {name: 0 for name in active_players}    
    player_pos_history = {name: {pos: 0 for pos in FIELD_POSITIONS} for name in active_players}
    last_quarter_gk = None
    for q in range(1, total_q + 1):
        starters = {pos: None for pos in ALL_POSITIONS}
        remaining = active_players.copy()
        gk_candidates = [p for p in remaining if GK_POSITION in players_pool[p]]
        if not gk_candidates: gk_candidates = remaining.copy()
        if last_quarter_gk in gk_candidates and len(gk_candidates) > 1: gk_candidates.remove(last_quarter_gk)
        random.shuffle(gk_candidates)
        gk_candidates.sort(key=lambda name: gk_counts[name])
        chosen_gk = gk_candidates[0]
        starters[GK_POSITION] = chosen_gk
        gk_counts[chosen_gk] += 1  
        remaining.remove(chosen_gk)
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
        lineups[f"{q}쿼터"] = {
            "starters": [starters[pos] for pos in ALL_POSITIONS],
            "subs": remaining,
            "field_snapshot": field_counts.copy(),
            "gk_snapshot": gk_counts.copy(),
            "history_snapshot": {name: player_pos_history[name].copy() for name in active_players}
        }
    return lineups

# 버튼 무게감 카피 추가
st.write("")
st.caption("✨ 모든 인원의 출전 횟수와 포지션 밸런스를 고려하여 가장 공평한 라인업을 계산합니다.")
if st.button("🚀 KOKO FC 라인업 자동 생성", type="primary", use_container_width=True):
    active_count = sum(1 for att in st.session_state.attendance.values() if att)
    if active_count < 5: st.error("오늘 경기 참석자가 최소 5명 이상이어야 라인업을 짜 수 있습니다! 체크박스를 확인해주세요.")
    else: st.session_state.lineups = generate_fair_lineups(st.session_state.players_dict, st.session_state.attendance, total_quarters)

if st.session_state.lineups:
    st.write("## 📋 경기 라인업 결과")
    kakao_text = "⚽ KOKO FC 경기 라인업 ⚽\n\n"
    for quarter, data in st.session_state.lineups.items():
        kakao_text += f"-----[{quarter}]-----\n🔱 PIVO : {data['starters'][0] or '미지정'}\n◀️ ALA_L : {data['starters'][1] or '미지정'}\n▶️ ALA_R : {data['starters'][2] or '미정'}\n🛡️ FIXO : {data['starters'][3] or '미지정'}\n🧤 GOLEIRO : {data['starters'][4] or '미정'}\n\n"

    html_button_code = f"""<button onclick="copyToClipboard()" style="width: 100%; background-color: #FEE500; color: #191919; border: none; padding: 14px; font-size: 15px; font-weight: 600; border-radius: 12px; cursor: pointer; box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: background 0.2s;">💬 카카오톡 공유용 라인업 복사하기</button>
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
    st.components.v1.html(html_button_code, height=55)
    
    edited_data = []
    for quarter, data in st.session_state.lineups.items():
        row = {"쿼터": quarter}
        for idx, pos in enumerate(ALL_POSITIONS): row[POS_CONFIG[pos]['label']] = data["starters"][idx] or "미지정"
        edited_data.append(row)
        
    st.data_editor(
        edited_data, 
        use_container_width=True, 
        num_rows="fixed",
        disabled=["쿼터"],
        hide_index=True
    )
    
    # 통계 표 섹션 (구조 분리로 인덴트/f-string 버그 원천 해결)
    st.write("### 📊 최종 포지션별 상세 출전 통계")
    last_quarter = list(st.session_state.lineups.keys())[-1]
    final_fields = st.session_state.lineups[last_quarter]["field_snapshot"]
    final_gks = st.session_state.lineups[last_quarter]["gk_snapshot"]
    final_history = st.session_state.lineups[last_quarter]["history_snapshot"]
    
    stats_data = []
    for name in final_fields.keys():
        player_history = final_history[name]
        stats_data.append({
            "선수명": name, "🧤 GOLEIRO": f"{final_gks[name]}회", "🏃 필드": f"{final_fields[name]}회",
            "🔱 PIVO": f"{player_history['PIVO (공격)']}회", "◀️ ALA_L": f"{player_history['ALA_L (좌윙)']}회",
            "▶️ ALA_R": f"{player_history['ALA_R (우윙)']}회", "🛡️ FIXO": f"{player_history.get('🛡️ FIXO (수비)', player_history.get('FIXO (수비)', 0))}회"
        })
    df_stats = pd.DataFrame(stats_data)
    html_tbody = df_stats.to_html(index=False, header=False, classes='modern-table')
    tbody_content = html_tbody.split('<tbody>')[1].split('</tbody>')[0]
    
    table_css = """
    <style>
        .modern-table {
            width: 100%;
            min-width: 500px;
            border-collapse: separate !important;
            border-spacing: 0;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px;
            background-color: var(--background-color);
            color: var(--text-color);
            border: 1px solid rgba(0, 0, 0, 0.08) !important;
            border-radius: 12px;
            overflow: hidden;
        }
        @media (prefers-color-scheme: dark) {
            .modern-table { border: 1px solid rgba(255, 255, 255, 0.1) !important; }
        }
        .modern-table th {
            background-color: var(--secondary-background-color);
            color: var(--text-color);
            font-weight: 600;
            padding: 10px 4px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
            border-right: 1px solid rgba(0, 0, 0, 0.04) !important;
            text-align: center !important;
            white-space: nowrap;
        }
        .modern-table td {
            padding: 10px 4px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.04) !important;
            border-right: 1px solid rgba(0, 0, 0, 0.04) !important;
            text-align: center !important; 
            white-space: nowrap;
        }
        .modern-table th:last-child, .modern-table td:last-child { border-right: none !important; }
        .modern-table tr:last-child td { border-bottom: none !important; }
        .modern-table tr:hover { background-color: rgba(0,0,0,0.02); }
        .modern-table td:nth-child(1) {
            font-weight: 600;
            position: sticky;
            left: 0;
            background-color: var(--background-color);
            border-right: 1px solid rgba(0, 0, 0, 0.08) !important;
        }
        .modern-table td:nth-child(3) {
            background-color: rgba(34, 197, 94, 0.06) !important;
            color: #22C55E !important;
            font-weight: 700;
        }
    </style>
    """

    table_body = f"""
    <div style="overflow-x: auto; -webkit-overflow-scrolling: touch; width: 100%; margin-top: 10px; border-radius: 12px; border: 1px solid rgba(0,0,0,0.08); contain: content;">
        <table class="modern-table">
            <thead>
                <tr>
                    <th rowspan="2" style="vertical-align: middle;">선수명</th>
                    <th rowspan="2" style="vertical-align: middle;">🧤 GOLEIRO</th>
                    <th rowspan="2" style="vertical-align: middle;">🏃 필드</th>
                    <th colspan="4" class="main-header">상세 (필드 포지션별 출전)</th>
                </tr>
                <tr>
                    <th>🔱 PIVO</th>
                    <th>◀️ ALA_L</th>
                    <th>▶️ ALA_R</th>
                    <th>🛡️ FIXO</th>
                </tr>
            </thead>
            <tbody>{tbody_content}</tbody>
        </table>
    </div>
    """
    st.html(table_css + table_body)
