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
st.caption("구글 스프레드시트 DB 로드 + 필드 균등 완벽 분배 + 골레이로 독립 로테이션")

# 구글 스프레드시트 연결 초기화
conn = st.connection("gsheets", type=GSheetsConnection)

# DB에서 선수 명단 로드 함수 (읽기는 안전하게 작동)
def load_players_from_db():
    try:
        df = conn.read(ttl="5s")
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
        return {}

# 🛠️ 에러가 나던 저장 함수를 안전하게 수정
def save_players_to_db(players_dict):
    # 구글 서비스 계정(비밀키)이 없으면 시트 쓰기가 불가능하므로, 
    # 에러를 내지 않고 캐시만 비워 앱 내부 메모리에서만 작동하도록 우회합니다.
    st.cache_data.clear()

# 앱 최초 실행 시 DB에서 선수 명단 동기화
if 'players_dict' not in st.session_state:
    st.session_state.players_dict = load_players_from_db()
if 'lineups' not in st.session_state:
    st.session_state.lineups = None

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
                    save_players_to_db(st.session_state.players_dict)
                    st.success(f"'{name}' 선수가 임시 명단에 등록되었습니다!")
                    st.rerun()
            else:
                st.error("선수 이름을 먼저 입력해 주세요.")

with col2:
    st.write("**② 경기 설정**")
    total_quarters = st.number_input("오늘 경기 쿼터 수 입력", min_value=1, max_value=12, value=4)
    if st.button("🔄 구글 시트 원본 로드 (새로고침)", use_container_width=True):
        st.session_state.players_dict = load_players_from_db()
        st.rerun()

# 참여 명단 출력
st.write(f"### 👥 참석 명단 ({len(st.session_state.players_dict)}명)")
if st.session_state.players_dict:
    for player, positions in list(st.session_state.players_dict.items()):
        emojis = "".join([POS_CONFIG[p]['emoji'] for p in positions if p in POS_CONFIG])
        col_p, col_b = st.columns([4, 1])
        with col_p:
            st.write(f"🏃 **{player}** <span style='font-size:14px;'>{emojis}</span>", unsafe_allow_html=True)
        with col_b:
            if st.button("제거", key=f"del_{player}"):
                del st.session_state.players_dict[player]
                save_players_to_db(st.session_state.players_dict)
                st.rerun()
else:
    st.info("등록된 선수가 없습니다. 선수를 추가하거나 우측의 새로고침을 눌러보세요.")

st.markdown("---")

# 라인업 생성 알고리즘
def generate_fair_lineups(players_pool, total_q):
    lineups = {}
    player_names = list(players_pool.keys())
    field_counts = {name: 0 for name in player_names} 
    gk_counts = {name: 0 for name in player_names}    
    player_pos_history = {name: {pos: 0 for pos in FIELD_POSITIONS} for name in player_names}
    
    for q in range(1, total_q + 1):
        starters = {pos: None for pos in ALL_POSITIONS}
        remaining = player_names.copy()
        
        gk_candidates = [p for p in remaining if GK_POSITION in players_pool[p]]
        if not gk_candidates:
            gk_candidates = remaining.copy()
            
        random.shuffle(gk_candidates)
        gk_candidates.sort(key=lambda name: gk_counts[name])
        
        chosen_gk = gk_candidates[0]
        starters[GK_POSITION] = chosen_gk
        gk_counts[chosen_gk] += 1  
        remaining.remove(chosen_gk)
        
        random.shuffle(remaining)
        remaining.sort(key=lambda name: field_counts[name])
        
        current_field_players = remaining[:4]
        actual_subs = remaining[4:]
        
        available_positions = FIELD_POSITIONS.copy()
        current_field_players.sort(key=lambda p: len([pos for pos in players_pool[p] if pos in FIELD_POSITIONS]))
        
        for player in current_field_players:
            valid_wishes = [pos for pos in players_pool[player] if pos in available_positions]
            if not valid_wishes:
                valid_wishes = available_positions.copy()
            
            valid_wishes.sort(key=lambda pos: player_pos_history[player][pos])
            best_pos = valid_wishes[0]
            starters[best_pos] = player
            available_positions.remove(best_pos)
            
            field_counts[player] += 1
            player_pos_history[player][best_pos] += 1
            
        lineups[f"{q}쿼터"] = {
            "starters": [starters[pos] for pos in ALL_POSITIONS],
            "subs": actual_subs,
            "field_snapshot": field_counts.copy(),
            "gk_snapshot": gk_counts.copy(),
            "history_snapshot": {name: player_pos_history[name].copy() for name in player_names}
        }
    return lineups

if st.button("🚀 KOKO FC 라인업 자동 생성", type="primary", use_container_width=True):
    if len(st.session_state.players_dict) < 5:
        st.error("경기를 진행하려면 최소 5명 이상의 선수가 필요합니다!")
    else:
        st.session_state.lineups = generate_fair_lineups(st.session_state.players_dict, total_quarters)

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
    for name in st.session_state.players_dict.keys():
        player_history = final_history[name]
        stats_data.append({
            "선수명": name,
            "🏃 필드 출전 (합계)": f"{final_fields[name]}회",
            "🔥 PIVO (공격)": f"{player_history['PIVO (공격)']}회",
            "⚡ ALA_L (좌윙)": f"{player_history['ALA_L (좌윙)']}회",
            "✨ ALA_R (우윙)": f"{player_history['ALA_R (우윙)']}회",
            "🛡️ FIXO (수비)": f"{player_history['FIXO (수비)']}회",
            "🧤 GOLEIRO (키퍼)": f"{final_gks[name]}회"
        })
    st.table(stats_data)
