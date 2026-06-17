import streamlit as st
import random

# 페이지 설정
st.set_page_config(page_title="⚽ KOKO FC 😈 라인업 매니저", layout="centered")
st.title("⚽ KOKO FC 😈 라인업 매니저")
st.caption("필드 균등 완벽 분배 + 희망 포지션 엄격 매칭 + 골레이로 독립 로테이션")

# 포지션별 고유 이모지와 색상 정의
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

# 세션 상태 초기화
if 'players_dict' not in st.session_state:
    st.session_state.players_dict = {}
if 'lineups' not in st.session_state:
    st.session_state.lineups = None

# 선수 등록 및 폼 섹션
st.subheader("⚙️ 설정 및 선수 등록")
col1, col2 = st.columns(2)

with col1:
    st.write("**① 선수 등록 (이름 입력 ➡️ 포지션 선택 ➡️ 등록 버튼)**")
    
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
                    # 아무것도 선택 안 하면 전 포지션 가능, 선택하면 '선택한 포지션만' 엄격 제한
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
        emojis = "".join([POS_CONFIG[p]['emoji'] for p in positions])
        col_p, col_b = st.columns([4, 1])
        with col_p:
            st.write(f"🏃 **{player}** <span style='font-size:14px;'>{emojis}</span>", unsafe_allow_html=True)
        with col_b:
            if st.button("제거", key=f"del_{player}"):
                del st.session_state.players_dict[player]
                st.rerun()
else:
    st.info("등록된 선수가 없습니다. 왼쪽에서 선수를 추가해 주세요.")

st.markdown("---")

# 업데이트된 완벽 공정 분배 알고리즘
def generate_fair_lineups(players_pool, total_q):
    lineups = {}
    player_names = list(players_pool.keys())
    
    # 통계 추적용 변수 (필드와 골레이로는 완벽히 독립적으로 카운트)
    field_counts = {name: 0 for name in player_names} 
    gk_counts = {name: 0 for name in player_names}    
    player_pos_history = {name: {pos: 0 for pos in FIELD_POSITIONS} for name in player_names}
    
    for q in range(1, total_q + 1):
        starters = {pos: None for pos in ALL_POSITIONS}
        remaining = player_names.copy()
        
        # [1단계] 골레이로(GK) 우선 선출 (골레이로 출전 횟수가 가장 적은 사람)
        gk_candidates = [p for p in remaining if GK_POSITION in players_pool[p]]
        if not gk_candidates:  # 아무도 희망 안 했다면 전원 후보
            gk_candidates = remaining.copy()
            
        random.shuffle(gk_candidates)
        gk_candidates.sort(key=lambda name: gk_counts[name])  # 오직 골레이로 뛴 횟수로만 정렬
        
        chosen_gk = gk_candidates[0]
        starters[GK_POSITION] = chosen_gk
        gk_counts[chosen_gk] += 1  
        remaining.remove(chosen_gk)  # 키퍼로 뽑힌 사람은 필드 후보에서 원천 제외
        
        # [2단계] 필드 플레이어 4명 선출 (★오직 '필드 출전 횟수'가 적은 순서대로)
        random.shuffle(remaining)
        remaining.sort(key=lambda name: field_counts[name])
        
        current_field_players = remaining[:4]
        actual_subs = remaining[4:]
        
        # [3단계] 선출된 필드 플레이어 4명을 포지션에 배치 (희망 포지션 엄격 반영)
        available_positions = FIELD_POSITIONS.copy()
        
        # 안정적인 매칭을 위해 희망 포지션 개수가 적어 까다로운 선수부터 먼저 배치
        current_field_players.sort(key=lambda p: len([pos for pos in players_pool[p] if pos in FIELD_POSITIONS]))
        
        for player in current_field_players:
            # 해당 선수의 희망 포지션 중 아직 남아있는 자리 필터링
            valid_wishes = [pos for pos in players_pool[player] if pos in available_positions]
            
            if not valid_wishes:
                # 만약 남은 포지션 중 희망하는 곳이 전혀 없다면, 어쩔 수 없이 남은 자리 중 과거에 가장 적게 서본 곳으로 강제 배정
                valid_wishes = available_positions.copy()
            
            # 과거에 해당 포지션을 적게 가본 순으로 정렬
            valid_wishes.sort(key=lambda pos: player_pos_history[player][pos])
            
            best_pos = valid_wishes[0]
            starters[best_pos] = player
            available_positions.remove(best_pos)
            
            # 가중치 업데이트 (필드 카운트 증가)
            field_counts[player] += 1
            player_pos_history[player][best_pos] += 1
            
        lineups[f"{q}쿼터"] = {
            "starters": [starters[pos] for pos in ALL_POSITIONS],
            "subs": actual_subs,
            "field_snapshot": field_counts.copy(),
            "gk_snapshot": gk_counts.copy()
        }
    return lineups

# 라인업 생성 실행 버튼
if st.button("🚀 KOKO FC 라인업 자동 생성", type="primary", use_container_width=True):
    if len(st.session_state.players_dict) < 5:
        st.error("경기를 진행하려면 최소 5명 이상의 선수가 필요합니다!")
    else:
        st.session_state.lineups = generate_fair_lineups(st.session_state.players_dict, total_quarters)

# 결과 표 출력 및 수정
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
    
    # 완전히 분리된 출전 통계 표 출력
    st.write("### 📊 최종 포지션별 출전 통계")
    last_quarter = list(st.session_state.lineups.keys())[-1]
    final_fields = st.session_state.lineups[last_quarter]["field_snapshot"]
    final_gks = st.session_state.lineups[last_quarter]["gk_snapshot"]
    
    stats_data = []
    for name in st.session_state.players_dict.keys():
        stats_data.append({
            "선수명": name,
            "필드 출전": f"{final_fields[name]}회",
            "골레이로 출전": f"{final_gks[name]}회",
            "총 출전 (합계)": f"{final_fields[name] + final_gks[name]}쿼터"
        })
    st.table(stats_data)
