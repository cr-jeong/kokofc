import streamlit as st
import random

# 페이지 설정
st.set_page_config(page_title="우리 팀 풋살 라인업 매니저", layout="centered")
st.title("⚽ 우리 팀 풋살 라인업 매니저")
st.caption("출전 시간 공정 분배 + 희망 포지션 매칭 버전")

# 포지션 정의
FIELD_POSITIONS = ['PIVO (공격)', 'ALA_L (좌윙)', 'ALA_R (우윙)', 'FIXO (수비)']
GK_POSITION = 'GOLEIRO (키퍼)'
ALL_POSITIONS = FIELD_POSITIONS + [GK_POSITION]

# 세션 상태 초기화
if 'players_dict' not in st.session_state:
    st.session_state.players_dict = {}  # {이름: [희망포지션 리스트]}
if 'lineups' not in st.session_state:
    st.session_state.lineups = None

# 엔터 시 호출되는 등록 함수
def handle_add_player():
    name = st.session_state.player_name.strip()
    if name:
        if name in st.session_state.players_dict:
            st.warning(f"'{name}' 선수는 이미 등록되어 있습니다.")
        else:
            selected_pos = st.session_state.wished_positions
            st.session_state.players_dict[name] = selected_pos if selected_pos else ALL_POSITIONS.copy()
            st.session_state.player_name = ""  # 입력창 초기화
    else:
        st.error("이름을 입력해 주세요.")

# 1. 설정 섹션
st.subheader("⚙️ 설정 및 선수 등록")
col1, col2 = st.columns(2)

with col1:
    st.write("**① 선수 등록 (엔터 가능)**")
    wished = st.multiselect(
        "희망 포지션 (선택 안 하면 올라운더)", 
        options=ALL_POSITIONS,
        key="wished_positions"
    )
    st.text_input(
        "선수 이름 입력 후 Enter", 
        key="player_name", 
        on_change=handle_add_player
    )

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

# 2. 공정 분배 기반 라인업 생성 알고리즘
def generate_fair_lineups(players_pool, total_q):
    lineups = {}
    player_names = list(players_pool.keys())
    
    # 선수별 필드 출전 횟수 기록용 딕셔너리 {이름: 출전횟수}
    play_counts = {name: 0 for name in player_names}
    
    for q in range(1, total_q + 1):
        starters = {pos: None for pos in ALL_POSITIONS}
        remaining = player_names.copy()
        
        # [1단계] 골레이로(GK) 먼저 선출 (GK 희망자 우선, 겹치면 무작위)
        gk_candidates = [p for p in remaining if GK_POSITION in players_pool[p]]
        if not gk_candidates:
            gk_candidates = remaining.copy()
        
        # GK는 많이 뛴 사람/적게 뛴 사람 상관없이 GK 풀에서 무작위 선출 (필드 출전 계산에서 제외하기 위함)
        chosen_gk = random.choice(gk_candidates)
        starters[GK_POSITION] = chosen_gk
        remaining.remove(chosen_gk)
        
        # [2단계] 필드 플레이어 4명 선출 (덜 뛴 사람 우선 순위 정렬)
        # 출전 횟수가 적은 순, 같다면 무작위(셔플) 정렬
        random.shuffle(remaining)
        remaining.sort(key=lambda name: play_counts[name])
        
        # 필드 포지션 매칭
        for pos in FIELD_POSITIONS:
            matched_player = None
            
            # 현재 쿼터에서 아직 안 뽑힌 선수 중, 해당 포지션을 희망하는 '가장 적게 뛴 선수' 탐색
            for p in remaining:
                if pos in players_pool[p]:
                    matched_player = p
                    break
            
            # 희망자가 없다면 남아있는 선수 중 가장 적게 뛴 선수 배정
            if not matched_player and remaining:
                matched_player = remaining[0]
                
            if matched_player:
                starters[pos] = matched_player
                play_counts[matched_player] += 1  # 필드 출전 횟수 누적 추가
                remaining.remove(matched_player)
                
        # 대기 명단 기록
        subs = remaining.copy()
        
        lineups[f"{q}쿼터"] = {
            "starters": [starters[pos] for pos in ALL_POSITIONS],
            "subs": subs,
            "counts_snapshot": play_counts.copy() # 시각화용 스냅샷
        }
        
    return lineups

# 실행 버튼
if st.button("🚀 공정 분배 라인업 자동 생성", type="primary", use_container_width=True):
    if len(st.session_state.players_dict) < 5:
        st.error("경기를 진행하려면 최소 5명 이상의 선수가 필요합니다!")
    else:
        st.session_state.lineups = generate_fair_lineups(st.session_state.players_dict, total_quarters)

# 3. 결과 표 출력 및 수정
if st.session_state.lineups:
    st.write("## 📋 경기 라인업 결과")
    st.info("💡 팁: 생성된 표의 셀을 더블클릭해서 이름을 직접 편집 및 트레이드할 수 있습니다.")
    
    edited_data = []
    for quarter, data in st.session_state.lineups.items():
        row = {"쿼터": quarter}
        for idx, pos in enumerate(ALL_POSITIONS):
            row[pos] = data["starters"][idx] if data["starters"][idx] else "미지정"
        row["대기 명단"] = ", ".join(data["subs"]) if data["subs"] else "- 없음 -"
        edited_data.append(row)
        
    st.data_editor(edited_data, use_container_width=True, num_rows="fixed")
    
    # [추가 기능] 공정하게 분배되었는지 시각적으로 보여주는 통계 표
    st.write("### 📊 이번 라인업의 선수별 최종 필드 출전 횟수")
    last_quarter = list(st.session_state.lineups.keys())[-1]
    final_counts = st.session_state.lineups[last_quarter]["counts_snapshot"]
    
    # 보기 좋게 표 형태로 변환
    stats_data = [{"선수명": name, "필드 출전 쿼터 수": f"{count}회"} for name, count in final_counts.items()]
    st.table(stats_data)