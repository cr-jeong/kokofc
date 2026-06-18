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

# 페이지 설정 (원래대로)
st.set_page_config(page_title="⚽ KOKO FC 😈 라인업 매니저", layout="centered")
st.title("⚽ KOKO FC 😈 라인업 매니저")
st.caption("KOKO 화이팅!! 버그 제보 환영")
st.caption("참석 체크 + 앱 내 실시간 포지션 수정 기능 + [카톡 복사] 대기 명단 제외 버전!")

# 구글 스프레딧시트 연결 초기화
conn = st.connection("gsheets", type=GSheetsConnection)

# 구글 시트 로딩 속도 향상 (TTL 5분 설정)
@st.cache_data(ttl=300)
def load_players_from_db():
    try:
        df = conn.read(header=None, ttl=300)
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
        st.error(f"구글 시트 로드 중 에러 발생: {e}")
        return {}

def save_players_to_db(players_dict):
    st.cache_data.clear()

# 앱 시작 시 구글 시트 원본 자동 로드 로직
if 'first_load_done' not in st.session_state:
    st.cache_data.clear()
    st.session_state.players_dict = load_players_from_db()
    st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}
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

# 희망 포지션 수정을 위한 팝업창(Dialog) 정의
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

# 설정 및 선수 등록 섹션 (박스 테두리 유지)
st.subheader("⚙️ 설정 및 선수 등록")
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
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
    with st.container(border=True):
        st.write("**② 경기 설정**")
        total_quarters = st.number_input("오늘 경기 쿼터 수 입력", min_value=1, max_value=12, value=7)
        st.
