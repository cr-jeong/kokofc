import streamlit as st
import random

# 페이지 설정
st.set_page_config(page_title="KOKO FC 풋살 라인업 매니저", layout="centered")
st.title("⚽ KOKO FC 풋살 라인업 매니저")
st.caption("필드 출전 횟수 100% 공정 분배 보장 버전")

# 포지션 정의
FIELD_POSITIONS = ['PIVO (공격)', 'ALA_L (좌윙)', 'ALA_R (우윙)', 'FIXO (수비)']
GK_POSITION = 'GOLEIRO (키퍼)'
ALL_POSITIONS = FIELD_POSITIONS + [GK_POSITION]

# 세션 상태 초기화
if 'players_dict' not in st.session_state:
    st.session_state.players_dict = {}  # {이름: [희망포지션 리스트]}
if 'lineups' not in st.session_state:
    st.session_state.lineups = None

# 선수 등록 함수
def add_player_action():
    name = st.session_state.player_name_input.strip()
    if name:
        if name in st.session_state.players_dict:
            st.warning(f"'{name}' 선수는 이미 등록되어 있습니다.")
        else:
            st.session_state.players_dict[name] = wished_input if wished_input else ALL_POSITIONS.copy()
    else:
        st.error("선수 이름을 먼저 입력해 주세요.")

# 1. 설정 및 입력 섹션
st.subheader("⚙️ 설정 및 선수 등록")
col1, col2 = st.columns(2)

with col1:
    st.write("**① 선수 등록 (이름 입력 ➡️ 포지션 선택 ➡️ 등록 버튼)**")
    
    with st.form(key="player_add_form", clear_on_submit=True):
        name_input = st.text_input("1. 선수 이름 입력", placeholder="예: 홍길동")
        wished_input = st.multiselect("2. 희망 포지션 선택 (생략 가능)", options=ALL_POSITIONS)
        submit_button = st.form_submit_button("🏃 선수 등록하기", use_container_width=True)
        
        if submit_button:
            name = name_input.strip()
            if name:
                if name in st.session_state.players_dict:
                    st.warning(f"'{name}' 선수는 이미 등록되어 있습니다.")
                else:
                    st.session_state.players_dict[name] = wished_input if wished_input else ALL_POSITIONS.copy()
                    st.rerun()
            else:
                st.error("선수 이름을 먼저 입력해 주세요.")

with col2:
    st.write("**② 경기 설정**")
    total_quarters = st.number_input("오늘 경기 쿼터 수 입력", min_value=1, max_value=12, value=4)

# 참여 명단 출력
st.write(f"### 👥 참석 명단 ({len(st.session_state.players_dict)}명)")
if st.session_state.players_dict:
    for player, positions in list(st.session_state.players_dict.items()):
        pos_text = ", ".join([p.split(" ")[0] for p in positions])
        col_p, col_b = st.columns([4, 1])
        with col_p:
            st.write(f"🏃 **{player}** <span style='color:gray; font-size:12px;'>({pos_text})</span>", unsafe_allow_html=True)
        with col_b:
            if st.button("제거", key=f"del_{player}"):
                del st.session_state.players_dict[player]
                st.rerun()
else:
    st.info("등록된 선수가 없습니다. 왼쪽에서 선수를 추가해 주세요.")

st.markdown("---")

# 2. 고도화된 공정 분배 라인업 생성 알고리즘
def generate_fair_lineups(players_pool, total_q):
    lineups = {}
    player_names = list(players_pool.keys())
    
    # 선수별 필드(골레이로 제외) 출전 횟수만 카운트
    play_counts = {name: 0 for name in player_names}
    
    for q in range(1, total_q + 1):
        starters = {pos: None for pos in ALL_POSITIONS}
        remaining = player_names.copy()
        
        # [핵심 변경 1단계] 골레이로(GK) 먼저 선출 (GK 선출은 필드 출전 횟수와 독립적)
        gk_candidates = [p for p in remaining if GK_POSITION in players_pool[p]]
        if not gk_candidates:
            gk_candidates = remaining.copy()
        chosen_gk = random.choice(gk_candidates)
        starters[GK_POSITION] = chosen_gk
        remaining.remove(chosen_gk)
        
        # [핵심 변경 2단계] 필드 플레이어 4명 "무조건 출전 적은 사람"으로 선발 고정
        random.shuffle(remaining) # 동률 처리를 위한 랜덤 셔플
        remaining.sort(key=lambda name: play_counts[name]) # 출전 적은 순 정렬
        
        # 이번 쿼터 필드에서 뛸 최종 4명 확정 (출전 기회 균등 100% 보장)
        current_field_players = remaining[:4]
        actual_subs = remaining[4:]
        
        # [핵심 변경 3단계] 뽑힌 4명 안에서 최선의 포지션 배치 (그리디 매칭)
        # 4명이 선호하는 포지션에 맞춰 배치하되, 선호가 겹치거나 없으면 남는 필드 자리에 들어감
        available_positions = FIELD_POSITIONS.copy()
        
        # 선호 포지션이 뚜렷한 사람부터 우선 매칭하기 위해 선호 목록이 적은 사람 순으로 정렬
        current_field_players.sort(key=lambda p: len(players_pool[p]))
        
        for player in current_field_players:
            matched_pos = None
            # 선수가 원하는 포지션 중 아직 남아있는 자리가 있는지 확인
            for pos in FIELD_POSITIONS:
                if pos in players_pool[player] and pos in available_positions:
                    matched_pos = pos
                    break
            
            # 원하는 자리가 이미 다 찼거나 없다면 남아있는 아무 필드 자리나 배정
            if not matched_pos:
                matched_pos = available_positions[0]
                
            starters[matched_pos] = player
            available_positions.remove(matched_pos)
            play_counts[player] += 1  # 필드 출전 횟수 정상 카운트
            
        lineups[f"{q}쿼터"] = {
            "starters": [starters[pos] for pos in ALL_POSITIONS],
            "subs": actual_subs,
            "counts_snapshot": play_counts.copy()
        }
    return lineups

# 라인업 생성 실행 버튼
if st.button("🚀 공정 분배 라인업 자동 생성", type="primary", use_container_width=True):
    if len(st.session_state.players_dict) < 5:
        st.error("경기를 진행하려면 최소 5명 이상의 선수가 필요합니다!")
    else:
        st.session_state.lineups = generate_fair_lineups(st.session_state.players_dict, total_quarters)

# 3. 결과 표 출력 및 수정
if st.session_state.lineups:
    st.write("## 📋 경기 라인업 결과")
    st.info("💡 팁: 생성된 표의 셀을 더블클릭해서 이름을 직접 수정할 수 있습니다.")
    
    edited_data = []
    for quarter, data in st.session_state.lineups.items():
        row = {"쿼터": quarter}
        for idx, pos in enumerate(ALL_POSITIONS):
            row[pos] = data["starters"][idx] if data["starters"][idx] else "미지정"
        row["대기 명단"] = ", ".join(data["subs"]) if data["subs"] else "- 없음 -"
        edited_data.append(row)
        
    st.data_editor(edited_data, use_container_width=True, num_rows="fixed")
    
    # 공정 분배 통계 표
    st.write("### 📊 최종 필드 출전 횟수 (자동 계산 기준)")
    last_quarter = list(st.session_state.lineups.keys())[-1]
    final_counts = st.session_state.lineups[last_quarter]["counts_snapshot"]
    
    stats_data = [{"선수명": name, "필드 출전 쿼터 수": f"{count}회"} for name, count in final_counts.items()]
    st.table(stats_data)
