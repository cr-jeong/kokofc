import streamlit as st
import random
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 포지션 및 기본 설정 (영어 이름 유지 + 새 이모지 반영)
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

# 페이지 설정
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
        st.write("") 
        if st.button("🔄 구글 시트 수동 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.session_state.players_dict = load_players_from_db()
            st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}
            st.success("구글 시트에서 명단을 다시 불러왔습니다!")
            st.rerun()

# 참여 명단 출력 (시차 0ms, 완벽 동기화 버전! ⚡)
st.write(f"### 👥 전체 명단 ({len(st.session_state.players_dict)}명)")
if st.session_state.players_dict:
    # 이름과 태그를 브라우저 단에서 동시에 제어하는 CSS
    st.markdown(
        """
        <style>
        /* 기본 체크박스 라벨 스타일 */
        .stCheckbox p {
            font-size: 16px !important;
            font-weight: bold !important;
        }
        
        /* 1. 체크 해제 시 이름 흐리게 */
        .stCheckbox [aria-checked="false"] ~ div p {
            opacity: 0.4 !important;
            text-decoration: line-through !important;
            color: #9CA3AF !important;
        }
        
        /* 2. 체크 해제 시 하단 태그도 시차 없이 '동시에' 흐리게 (핵심!) */
        .stCheckbox:has([aria-checked="false"]) + div .player-tags {
            opacity: 0.4 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 세련되고 부드러운 파스텔톤 태그 스타일 정의
    TAG_STYLES = {
        'PIVO (공격)': 'background-color: #FEE2E2; color: #EF4444;', 
        'ALA_L (좌윙)': 'background-color: #E0F2FE; color: #0284C7;', 
        'ALA_R (우윙)': 'background-color: #FEF3C7; color: #D97706;', 
        'FIXO (수비)': 'background-color: #DCFCE7; color: #16A34A;', 
        'GOLEIRO (키퍼)': 'background-color: #F3F4F6; color: #4B5563;' 
    }

    with st.container(border=True):
        for player in list(st.session_state.players_dict.keys()):
            positions = st.session_state.players_dict[player]
            
            # 포지션 태그 HTML 생성
            tag_htmls = []
            for p in positions:
                if p in POS_CONFIG:
                    label = POS_CONFIG[p]['label']
                    style = TAG_STYLES.get(p, 'background-color: #E5E7EB; color: #4B5563;')
                    tag_htmls.append(f"<span style='padding: 3px 8px; margin-right: 4px; border-radius: 6px; font-size: 11px; font-weight: 600; {style}'>{label}</span>")
            tags_inline = "".join(tag_htmls)
            
            # 레이아웃 분할: 왼쪽(이름+태그), 오른쪽(버튼)
            col_left, col_right = st.columns([2.8, 1.2])
            
            with col_left:
                is_active = st.session_state.attendance.get(player, True)
                
                # 순정 체크박스
                cb_label = f"🏃 {player}"
                selected = st.checkbox(cb_label, value=is_active, key=f"att_v9_{player}")
                st.session_state.attendance[player] = selected
                
                # 파이썬 opacity 조건문을 빼고 CSS 클래스(player-tags)만 부여!
                st.write(
                    f"""<div class='player-tags' style='padding-left: 28px; margin-top: 4px; margin-bottom: 12px;'>
                        <div style='display: flex; flex-wrap: wrap; gap: 4px;'>
                            {tags_inline}
                        </div>
                    </div>""", 
                    unsafe_allow_html=True
                )
                
            with col_right:
                st.write("<div style='margin-top: 4px;'></div>", unsafe_allow_html=True)
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("⚙️", key=f"edit_btn_{player}", use_container_width=True, help="포지션 수정"):
                        edit_position_dialog(player)
                with btn_col2:
                    if st.button("❌", key=f"del_{player}", use_container_width=True, help="선수 제거"):
                        del st.session_state.players_dict[player]
                        if player in st.session_state.attendance:
                            del st.session_state.attendance[player]
                        save_players_to_db(st.session_state.players_dict)
                        st.rerun()
            
            st.write("<div style='margin: 4px 0; border-bottom: 1px dashed #E5E7EB;'></div>", unsafe_allow_html=True)
else:
    st.info("등록된 선수가 없습니다. 구글 시트를 확인하거나 선수를 직접 추가해 보세요.")
    
st.markdown("---")

# 공정한 라인업 생성 알고리즘 (기존 로직 유지)
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
        st.error("오늘 경기 참석자가 최소 5명 이상이어야 라인업을 짜 수 있습니다! 체크박스를 확인해주세요.")
    else:
        st.session_state.lineups = generate_fair_lineups(
            st.session_state.players_dict, 
            st.session_state.attendance, 
            total_quarters
        )

# 결과 출력 섹션
if st.session_state.lineups:
    st.write("## 📋 경기 라인업 결과")
    
    # 카톡 공유용 텍스트 포맷팅
    kakao_text = "⚽ KOKO FC 경기 라인업 ⚽\n\n"
    for quarter, data in st.session_state.lineups.items():
        kakao_text += f"-----[{quarter}]-----\n"
        kakao_text += f"🔱 PIVO : {data['starters'][0] or '미지정'}\n"
        kakao_text += f"◀️ ALA_L : {data['starters'][1] or '미지정'}\n"
        kakao_text += f"▶️ ALA_R : {data['starters'][2] or '미정'}\n"
        kakao_text += f"🛡️ FIXO : {data['starters'][3] or '미지정'}\n"
        kakao_text += f"🧤 GOLEIRO : {data['starters'][4] or '미정'}\n"
        kakao_text += "\n"

    # 공유하기 카톡 노란색 버튼 유지
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
        if(successful) {{
            alert('📋 [KOKO FC] 카톡 공유용 텍스트가 복사되었습니다!');
        }} else {{
            alert('복사 실패');
        }}
    }} catch (err) {{
        navigator.clipboard.writeText(textToCopy).then(function() {{
            alert('📋 [KOKO FC] 카톡 공유용 텍스트가 복사되었습니다!');
        }}).catch(function(e) {{
            alert('복사 실패');
        }});
    }}
    document.body.removeChild(textArea);
}}
</script>"""
    
    st.components.v1.html(html_button_code, height=55)
    st.info("💡 팁: 생성된 표의 셀을 더블클릭해서 이름을 직접 수정할 수 있습니다.")
    
    # 데이터 에디터 표 생성
    edited_data = []
    for quarter, data in st.session_state.lineups.items():
        row = {"쿼터": quarter}
        for idx, pos in enumerate(ALL_POSITIONS):
            header_label = POS_CONFIG[pos]['label']
            row[header_label] = data["starters"][idx] or "미지정"
        edited_data.append(row)
        
    st.data_editor(edited_data, use_container_width=True, num_rows="fixed")
    
    # 최종 포지션별 상세 출전 통계 표 가공
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
            "🧤 GOLEIRO": f"{final_gks[name]}회",
            "🏃 필드": f"{final_fields[name]}회",
            "🔱 PIVO": f"{player_history['PIVO (공격)']}회",
            "◀️ ALA_L": f"{player_history['ALA_L (좌윙)']}회",
            "▶️ ALA_R": f"{player_history['ALA_R (우윙)']}회",
            "🛡️ FIXO": f"{player_history.get('🛡️ FIXO (수비)', player_history.get('FIXO (수비)', 0))}회"
        })
    
    df_stats = pd.DataFrame(stats_data)
    
    # 데이터 본문(tbody)의 html 코드만 추출
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
                    <th rowspan="2" style="vertical-align: middle;">🧤 GOLEIRO</th>
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
