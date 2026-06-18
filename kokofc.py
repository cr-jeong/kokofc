import streamlit as st
import random
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 포지션 및 기본 설정
POS_CONFIG = {
    'PIVO (공격)': {'emoji': '🔥', 'label': '🔥 PIVO (공격)'},
    'ALA_L (좌윙)': {'emoji': '⚡', 'label': '⚡ ALA_L (좌윙)'},
    'ALA_R (우윙)': {'emoji': '✨', 'label': '✨ ALA_R (우윙)'},
    'FIXO (수비)': {'emoji': '🛡️', 'label': '🛡️ FIXO (수비)'},
    'GOLEIRO (키퍼)': {'emoji': '🧤', 'label': '🧤 GOLEIRO (키퍼)'}
}
FIELD_POSITIONS = ['PIVO (공격)', 'ALA_L (좌윙)', 'ALA_R (우윙)', 'FIXO (수비)']
GK_POSITION = 'GOLEIRO (키퍼)'
ALL_POSITIONS = FIELD_POSITIONS + [GK_POSITION]

# 페이지 설정
st.set_page_config(page_title="⚽ KOKO FC 😈 라인업 매니저", layout="centered")
st.title("⚽ KOKO FC 😈 라인업 매니저")
st.caption("KOKO 화이팅!! 버그 제보 환영")
st.caption("참석 체크 + 앱 내 실시간 포지션 수정 기능 추가 완료!")

# 구글 스프레딧시트 연결 초기화
conn = st.connection("gsheets", type=GSheetsConnection)

def load_players_from_db():
    try:
        # 💡 header=None 추가 및 ttl=0으로 설정하여 캐시 문제 방지
        df = conn.read(header=None, ttl=0)
        if df.empty:
            return {}
            
        players_dict = {}
        for _, row in df.iterrows():
            if len(row) >= 1 and pd.notna(row.iloc[0]):
                name = str(row.iloc[0]).strip()
                if not name or name.lower() == 'nan':
                    continue
                
                pos_str = str(row.iloc[1]).strip() if len(row) >= 2 and pd.notna(row.iloc[1]) else ""
                
                if pos_str and pos_str.lower() != 'nan':
                    positions = [p.strip() for p in pos_str.split(',')]
                    positions = [p for p in positions if p in ALL_POSITIONS]
                else:
                    positions = ALL_POSITIONS.copy()
                
                if not positions:
                    positions = ALL_POSITIONS.copy()
                    
                players_dict[name] = positions
        return players_dict
    except Exception as e:
        # 오류 발생 시 화면에 원인 출력
        st.error(f"구글 시트 로드 중 에러 발생: {e}")
        return {}

def save_players_to_db(players_dict):
    st.cache_data.clear()

# ========================================================
# 💡 [핵심 수정] 앱 시작 시 구글 시트 원본 자동 로드 로직
# ========================================================
if 'first_load_done' not in st.session_state:
    st.cache_data.clear()  # 구글 시트 기존 캐시 초기화
    st.session_state.players_dict = load_players_from_db()  # 데이터 강제 로드
    st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}  # 출석부 초기화
    st.session_state.first_load_done = True

# 세션 상태 기본 변수 안전장치
if 'players_dict' not in st.session_state:
    st.session_state.players_dict = {}
if 'lineups' not in st.session_state:
    st.session_state.lineups = None
if 'attendance' not in st.session_state:
    st.session_state.attendance = {}

# 명단이 바뀔 때 출석부 상태 동기화
for p in st.session_state.players_dict.keys():
    if p not in st.session_state.attendance:
        st.session_state.attendance[p] = True

# 💡 포지션 수정을 위한 팝업창(Dialog) 정의
@st.dialog("🎯 희망 포지션 수정")
def edit_position_dialog(player_name):
    st.write(f"🏃 **{player_name}** 선수의 희망 포지션을 선택하세요.")
    st.caption("아무것도 선택하지 않으면 '모든 포지션 가능'으로 설정됩니다.")
    
    current_wishes = st.session_state.players_dict[player_name]
    
    new_wishes = st.multiselect(
        "희망 포지션 (복수 선택 가능)",
        options=ALL_POSITIONS,
        default=[p for p in current_wishes if p in ALL_POSITIONS],
        format_func=lambda x: POS_CONFIG[x]['label']
    )
    
    if st.button("💾 변경사항 저장", use_container_width=True, type="primary"):
        st.session_state.players_dict[player_name] = new_wishes if new_wishes else ALL_POSITIONS.copy()
        st.success(f"{player_name} 선수의 포지션이 수정되었습니다!")
        st.rerun()

# 설정 및 선수 등록 섹션
st.subheader("⚙️ 설정 및 선수 등록")
col1, col2 = st.columns(2)

with col1:
    st.write("**① 선수 등록 (실시간 반영)**")
    with st.form(key="player_add_form", clear_on_submit=True):
        name_input = st.text_input("1. 선수 이름 입력", placeholder="예: 홍길동")
        wished_input = st.multiselect(
            "2. 희망 포지션 선택 (생략 가능)", 
            options=ALL_POSITIONS,
            format_func=lambda x: POS_CONFIG[x]['label']
        )
        submit_button = st.form_submit_button("🏃 선수 등록하기", use_container_width=True)
        
        if submit_button:
            name = name_input.strip()
            if name:
                if name in st.session_state.players_dict:
                    st.warning(f"'{name}' 선수는 이미 등록되어 있습니다.")
                else:
                    st.session_state.players_dict[name] = wished_input if wished_input else ALL_POSITIONS.copy()
                    st.session_state.attendance[name] = True
                    save_players_to_db(st.session_state.players_dict)
                    st.success(f"'{name}' 선수가 임시 명단에 등록되었습니다!")
                    st.rerun()
            else:
                st.error("선수 이름을 먼저 입력해 주세요.")

with col2:
    st.write("**② 경기 설정**")
    total_quarters = st.number_input("오늘 경기 쿼터 수 입력", min_value=1, max_value=12, value=7)
    if st.button("🔄 구글 시트 수동 새로고침", use_container_width=True):
        st.cache_data.clear()  # 수동 리로드 시에도 캐시 클리어 추가
        st.session_state.players_dict = load_players_from_db()
        st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}
        st.success("구글 시트에서 명단을 다시 불러왔습니다!")
        st.rerun()

# 참여 명단 출력
st.write(f"### 👥 전체 명단 ({len(st.session_state.players_dict)}명)")
if st.session_state.players_dict:
    for player, positions in list(st.session_state.players_dict.items()):
        emojis = "".join([POS_CONFIG[p]['emoji'] for p in positions if p in POS_CONFIG])
        
        col_att, col_p, col_edit, col_b = st.columns([1, 2.5, 1, 0.8])
        
        with col_att:
            st.session_state.attendance[player] = st.checkbox("참석", value=st.session_state.attendance.get(player, True), key=f"att_{player}")
        with col_p:
            color = "black" if st.session_state.attendance[player] else "#A0A0A0"
            st.write(f"<span style='color:{color}; font-weight:bold;'>🏃 {player}</span> <span style='font-size:14px;'>{emojis}</span>", unsafe_allow_html=True)
        with col_edit:
            if st.button("⚙️ 수정", key=f"edit_btn_{player}", use_container_width=True):
                edit_position_dialog(player)
        with col_b:
            if st.button("제거", key=f"del_{player}", use_container_width=True):
                del st.session_state.players_dict[player]
                if player in st.session_state.attendance:
                    del st.session_state.attendance[player]
                save_players_to_db(st.session_state.players_dict)
                st.rerun()
else:
    st.info("등록된 선수가 없습니다. 구글 시트를 확인하거나 선수를 직접 추가해 보세요.")

st.markdown("---")

# 라인업 생성 알고리즘
def generate_fair_lineups(players_pool, attendance_dict, total_q):
    active_players = [p for p, att in attendance_dict.items() if att and p in players_pool]
    if len(active_players) < 5:
        return None

    lineups = {}
    field_counts = {name: 0 for name in active_players} 
    gk_counts = {name: 0 for name in active_players}    
    player_pos_history = {name: {pos: 0 for pos in FIELD_POSITIONS} for name in active_players}
    
    last_quarter_gk = None
    
    for q in range(1, total_q + 1):
        starters = {pos: None for pos in ALL_POSITIONS}
        remaining = active_players.copy()
        
        # 1. 골레이로(GK) 선정
        gk_candidates = [p for p in remaining if GK_POSITION in players_pool[p]]
        if not gk_candidates:
            gk_candidates = remaining.copy()
            
        if last_quarter_gk in gk_candidates and len(gk_candidates) > 1:
            gk_candidates.remove(last_quarter_gk)
            
        random.shuffle(gk_candidates)
        gk_candidates.sort(key=lambda name: gk_counts[name])
        
        chosen_gk = gk_candidates[0]
        starters[GK_POSITION] = chosen_gk
        gk_counts[chosen_gk] += 1  
        remaining.remove(chosen_gk)
        last_quarter_gk = chosen_gk
        
        # 2. 필드 플레이어 선정
        random.shuffle(remaining)
        remaining.sort(key=lambda name: field_counts[name])
        
        shuffled_positions = FIELD_POSITIONS.copy()
        random.shuffle(shuffled_positions)
        
        for pos in shuffled_positions:
            wished_candidates = [p for p in remaining if pos in players_pool[p]]
            
            if wished_candidates:
                chosen_player = wished_candidates[0]
            else:
                remaining.sort(key=lambda name: (field_counts[name], player_pos_history[name][pos]))
                chosen_player = remaining[0]
                
            starters[pos] = chosen_player
            remaining.remove(chosen_player)
            
            field_counts[chosen_player] += 1
            player_pos_history[chosen_player][pos] += 1
            
        actual_subs = remaining
            
        lineups[f"{q}쿼터"] = {
            "starters": [starters[pos] for pos in ALL_POSITIONS],
            "subs": actual_subs,
            "field_snapshot": field_counts.copy(),
            "gk_snapshot": gk_counts.copy(),
            "history_snapshot": {name: player_pos_history[name].copy() for name in active_players}
        }
    return lineups

# 실행 버튼
if st.button("🚀 KOKO FC 라인업 자동 생성", type="primary", use_container_width=True):
    active_count = sum(1 for att in st.session_state.attendance.values() if att)
    if active_count < 5:
        st.error("오늘 경기 참석자가 최소 5명 이상이어야 라인업을 짤 수 있습니다! 체크박스를 확인해주세요.")
    else:
        st.session_state.lineups = generate_fair_lineups(
            st.session_state.players_dict, 
            st.session_state.attendance, 
            total_quarters
        )

# 결과 출력 섹션
if st.session_state.lineups:
    st.write("## 📋 경기 라인업 결과")
    st.info("💡 팁: 생성된 표의 셀을 더블클릭해서 이름을 직접 수정할 수 있습니다.")
    
    edited_data = []
    for quarter, data in st.session_state.lineups.items():
        row = {"쿼터": quarter}
        for idx, pos in enumerate(ALL_POSITIONS):
            header_label = POS_CONFIG[pos]['label']
            row[header_label] = data["starters"][idx] if data["starters"][idx] else "미지정"
        row["💤 대기 명단"] = ", ".join(data["subs"]) if data["subs"] else "- 없음 -"
        edited_data.append(row)
        
    st.data_editor(edited_data, use_container_width=True, num_rows="fixed")
    
    st.write("### 📊 최종 포지션별 상세 출전 통계")
    last_quarter = list(st.session_state.lineups.keys())[-1]
    final_fields = st.session_state.lineups[last_quarter]["field_snapshot"]
    final_gks = st.session_state.lineups[last_quarter]["gk_snapshot"]
    final_history = st.session_state.lineups[last_quarter]["history_snapshot"]
    
    stats_data = []
    for name in final_fields.keys():
        player_history = final_history[name]
        stats_data.append({
            "선수명": name,
            "🏃 필드 출전 ": f"{final_fields[name]}회",
            "🔥 PIVO ": f"{player_history['PIVO (공격)']}회",
            "⚡ ALA_L ": f"{player_history['ALA_L (좌윙)']}회",
            "✨ ALA_R ": f"{player_history['ALA_R (우윙)']}회",
            "🛡️ FIXO ": f"{player_history['🛡️ FIXO (수비)']}회" if '🛡️ FIXO (수비)' in player_history else f"{player_history.get('FIXO (수비)', 0)}회",
            "🧤 GOLEIRO ": f"{final_gks[name]}회"
        })
    
    # 💡 [핵심 수정] 타이틀 줄의 각 칸(th) 마다 번호를 매겨 개별 색상을 주입합니다.
    df_stats = pd.DataFrame(stats_data)
    styled_stats = df_stats.style.set_properties(**{
        'text-align': 'center'
    }).set_table_styles([
        # th 공통 속성 (글자색, 정렬)
        {'selector': 'th', 'props': [('color', 'white'), ('text-align', 'center')]},
        
        # th:nth-child(1) -> 첫 번째 칸 (선수명) -> 초록색
        {'selector': 'th:nth-child(1)', 'props': [('background-color', '#14532D')]},
        
        # th:nth-child(2) -> 두 번째 칸 (🏃 필드 출전 ) -> 남색
        {'selector': 'th:nth-child(2)', 'props': [('background-color', '#1E3A8A')]},
        
        # th:nth-child(3~6) -> 포지션 칸들 (PIVO, ALA_L, ALA_R, FIXO) -> 회색
        {'selector': 'th:nth-child(3)', 'props': [('background-color', '#374151')]},
        {'selector': 'th:nth-child(4)', 'props': [('background-color', '#374151')]},
        {'selector': 'th:nth-child(5)', 'props': [('background-color', '#374151')]},
        {'selector': 'th:nth-child(6)', 'props': [('background-color', '#374151')]},
        
        # th:nth-child(7) -> 일곱 번째 칸 (🧤 GOLEIRO ) -> 남색
        {'selector': 'th:nth-child(7)', 'props': [('background-color', '#1E3A8A')]}
    ]).hide(axis="index")
    
    st.write(styled_stats.to_html(), unsafe_allow_html=True)
