import streamlit as st
import random
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 상수 정의
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

st.set_page_config(page_title="⚽ KOKO FC 😈 라인업 매니저", layout="centered")

# 모바일 화면 최적화용 CSS 추가
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { overflow-x: hidden !important; width: 100% !important; }
    .stCheckbox p { font-size: 15px !important; font-weight: 700 !important; }
    .stCheckbox [aria-checked="false"] ~ div p { opacity: 0.35 !important; text-decoration: line-through !important; }
    
    /* 팝오버 버튼 스타일을 조금 더 컴팩트하게 */
    div[data-testid="stPopover"] button {
        padding: 2px 8px !important;
        background-color: transparent !important;
        border: 1px solid rgba(0,0,0,0.1) !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ KOKO FC 😈 라인업 매니저")

# 데이터베이스 로드 및 세션 상태 초기화 (기존 로직 유지)
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

# 설정 및 선수 등록 단축 (익스팬더)
with st.expander("⚙️ 설정 및 선수 등록", expanded=False):
    total_quarters = st.number_input("오늘 경기 쿼터 수 입력", min_value=1, max_value=12, value=7)
    if st.button("🔄 구글 시트 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.session_state.players_dict = load_players_from_db()
        st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}
        st.rerun()

# 👥 5. 명단 출력 섹션 (st.popover 도입으로 모바일 완벽 대응)
st.markdown(f"### 👥 참석 명단 체크 ({sum(1 for v in st.session_state.attendance.values() if v)}명)")
if st.session_state.players_dict:
    TAG_STYLES = {
        'PIVO (공격)': 'background-color: rgba(239, 68, 68, 0.1); color: #EF4444;', 
        'ALA_L (좌윙)': 'background-color: rgba(56, 189, 248, 0.1); color: #38BDF8;', 
        'ALA_R (우윙)': 'background-color: rgba(251, 191, 36, 0.1); color: #FBBF24;', 
        'FIXO (수비)': 'background-color: rgba(74, 222, 128, 0.1); color: #4ADE80;', 
        'GOLEIRO (키퍼)': 'background-color: rgba(156, 163, 175, 0.1); color: #9CA3AF;' 
    }

    with st.container(border=True):
        for player in list(st.session_state.players_dict.keys()):
            is_active = st.session_state.attendance.get(player, True)
            
            # 모바일에서도 절대 깨지지 않는 Row 레이아웃 구성
            col1, col2 = st.columns([4, 1])
            with col1:
                selected = st.checkbox(f"🏃 {player}", value=is_active, key=f"att_v16_{player}")
                st.session_state.attendance[player] = selected
                
                # 포지션 태그 생성
                positions = st.session_state.players_dict[player]
                tag_htmls = [f"<span style='padding: 1px 4px; margin-right: 3px; border-radius: 4px; font-size: 10px; font-weight: 600; {TAG_STYLES.get(p, '')}'>{POS_CONFIG[p]['label']}</span>" for p in positions if p in POS_CONFIG]
                st.markdown(f"<div style='padding-left: 28px; margin-top: -6px; margin-bottom: 8px; opacity: {1.0 if selected else 0.3};'>{''.join(tag_htmls)}</div>", unsafe_allow_html=True)
            
            with col2:
                # 🛠️ 버튼을 누르면 그 자리에 레이어가 뜨므로 모바일 우측 정렬 완벽 유지!
                with st.popover("⚙️", use_container_width=True):
                    st.write(f"**{player} 설정**")
                    new_wishes = st.multiselect(
                        "희망 포지션", options=ALL_POSITIONS, 
                        default=[p for p in st.session_state.players_dict[player] if p in ALL_POSITIONS],
                        format_func=lambda x: POS_CONFIG[x]['label'], key=f"pop_sel_{player}"
                    )
                    if st.button("💾 저장", key=f"pop_save_{player}", use_container_width=True, type="primary"):
                        st.session_state.players_dict[player] = new_wishes if new_wishes else ALL_POSITIONS.copy()
                        st.rerun()
                    if st.button("🗑️ 삭제", key=f"pop_del_{player}", use_container_width=True):
                        del st.session_state.players_dict[player]
                        if player in st.session_state.attendance: del st.session_state.attendance[player]
                        st.rerun()
            
            st.markdown("<div style='margin: 1px 0; border-bottom: 1px dashed rgba(0,0,0,0.05);'></div>", unsafe_allow_html=True)

# 6. 라인업 생성 알고리즘 함수
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
            "field_snapshot": field_counts.copy(),
            "gk_snapshot": gk_counts.copy(),
            "history_snapshot": {name: player_pos_history[name].copy() for name in active_players}
        }
        last_quarter_gk = chosen_gk
    return lineups

if st.button("🚀 KOKO FC 라인업 자동 생성", type="primary", use_container_width=True):
    active_count = sum(1 for att in st.session_state.attendance.values() if att)
    if active_count < 5: st.error("참석 인원이 부족합니다.")
    else: st.session_state.lineups = generate_fair_lineups(st.session_state.players_dict, st.session_state.attendance, total_quarters)

# 7. 결과 및 통계 (안정성 강화)
if st.session_state.lineups:
    st.markdown("### 📋 경기 라인업 결과")
    
    edited_data = []
    for quarter, data in st.session_state.lineups.items():
        row = {"쿼터": quarter}
        for idx, pos in enumerate(ALL_POSITIONS): 
            row[POS_CONFIG[pos]['label']] = data["starters"][idx] or "미지정"
        edited_data.append(row)
        
    updated_rows = st.data_editor(edited_data, use_container_width=True, num_rows="fixed", disabled=["쿼터"], hide_index=True)
    
    # 동적 카톡 복사 시스템
    kakao_text = "⚽ KOKO FC 경기 라인업 ⚽\\n\\n"
    for r in updated_rows:
        kakao_text += f"-----[{r['쿼터']}]-----\\n"
        for pos in ALL_POSITIONS:
            lbl = POS_CONFIG[pos]['label']
            kakao_text += f"{lbl} : {r.get(lbl, '미정')}\\n"
        kakao_text += "\\n"

    html_button_code = f"""<button onclick="copyToClipboard()" style="width: 100%; background-color: #FEE500; color: #191919; border: none; padding: 12px; font-size: 14px; font-weight: 700; border-radius: 8px; cursor: pointer; margin-bottom: 15px;">💬 카카오톡 공유용 라인업 복사하기</button>
    <script>
    function copyToClipboard() {{
        var textToCopy = `{kakao_text}`;
        var textArea = document.createElement("textarea");
        textArea.value = textToCopy; textArea.style.position = "fixed";
        document.body.appendChild(textArea); textArea.select();
        try {{ if(document.execCommand('copy')) alert('📋 카톡 공유 텍스트가 복사되었습니다!'); }} 
        catch (err) {{ navigator.clipboard.writeText(textToCopy).then(function() {{ alert('📋 카톡 공유 텍스트가 복사되었습니다!'); }}); }}
        document.body.removeChild(textArea);
    }}
    </script>"""
    st.components.v1.html(html_button_code, height=45)
    
    # 📊 8. 통계부 출력 (Key 에러 완벽 방어 처리된 Pandas 매핑)
    st.markdown("### 📊 포지션별 상세 출전 통계")
    last_quarter = list(st.session_state.lineups.keys())[-1]
    final_fields = st.session_state.lineups[last_quarter]["field_snapshot"]
    final_gks = st.session_state.lineups[last_quarter]["gk_snapshot"]
    final_history = st.session_state.lineups[last_quarter]["history_snapshot"]
    
    stats_data = []
    for name in final_fields.keys():
        player_history = final_history.get(name, {})
        stats_data.append({
            "선수명": name, 
            "🧤 GK": f"{final_gks.get(name, 0)}회", 
            "🏃 필드": f"{final_fields.get(name, 0)}회",
            "🔱 PIVO": f"{player_history.get('PIVO (공격)', 0)}회", 
            "◀️ ALA_L": f"{player_history.get('ALA_L (좌윙)', 0)}회",
            "▶️ ALA_R": f"{player_history.get('ALA_R (우윙)', 0)}회", 
            "🛡️ FIXO": f"{player_history.get('FIXO (수비)', 0)}회"
        })
    
    df_stats = pd.DataFrame(stats_data)
    
    # 안전하게 HTML 내부 파싱 진행
    html_table = df_stats.to_html(index=False, classes='modern-table')
    
    table_css = """<style>
        .modern-table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: center; color: var(--text-color); }
        .modern-table th, .modern-table td { padding: 8px 4px; border: 1px solid rgba(128,128,128,0.2); }
        .modern-table th { background-color: var(--secondary-background-color); font-weight: 600; }
        .modern-table td:nth-child(1) { font-weight: bold; position: sticky; left:0; background: var(--background-color); border-right: 2px solid rgba(128,128,128,0.4); }
    </style>"""
    
    st.markdown(table_css + f'<div style="overflow-x: auto; width: 100%; border-radius: 8px;">{html_table}</div>', unsafe_allow_html=True)
