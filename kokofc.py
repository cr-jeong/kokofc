import streamlit as st
import random
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 포지션 및 기본 구성
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

st.set_page_config(page_title="KOKO FC 모바일 매니저", layout="centered")

# 모바일 전용 CSS 주입 (여백 최적화 및 터치 영역 확보)
st.markdown("""
    <style>
    /* 전체 좌우 여백 줄여서 모바일 화면 넓게 쓰기 */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    /* 체크박스 터치 영역 키우고 글자 흐림 처리 */
    .stCheckbox {
        padding: 6px 0;
    }
    .stCheckbox [aria-checked="false"] ~ div p {
        opacity: 0.3 !important;
        text-decoration: line-through !important;
    }
    /* 버튼 패딩 최적화 */
    div.stButton > button {
        padding: 6px 10px !important;
        font-size: 14px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 구글 시트 연동
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
                players_dict[name] = positions if positions else ALL_POSITIONS.copy()
        return players_dict
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return {}

# 3. 세션 상태 동기화
if 'first_load_done' not in st.session_state:
    st.session_state.players_dict = load_players_from_db()
    st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}
    st.session_state.lineups = None
    st.session_state.first_load_done = True

for p in st.session_state.players_dict.keys():
    if p not in st.session_state.attendance:
        st.session_state.attendance[p] = True

# 4. 희망 포지션 수정 다이얼로그 (모바일 팝업 대응)
@st.dialog("🎯 포지션 변경")
def edit_position_dialog(player_name):
    st.write(f"🏃 **{player_name}** 선수의 선호 포지션")
    current_wishes = st.session_state.players_dict[player_name]
    new_wishes = st.multiselect(
        "선택 (미선택 시 전포지션 가능)",
        options=ALL_POSITIONS,
        default=[p for p in current_wishes if p in ALL_POSITIONS],
        format_func=lambda x: POS_CONFIG[x]['label']
    )
    if st.button("💾 저장하기", use_container_width=True, type="primary"):
        st.session_state.players_dict[player_name] = new_wishes if new_wishes else ALL_POSITIONS.copy()
        st.rerun()

# --- 타이틀 및 메인 영역 ---
st.title("⚽ KOKO FC 라인업")

# 5. [모바일 UX] 경기 설정부 아코디언으로 접기 (첫 화면에 명단이 바로 보이게!)
with st.expander("⚙️ 경기 세팅 및 선수 추가 (터치해서 열기)", expanded=False):
    total_quarters = st.number_input("오늘 총 쿼터 수", min_value=1, max_value=12, value=7)
    
    with st.form(key="player_add_form", clear_on_submit=True):
        st.write("**➕ 신규 임시 선수 등록**")
        name_input = st.text_input("선수 이름", placeholder="이름 입력")
        wished_input = st.multiselect("희망 포지션", options=ALL_POSITIONS, format_func=lambda x: POS_CONFIG[x]['label'])
        if st.form_submit_button("등록하기", use_container_width=True):
            name = name_input.strip()
            if name and name not in st.session_state.players_dict:
                st.session_state.players_dict[name] = wished_input if wished_input else ALL_POSITIONS.copy()
                st.session_state.attendance[name] = True
                st.rerun()

    if st.button("🔄 구글 시트 명단 가져오기", use_container_width=True):
        st.cache_data.clear()
        st.session_state.players_dict = load_players_from_db()
        st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}
        st.rerun()

st.markdown("---")

# 6. 모바일 화면 맞춤형 명단 레이아웃 (세로형 정렬 변환)
st.subheader(f"👥 참석 체크 ({sum(1 for att in st.session_state.attendance.values() if att)}명 출석)")

TAG_STYLES = {
    'PIVO (공격)': 'background-color: #FEE2E2; color: #EF4444;', 
    'ALA_L (좌윙)': 'background-color: #E0F2FE; color: #0284C7;', 
    'ALA_R (우윙)': 'background-color: #FEF3C7; color: #D97706;', 
    'FIXO (수비)': 'background-color: #DCFCE7; color: #16A34A;', 
    'GOLEIRO (키퍼)': 'background-color: #F3F4F6; color: #4B5563;' 
}

if st.session_state.players_dict:
    with st.container(border=True):
        for player in list(st.session_state.players_dict.keys()):
            positions = st.session_state.players_dict[player]
            is_active = st.session_state.attendance.get(player, True)
            
            # [모바일 최적화] 왼쪽은 체크박스 전용, 오른쪽은 관리 버튼들 배치
            col_main, col_ctrl = st.columns([2.5, 1.5])
            
            with col_main:
                selected = st.checkbox(f"🏃 {player}", value=is_active, key=f"chk_{player}")
                st.session_state.attendance[player] = selected
                
                # 포지션 태그들을 체크박스 바로 밑에 배치
                tag_htmls = []
                for p in positions:
                    if p in POS_CONFIG:
                        tag_htmls.append(f"<span style='padding: 2px 5px; margin-right: 3px; margin-bottom: 2px; border-radius: 4px; font-size: 10px; font-weight: bold; {TAG_STYLES.get(p, '')}'>{POS_CONFIG[p]['label'].split(' ')[1]}</span>")
                opacity_val = "1.0" if selected else "0.2"
                st.markdown(f"<div style='padding-left: 28px; margin-top: -4px; margin-bottom: 6px; display: flex; flex-wrap: wrap; opacity: {opacity_val};'>{''.join(tag_htmls)}</div>", unsafe_allow_html=True)
                
            with col_ctrl:
                # 버튼들이 모바일에서 안 깨지도록 간격 조절
                btn_c1, btn_c2 = st.columns(2)
                with btn_c1:
                    if st.button("⚙️", key=f"ed_{player}", use_container_width=True):
                        edit_position_dialog(player)
                with btn_c2:
                    if st.button("❌", key=f"del_{player}", use_container_width=True):
                        del st.session_state.players_dict[player]
                        if player in st.session_state.attendance: del st.session_state.attendance[player]
                        st.rerun()
            
            st.markdown("<div style='margin: 2px 0; border-bottom: 1px dashed #F1F5F9;'></div>", unsafe_allow_html=True)
else:
    st.info("등록된 선수가 없습니다.")

# 7. 라인업 알고리즘 (동일 유지)
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
        if last_quarter_gk in gk_candidates and len(gk_candidates) > 1:
            gk_candidates.remove(last_quarter_gk)
            
        random.shuffle(gk_candidates)
        gk_candidates.sort(key=lambda name: gk_counts[name])
        
        chosen_gk = gk_candidates[0]
        starters[GK_POSITION] = chosen_gk
        gk_counts[chosen_gk] += 1  
        remaining.remove(chosen_gk)
        last_quarter_gk = chosen_gk
        
        random.shuffle(remaining)
        remaining.sort(key=lambda name: field_counts[name])
        shuffled_positions = FIELD_POSITIONS.copy()
        random.shuffle(shuffled_positions)
        
        for pos in shuffled_positions:
            wished_candidates = [p for p in remaining if pos in players_pool[p]]
            if wished_candidates:
                chosen_player = wished_candidates[0]
            else:
                remaining.sort(key=lambda name: (field_counts[name], player_pos_history[name].get(pos, 0)))
                chosen_player = remaining[0]
                
            starters[pos] = chosen_player
            remaining.remove(chosen_player)
            field_counts[chosen_player] += 1
            player_pos_history[chosen_player][pos] = player_pos_history[chosen_player].get(pos, 0) + 1
            
        lineups[f"{q}쿼터"] = {
            "starters": [starters[pos] for pos in ALL_POSITIONS],
            "subs": remaining,
            "field_snapshot": field_counts.copy(),
            "gk_snapshot": gk_counts.copy(),
            "history_snapshot": {name: player_pos_history[name].copy() for name in active_players}
        }
    return lineups

st.markdown("---")

if st.button("🚀 KOKO FC 라인업 짜기", type="primary", use_container_width=True):
    active_count = sum(1 for att in st.session_state.attendance.values() if att)
    if active_count < 5:
        st.error("출석 선수가 최소 5명 이상이어야 합니다.")
    else:
        st.session_state.lineups = generate_fair_lineups(st.session_state.players_dict, st.session_state.attendance, total_quarters)

# --- 결과 출력 영역 ---
if st.session_state.lineups:
    st.subheader("📋 생성된 라인업")
    
    kakao_text = "⚽ KOKO FC 경기 라인업 ⚽\n\n"
    for quarter, data in st.session_state.lineups.items():
        kakao_text += f"-----[{quarter}]-----\n"
        kakao_text += f"🔱 PIVO : {data['starters'][0] or '미정'}\n"
        kakao_text += f"◀️ ALA_L : {data['starters'][1] or '미정'}\n"
        kakao_text += f"▶️ ALA_R : {data['starters'][2] or '미정'}\n"
        kakao_text += f"🛡️ FIXO : {data['starters'][3] or '미정'}\n"
        kakao_text += f"🧤 GOLEIRO : {data['starters'][4] or '미정'}\n\n"

    # 카톡 복사 버튼
    html_button_code = f"""
    <button onclick="copyToClipboard()" style="width: 100%; background: linear-gradient(135deg, #FEE500, #FACC15); color: #381E1F; border: none; padding: 14px; font-size: 15px; font-weight: bold; border-radius: 10px; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.08);">💬 카카오톡 공유용 라인업 복사</button>
    <script>
    function copyToClipboard() {{
        var textToCopy = `{kakao_text}`;
        var textArea = document.createElement("textarea");
        textArea.value = textToCopy;
        textArea.style.position = "fixed";
        document.body.appendChild(textArea);
        textArea.select();
        try {{
            if(document.execCommand('copy')) {{ alert('📋 라인업이 복사되었습니다! 카톡방에 붙여넣으세요.'); }}
        }} catch (err) {{
            navigator.clipboard.writeText(textToCopy).then(function() {{ alert('📋 라인업이 복사되었습니다!'); }});
        }}
        document.body.removeChild(textArea);
    }}
    </script>"""
    st.components.v1.html(html_button_code, height=52)
    
    with st.expander("⚠️ 복사가 안 될 경우 여기서 드래그 복사"):
        st.code(kakao_text, language="text")

    # [모바일 UX 초필살기] 데이터 에디터를 모바일용 카드 뷰 스타일로 커스텀 렌더링
    st.write("### 🏃 쿼터별 스쿼드 시트")
    
    card_html = ""
    for quarter, data in st.session_state.lineups.items():
        card_html += f"""
        <div style="background-color: #ffffff; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <div style="font-weight: bold; font-size: 15px; color: #1E293B; margin-bottom: 8px; border-bottom: 2px solid #3B82F6; padding-bottom: 4px;">🔥 {quarter}</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 13px;">
                <div><span style="color:#EF4444; font-weight:600;">🔱 PIVO:</span> {data['starters'][0]}</div>
                <div><span style="color:#0284C7; font-weight:600;">🛡️ FIXO:</span> {data['starters'][3]}</div>
                <div><span style="color:#2563EB; font-weight:600;">◀️ ALA_L:</span> {data['starters'][1]}</div>
                <div><span style="color:#D97706; font-weight:600;">▶️ ALA_R:</span> {data['starters'][2]}</div>
                <div style="grid-column: span 2;"><span style="color:#4B5563; font-weight:600;">🧤 GOLEIRO:</span> {data['starters'][4]}</div>
            </div>
            <div style="margin-top: 6px; font-size: 11px; color: #64748B; background: #F8FAFC; padding: 4px 8px; border-radius: 6px;">
                🔹 대기 명단: {", ".join(data['subs']) if data['subs'] else "없음"}
            </div>
        </div>
        """
    st.html(card_html)

    # 데이터 수정용 순정 툴도 아래에 보조용으로 유지
    with st.expander("✏️ 현장에서 수동으로 이름 직접 편집하기"):
        edited_data = []
        for quarter, data in st.session_state.lineups.items():
            row = {"쿼터": quarter}
            for idx, pos in enumerate(ALL_POSITIONS):
                row[POS_CONFIG[pos]['label']] = data["starters"][idx] or "미정"
            edited_data.append(row)
        st.data_editor(edited_data, use_container_width=True, num_rows="fixed")

    # 8. 통계부 모바일 최적화 표 (가로 스크롤 가능하게 래핑 감싸기)
    st.subheader("📊 출전 분배 통계")
    last_quarter = list(st.session_state.lineups.keys())[-1]
    final_fields = st.session_state.lineups[last_quarter]["field_snapshot"]
    final_gks = st.session_state.lineups[last_quarter]["gk_snapshot"]
    
    stats_data = []
    for name in final_fields.keys():
        stats_data.append({
            "선수명": name,
            "🧤 GK": f"{final_gks.get(name, 0)}회",
            "🏃 필드": f"{final_fields.get(name, 0)}회",
            "총 출전": f"{final_gks.get(name, 0) + final_fields.get(name, 0)}회"
        })
    df_stats = pd.DataFrame(stats_data)
    tbody = df_stats.to_html(index=False, header=False)
    tbody_content = tbody.split('<tbody>')[1].split('</tbody>')[0] if '<tbody>' in tbody else ''
    
    custom_table_html = f"""
    <div style="overflow-x: auto; -webkit-overflow-scrolling: touch; border-radius: 8px; border: 1px solid #E2E8F0;">
        <table style="width: 100%; border-collapse: collapse; font-size: 13px; text-align: center; min-width: 340px;">
            <thead>
                <tr style="background-color: #F8FAFC; border-bottom: 2px solid #E2E8F0; color:#475569;">
                    <th style="padding: 10px;">선수명</th>
                    <th style="padding: 10px;">🧤 GK</th>
                    <th style="padding: 10px;">🏃 필드</th>
                    <th style="padding: 10px; background-color:#EFF6FF;">🔥 총합</th>
                </tr>
            </thead>
            <tbody>
                {tbody_content}
            </tbody>
        </table>
    </div>
    <style>
        tbody tr {{ border-bottom: 1px solid #F1F5F9; }}
        tbody td {{ padding: 10px 6px; }}
        tbody td:first-child {{ font-weight: bold; color: #0F172A; }}
        tbody td:last-child {{ font-weight: bold; background-color: #F9FEEB; }}
    </style>
    """
    st.html(custom_table_html)
