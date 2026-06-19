import streamlit as st
import random
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# [UI/UX 디자인 업그레이드] 창과 방패 구도 + 윙어 방향성 + 가독성 최적화 컬러 매칭
POS_CONFIG = {
    'PIVO (공격)': {
        'emoji': '🔱', 
        'label': '🔱 PIVO (공격)', 
        'bg': '#FEE2E2',     # 연한 레드 (공격적, 열정)
        'color': '#B91C1C',  # 딥 레드
        'text': 'PIVO'
    },
    'ALA_L (좌윙)': {
        'emoji': '◀️', 
        'label': '◀️ ALA_L (좌윙)', 
        'bg': '#EFF6FF',     # 연한 블루 (신속, 시원한 돌파)
        'color': '#1D4ED8',  # 딥 블루
        'text': 'ALA_L'
    },
    'ALA_R (우윙)': {
        'emoji': '▶️', 
        'label': '▶️ ALA_R (우윙)', 
        'bg': '#ECFDF5',     # 연한 에메랄드 (안정감 있는 전진)
        'color': '#047857',  # 딥 에메랄드
        'text': 'ALA_R'
    },
    'FIXO (수비)': {
        'emoji': '🛡️', 
        'label': '🛡️ FIXO (수비)', 
        'bg': '#FFF7ED',     # 연한 오렌지/앰버 (든든하고 무게감 있는 수비)
        'color': '#C2410C',  # 딥 오렌지
        'text': 'FIXO'
    },
    'GOLEIRO (키퍼)': {
        'emoji': '🧤', 
        'label': '🧤 GOLEIRO (키퍼)', 
        'bg': '#F1F5F9',     # 톤다운된 슬레이트 그레이 (최후방의 차분함)
        'color': '#475569',  # 묵직한 그레이
        'text': 'GK'
    }
}
FIELD_POSITIONS = ['PIVO (공격)', 'ALA_L (좌윙)', 'ALA_R (우윙)', 'FIXO (수비)']
GK_POSITION = 'GOLEIRO (키퍼)'
ALL_POSITIONS = FIELD_POSITIONS + [GK_POSITION]

# 페이지 설정
st.set_page_config(page_title="⚽ KOKO FC 😈 라인업 매니저", layout="centered")
st.title("⚽ KOKO FC 😈 라인업 매니저")
st.caption("KOKO 화이팅!! 버그 제보 환영")
st.caption("참석 체크 + 앱 내 실시간 포지션 수정 기능 + [카톡 복사] 대기 명단 제외 버전!")

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
    st.write(f"🏃 **{player_name}** 선수의 희망 포지션을 선택하세요.")
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
                        st.rerun()

with col2:
    with st.container(border=True):
        st.write("**② 경기 설정**")
        total_quarters = st.number_input("오늘 경기 쿼터 수 입력", min_value=1, max_value=12, value=7)
        st.write("") 
        if st.button("🔄 구글 시트 수동 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.session_state.players_dict = load_players_from_db()
            st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}
            st.rerun()

# 참여 명단 출력
st.write(f"### 👥 전체 명단 ({len(st.session_state.players_dict)}명)")
if st.session_state.players_dict:
    for player, positions in st.session_state.players_dict.items():
        prev_status = st.session_state.attendance.get(player, True)
        
        # 각 선수를 하나의 깔끔한 카드(테두리) 형태로 분리하여 모바일 가독성 향상
        with st.container(border=True):
            # 구조 단순화: [좌측: 체크박스 & 이름 & 태그] | [우측: 관리 버튼]
            col_content, col_actions = st.columns([3, 1])
            
            with col_content:
                # 이름과 참석 체크박스를 한 줄로 밀착 배치
                col_chk, col_txt = st.columns([0.4, 2.6])
                with col_chk:
                    is_attended = st.checkbox("참석", value=prev_status, key=f"att_{player}", label_visibility="collapsed")
                    if is_attended != prev_status:
                        st.session_state.attendance[player] = is_attended
                        st.rerun()
                
                with col_txt:
                    color = "#1E293B" if is_attended else "#94A3B8"
                    text_style = "font-weight:bold; font-size:16px;" if is_attended else "text-decoration: line-through; opacity: 0.4; font-size:16px;"
                    st.markdown(f"<div style='padding-top: 1px;'><span style='color:{color}; {text_style}'>🏃 {player}</span></div>", unsafe_allow_html=True)
                
                # 포지션 배지는 이름 아래 공간에 자연스럽게 Wrap 되도록 배치 (줄바꿈 현상 역이용)
                badge_html = ""
                for p in positions:
                    if p in POS_CONFIG:
                        cfg = POS_CONFIG[p]
                        bg_color = "#E2E8F0" if not is_attended else cfg['bg']
                        text_color = "#94A3B8" if not is_attended else cfg['color']
                        badge_html += f'<span style="background-color: {bg_color}; color: {text_color}; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; margin-right: 4px; margin-bottom: 4px; display: inline-block;">{cfg["emoji"]} {cfg["text"]}</span>'
                
                badge_opacity = "1.0" if is_attended else "0.4"
                st.markdown(f"<div style='margin-top: 6px; margin-left: 2px; opacity: {badge_opacity};'>{badge_html}</div>", unsafe_allow_html=True)
            
            with col_actions:
                # 우측 정렬된 관리 버튼 (모바일에서도 찌그러지지 않고 세로로 이쁘게 스택됨)
                st.write("<div style='margin-top: 2px;'></div>", unsafe_allow_html=True) # 약간의 상단 패딩
                if st.button("⚙️ 수정", key=f"edit_btn_{player}", use_container_width=True):
                    edit_position_dialog(player)
                
                if st.button("제거", key=f"del_{player}", use_container_width=True, type="secondary"):
                    del st.session_state.players_dict[player]
                    if player in st.session_state.attendance:
                        del st.session_state.attendance[player]
                    save_players_to_db(st.session_state.players_dict)
                    st.rerun()
else:
    st.info("등록된 선수가 없습니다.")

st.markdown("---")

# 공정한 라인업 생성 알고리즘
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

# 실행 버튼
if st.button("🚀 KOKO FC 라인업 자동 생성", type="primary", use_container_width=True):
    active_count = sum(1 for att in st.session_state.attendance.values() if att)
    if active_count < 5:
        st.error("오늘 경기 참석자가 최소 5명 이상이어야 합니다.")
    else:
        st.session_state.lineups = generate_fair_lineups(st.session_state.players_dict, st.session_state.attendance, total_quarters)

# 결과 출력 섹션
if st.session_state.lineups:
    st.write("## 📋 경기 라인업 결과")
    
    kakao_text = "⚽ KOKO FC 경기 라인업 ⚽\n\n"
    for quarter, data in st.session_state.lineups.items():
        kakao_text += f"-----[{quarter}]-----\n"
        kakao_text += f"🔱 PIVO : {data['starters'][0] or '미지정'}\n"
        kakao_text += f"◀️ ALA_L : {data['starters'][1] or '미지정'}\n"
        kakao_text += f"▶️ ALA_R : {data['starters'][2] or '미정'}\n"
        kakao_text += f"🛡️ FIXO : {data['starters'][3] or '미지정'}\n"
        kakao_text += f"🧤 GOLEIRO : {data['starters'][4] or '미정'}\n"
        kakao_text += "\n"

    html_button_code = f"""<button onclick="copyToClipboard()" style="width: 100%; background: linear-gradient(135deg, #FEE500, #FCD34D); color: #381E1F; border: none; padding: 14px; font-size: 15px; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-weight: bold; border-radius: 10px; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: opacity 0.2s;" onmouseover="this.style.opacity='0.9';" onmouseout="this.style.opacity='1';">💬 카카오톡 공유용 라인업 복사하기</button>
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
    st.info("💡 팁: 생성된 표의 셀을 더블클릭해서 이름을 직접 수정할 수 있습니다.")
    
    edited_data = []
    for quarter, data in st.session_state.lineups.items():
        row = {"쿼터": quarter}
        for idx, pos in enumerate(ALL_POSITIONS):
            header_label = POS_CONFIG[pos]['label']
            row[header_label] = data["starters"][idx] or "미지정"
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
            "🧤 GK": f"{final_gks[name]}회",
            "🏃 필드": f"{final_fields[name]}회",
            "🔱 PIVO": f"{player_history['PIVO (공격)']}회",
            "◀️ ALA_L": f"{player_history['ALA_L (좌윙)']}회",
            "▶️ ALA_R": f"{player_history['ALA_R (우윙)']}회",
            "🛡️ FIXO": f"{player_history.get('🛡️ FIXO (수비)', player_history.get('FIXO (수비)', 0))}회"
        })
    
    df_stats = pd.DataFrame(stats_data)
    html_tbody = df_stats.to_html(index=False, header=False, classes='modern-table')
    tbody_content = html_tbody.split('<tbody>')[1].split('</tbody>')[0]
    
    custom_html = f"""
    <div style="overflow-x: auto; width: 100%; margin-top: 10px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <style>
            .modern-table {{
                width: 100%;
                border-collapse: collapse;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 13px;
                text-align: center !important;
                background-color: #ffffff;
                color: #334155;
            }}
            .modern-table th {{
                background-color: #f8fafc;
                color: #475569;
                font-weight: 600;
                padding: 10px 8px;
                border: 1px solid #e2e8f0;
                text-align: center !important;
            }}
            .modern-table th.main-header {{
                background-color: #f1f5f9;
                color: #1e293b;
                font-size: 14px;
            }}
            .modern-table td {{
                padding: 12px 8px;
                border: 1px solid #f1f5f9;
                text-align: center !important; 
            }}
            .modern-table tr:hover {{
                background-color: #f8fafc;
            }}
            .modern-table td:nth-child(1) {{
                font-weight: bold;
                color: #0f172a;
            }}
        </style>
        <table class="modern-table">
            <thead>
                <tr>
                    <th rowspan="2" style="vertical-align: middle;">선수명</th>
                    <th rowspan="2" style="vertical-align: middle;">🧤 GK</th>
                    <th rowspan="2" style="vertical-align: middle;">🏃 필드</th>
                    <th colspan="4" class="main-header">상세 (필드 포지션별 출전)</th>
                </tr>
                <tr>
                    <th>🔱 PIVO</th>
                    <th>◀️ ALA_L</th>
                    <th>▶️ ALA_R</th>
                    <th>🛡️ FIXO</th>
                </tr>
            </thead>
            <tbody>
                {tbody_content}
            </tbody>
        </table>
    </div>
    """
    st.html(custom_html)
