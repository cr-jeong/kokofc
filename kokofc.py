import streamlit as st
import random
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 포지션 및 기본 설정 (이모지와 컬러 매칭 개선)
POS_CONFIG = {
    'PIVO (공격)': {'emoji': '🔥', 'label': '🔥 PIVO (공격)', 'color': '#EF4444'},
    'ALA_L (좌윙)': {'emoji': '⚡', 'label': '⚡ ALA_L (좌윙)', 'color': '#3B82F6'},
    'ALA_R (우윙)': {'emoji': '✨', 'label': '✨ ALA_R (우윙)', 'color': '#10B981'},
    'FIXO (수비)': {'emoji': '🛡️', 'label': '🛡️ FIXO (수비)', 'color': '#F59E0B'},
    'GOLEIRO (키퍼)': {'emoji': '🧤', 'label': '🧤 GOLEIRO (키퍼)', 'color': '#6B7280'}
}
FIELD_POSITIONS = ['PIVO (공격)', 'ALA_L (좌윙)', 'ALA_R (우윙)', 'FIXO (수비)']
GK_POSITION = 'GOLEIRO (키퍼)'
ALL_POSITIONS = FIELD_POSITIONS + [GK_POSITION]

# 페이지 설정 (기기 화면에 맞춰 컴팩트하게 조정)
st.set_page_config(page_title="KOKO FC 라인업 매니저", layout="centered")

# 헤더 디자인 개선 (카드 스타일 효과)
st.markdown("""
    <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
        <h1 style="color: white; margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">⚽ KOKO FC 😈 라인업 매니저</h1>
        <p style="color: #c7d2fe; margin: 8px 0 0 0; font-size: 13px; opacity: 0.9;">참석 체크 • 실시간 포지션 수정 • 카톡 공유</p>
    </div>
""", unsafe_allow_html=True)

# 구글 스프레딧시트 연결 초기화
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

@st.dialog("🎯 희망 포지션 수정")
def edit_position_dialog(player_name):
    st.markdown(f"🏃‍♂️ **{player_name}** 선수의 희망 포지션을 선택하세요.")
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

# 서브헤더 및 가이드 카드화
st.markdown("### ⚙️ 경기 설정 및 명단 관리")
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("<p style='font-weight: bold; margin-bottom: 5px;'>① 선수 추가</p>", unsafe_allow_html=True)
        with st.form(key="player_add_form", clear_on_submit=True):
            name_input = st.text_input("선수 이름", placeholder="이름 입력", label_visibility="collapsed")
            wished_input = st.multiselect(
                "희망 포지션 선택", 
                options=ALL_POSITIONS,
                format_func=lambda x: POS_CONFIG[x]['label'],
                placeholder="포지션 선택 (미선택 시 전체)"
            )
            submit_button = st.form_submit_button("🏃 등록", use_container_width=True)
            if submit_button:
                name = name_input.strip()
                if name:
                    if name in st.session_state.players_dict:
                        st.warning(f"'{name}' 선수는 이미 있습니다.")
                    else:
                        st.session_state.players_dict[name] = wished_input if wished_input else ALL_POSITIONS.copy()
                        st.session_state.attendance[name] = True
                        save_players_to_db(st.session_state.players_dict)
                        st.rerun()

with col2:
    with st.container(border=True):
        st.markdown("<p style='font-weight: bold; margin-bottom: 5px;'>② 경기 쿼터</p>", unsafe_allow_html=True)
        total_quarters = st.number_input("오늘 경기 쿼터 수", min_value=1, max_value=12, value=7, label_visibility="collapsed")
        st.write("") # 간격 맞추기용
        if st.button("🔄 시트 동기화", use_container_width=True):
            st.cache_data.clear()
            st.session_state.players_dict = load_players_from_db()
            st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}
            st.rerun()

# 참여 명단 출력 영역 UI 개선
st.markdown(f"### 👥 등록 선수 ({len(st.session_state.players_dict)}명)")
if st.session_state.players_dict:
    # 스크롤 가능한 세련된 박스 형태로 선수 명단 묶기
    with st.container(border=True):
        for player, positions in st.session_state.players_dict.items():
            emojis = "".join([POS_CONFIG[p]['emoji'] for p in positions if p in POS_CONFIG])
            col_att, col_p, col_edit, col_b = st.columns([1, 3, 1.2, 1])
            
            with col_att:
                st.session_state.attendance[player] = st.checkbox("참석", value=st.session_state.attendance.get(player, True), key=f"att_{player}", label_visibility="collapsed")
            with col_p:
                color = "#1E293B" if st.session_state.attendance[player] else "#94A3B8"
                text_style = "font-weight:bold;" if st.session_state.attendance[player] else "text-decoration: line-through; opacity: 0.6;"
                st.markdown(f"<div style='padding-top: 4px;'><span style='color:{color}; {text_style}'>🏃 {player}</span> <span style='font-size:12px; margin-left:5px;'>{emojis}</span></div>", unsafe_allow_html=True)
            with col_edit:
                if st.button("⚙️ 수정", key=f"edit_btn_{player}", use_container_width=True):
                    edit_position_dialog(player)
            with col_b:
                if st.button("제거", key=f"del_{player}", use_container_width=True, type="secondary"):
                    del st.session_state.players_dict[player]
                    if player in st.session_state.attendance: del st.session_state.attendance[player]
                    save_players_to_db(st.session_state.players_dict)
                    st.rerun()
else:
    st.info("등록된 선수가 없습니다.")

st.markdown("---")

# 알고리즘 (기존 로직 유지)
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

if st.button("🚀 KOKO FC 라인업 자동 생성", type="primary", use_container_width=True):
    active_count = sum(1 for att in st.session_state.attendance.values() if att)
    if active_count < 5:
        st.error("오늘 경기 참석자가 최소 5명 이상이어야 합니다.")
    else:
        st.session_state.lineups = generate_fair_lineups(st.session_state.players_dict, st.session_state.attendance, total_quarters)

# 결과 출력 섹션
if st.session_state.lineups:
    st.markdown("## 📋 경기 라인업 결과")
    
    kakao_text = "⚽ KOKO FC 경기 라인업 ⚽\n\n"
    for quarter, data in st.session_state.lineups.items():
        kakao_text += f"-----[{quarter}]-----\n"
        kakao_text += f"🔥 PIVO : {data['starters'][0] or '미지정'}\n"
        kakao_text += f"⚡ ALA_L : {data['starters'][1] or '미지정'}\n"
        kakao_text += f"✨ ALA_R : {data['starters'][2] or '미정'}\n"
        kakao_text += f"🛡️ FIXO : {data['starters'][3] or '미지정'}\n"
        kakao_text += f"🧤 GOLEIRO : {data['starters'][4] or '미정'}\n"
        kakao_text += "\n"

    # 복사 버튼 스타일 고도화 (더 부드러운 라운딩과 그림자)
    html_button_code = f"""<button onclick="copyToClipboard()" style="width: 100%; background: linear-gradient(135deg, #FEE500, #FCD34D); color: #381E1F; border: none; padding: 14px; font-size: 15px; font-family: -apple-system, sans-serif; font-weight: bold; border-radius: 10px; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: all 0.2s;" onmouseover="this.style.opacity='0.9';" onmouseout="this.style.opacity='1';">💬 카카오톡 공유용 라인업 복사하기</button>
<script>
function copyToClipboard() {{
    var textToCopy = `{kakao_text}`;
    var textArea = document.createElement("textarea");
    textArea.value = textToCopy;
    textArea.style.position = "fixed";
    document.body.appendChild(textArea);
    textArea.select();
    try {{
        var successful = document.execCommand('copy');
        if(successful) {{ alert('📋 [KOKO FC] 카톡 공유용 텍스트가 복사되었습니다!'); }}
        else {{ alert('복사 실패'); }}
    }} catch (err) {{
        navigator.clipboard.writeText(textToCopy).then(function() {{
            alert('📋 [KOKO FC] 카톡 공유용 텍스트가 복사되었습니다!');
        }}).catch(function(e) {{ alert('복사 실패'); }});
    }}
    document.body.removeChild(textArea);
}}
</script>"""
    
    st.components.v1.html(html_button_code, height=55)
    st.caption("💡 팁: 생성된 표의 셀을 더블클릭해서 이름을 직접 수정할 수 있습니다.")
    
    # 데이터 에디터 표 생성
    edited_data = []
    for quarter, data in st.session_state.lineups.items():
        row = {"쿼터": quarter}
        for idx, pos in enumerate(ALL_POSITIONS):
            header_label = POS_CONFIG[pos]['label']
            row[header_label] = data["starters"][idx] or "미지정"
        edited_data.append(row)
        
    st.data_editor(edited_data, use_container_width=True, num_rows="fixed")
    
    # 📊 최종 통계 HTML 표 스타일 대폭 개선 (모던 다크/라이트 테마 매칭, 패딩 최적화)
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
            "🏃 필드": f"{final_fields[name]}회",
            "🔥 PIVO": f"{player_history['PIVO (공격)']}회",
            "⚡ ALA_L": f"{player_history['ALA_L (좌윙)']}회",
            "✨ ALA_R": f"{player_history['ALA_R (우윙)']}회",
            "🛡️ FIXO": f"{player_history.get('🛡️ FIXO (수비)', player_history.get('FIXO (수비)', 0))}회",
            "🧤 GK": f"{final_gks[name]}회"
        })
    
    df_stats = pd.DataFrame(stats_data)
    
    # 테두리를 없애고 가로 구분선만 깔끔하게 넣는 모던 UI 스타일 CSS
    html_code = df_stats.to_html(index=False, classes='modern-table')
    custom_html = f"""
    <div style="overflow-x: auto; width: 100%; margin-top: 10px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <style>
            .modern-table {{
                width: 100%;
                border-collapse: collapse;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 13px;
                text-align: center;
                background-color: #ffffff;
                color: #334155;
            }}
            .modern-table th {{
                background-color: #f8fafc;
                color: #475569;
                font-weight: 600;
                padding: 12px 8px;
                border-bottom: 2px solid #e2e8f0;
            }}
            .modern-table td {{
                padding: 12px 8px;
                border-bottom: 1px solid #f1f5f9;
            }}
            .modern-table tr:hover {{
                background-color: #f8fafc;
            }}
            /* 첫 번째 열(선수명) 강조 */
            .modern-table td:nth-child(1) {{
                font-weight: bold;
                color: #0f172a;
            }}
        </style>
        {html_code}
    </div>
    """
    st.html(custom_html)
