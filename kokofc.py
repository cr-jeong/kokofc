import streamlit as st
import random
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 포지션 설정 및 상수
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

st.set_page_config(page_title="⚽ KOKO FC 라인업 매니저", layout="centered")

st.title("⚽ KOKO FC 😈 라인업 매니저")

# 2. 구글 시트 연동 및 데이터 세션 관리
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
    st.session_state.players_dict = load_players_from_db()
    st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}
    st.session_state.first_load_done = True

if 'players_dict' not in st.session_state: st.session_state.players_dict = {}
if 'lineups' not in st.session_state: st.session_state.lineups = None
if 'attendance' not in st.session_state: st.session_state.attendance = {}

# 데이터 동기화
for p in st.session_state.players_dict.keys():
    if p not in st.session_state.attendance:
        st.session_state.attendance[p] = True

# 3. [통합 관리 관리자 툴] 익스팬더 하나로 UI 정리
with st.expander("🛠️ 경기 설정 / 선수 추가 및 개별 변경", expanded=False):
    # ① 경기 설정
    st.markdown("#### **① 경기 기본 설정**")
    total_quarters = st.number_input("오늘 경기 쿼터 수 입력", min_value=1, max_value=12, value=7)
    if st.button("🔄 구글 시트 명단 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.session_state.players_dict = load_players_from_db()
        st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}
        st.rerun()
    
    st.markdown("---")
    
    # ② 실시간 선수 추가
    st.markdown("#### **② 명단 즉시 추가 (용병 등)**")
    with st.form(key="player_add_form_v2", clear_on_submit=True, border=False):
        name_input = st.text_input("선수 이름 입력", placeholder="예: 홍길동(용병)")
        wished_input = st.multiselect("희망 포지션 선택 (미선택 시 전체)", options=ALL_POSITIONS, format_func=lambda x: POS_CONFIG[x]['label'])
        if st.form_submit_button("🏃 신규 선수 명단 등록", use_container_width=True):
            name = name_input.strip()
            if name and name not in st.session_state.players_dict:
                st.session_state.players_dict[name] = wished_input if wished_input else ALL_POSITIONS.copy()
                st.session_state.attendance[name] = True
                st.rerun()

    st.markdown("---")

    # ③ UI 혁신: 버튼 폭탄을 지우는 단 하나의 드롭다운 관리자 툴
    st.markdown("#### **③ 기존 선수 설정 및 삭제**")
    target_player = st.selectbox("수정 또는 삭제할 선수를 선택하세요", options=["-- 선택하세요 --"] + list(st.session_state.players_dict.keys()))
    if target_player != "-- 선택하세요 --":
        current_wishes = st.session_state.players_dict[target_player]
        new_wishes = st.multiselect(
            f"🎯 {target_player} 선수의 희망 포지션 변경",
            options=ALL_POSITIONS,
            default=[p for p in current_wishes if p in ALL_POSITIONS],
            format_func=lambda x: POS_CONFIG[x]['label'],
            key="edit_wishes_key"
        )
        col_edit1, col_edit2 = st.columns(2)
        with col_edit1:
            if st.button("💾 포지션 저장", use_container_width=True, type="primary"):
                st.session_state.players_dict[target_player] = new_wishes if new_wishes else ALL_POSITIONS.copy()
                st.success(f"{target_player} 선수의 포지션이 변경되었습니다.")
                st.rerun()
        with col_edit2:
            if st.button("🗑️ 이 선수 삭제", use_container_width=True):
                del st.session_state.players_dict[target_player]
                if target_player in st.session_state.attendance: del st.session_state.attendance[target_player]
                st.rerun()

# 4. 👥 전체 명단 및 출석 체크 (지저분한 버튼이 다 사라져 완벽히 깔끔해짐)
st.markdown(f"### 👥 참석 명단 체크 ({sum(1 for v in st.session_state.attendance.values() if v)} / {len(st.session_state.players_dict)}명)")
if st.session_state.players_dict:
    with st.container(border=True):
        for player in list(st.session_state.players_dict.keys()):
            is_active = st.session_state.attendance.get(player, True)
            
            # 순정 체크박스로 깔끔하게 나열
            selected = st.checkbox(f"🏃 {player}", value=is_active, key=f"attendance_v17_{player}")
            st.session_state.attendance[player] = selected
            
            # 인라인 포지션 안내 텍스트로 깔끔하게 처리
            positions = st.session_state.players_dict[player]
            labels = [POS_CONFIG[p]['label'] for p in positions if p in POS_CONFIG]
            pos_text = " | ".join(labels) if len(labels) < len(ALL_POSITIONS) else "모든 포지션 가능"
            
            st.markdown(f"<div style='padding-left: 28px; font-size: 11px; margin-top: -6px; margin-bottom: 8px; color: gray; opacity: {1.0 if selected else 0.3};'>💡 희망: {pos_text}</div>", unsafe_allow_html=True)
else:
    st.info("등록된 선수가 없습니다.")

# 5. 라인업 생성 알고리즘
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

st.write("")
if st.button("🚀 KOKO FC 라인업 자동 생성", type="primary", use_container_width=True):
    active_count = sum(1 for att in st.session_state.attendance.values() if att)
    if active_count < 5: 
        st.error("참석 인원이 최소 5명 이상이어야 합니다.")
    else: 
        st.session_state.lineups = generate_fair_lineups(st.session_state.players_dict, st.session_state.attendance, total_quarters)

# 6. 결과 및 통계 노출
if st.session_state.lineups:
    st.markdown("### 📋 경기 라인업 결과 (수정 가능)")
    
    edited_data = []
    for quarter, data in st.session_state.lineups.items():
        row = {"쿼터": quarter}
        for idx, pos in enumerate(ALL_POSITIONS): 
            row[POS_CONFIG[pos]['label']] = data["starters"][idx] or "미지정"
        edited_data.append(row)
        
    # 편집 가능한 라인업 테이블
    updated_rows = st.data_editor(edited_data, use_container_width=True, num_rows="fixed", disabled=["쿼터"], hide_index=True)
    
    # 수정 사항을 즉시 연동하는 카톡 공유 텍스트 빌더
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
    
    # 7. 📊 포지션별 상세 출전 통계 (완벽하게 안전하고 에러 없는 순정 DataFrame 구현)
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
            "🧤 GK": final_gks.get(name, 0), 
            "🏃 필드": final_fields.get(name, 0),
            "🔱 PIVO": player_history.get('PIVO (공격)', 0), 
            "◀️ ALA_L": player_history.get('ALA_L (좌윙)', 0),
            "▶️ ALA_R": player_history.get('ALA_R (우윙)', 0), 
            "🛡️ FIXO": player_history.get('FIXO (수비)', 0)
        })
    
    df_stats = pd.DataFrame(stats_data)
    
    # 💥 핵심 수정: 에러 유발 HTML 대신 Streamlit 자체 데이터프레임을 사용해 다크모드 완벽 대응 및 크래시 완전 차단
    st.dataframe(df_stats, use_container_width=True, hide_index=True)
