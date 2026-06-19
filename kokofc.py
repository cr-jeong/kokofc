import streamlit as st
import random
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 기본 설정 및 포지션 구성
POS_CONFIG = {
    'PIVO (공격)': {'emoji': '🔱', 'label': '🔱 PIVO', 'color': 'red'},
    'ALA_L (좌윙)': {'emoji': '◀️', 'label': '◀️ ALA_L', 'color': 'blue'},
    'ALA_R (우윙)': {'emoji': '▶️', 'label': '▶️ ALA_R', 'color': 'orange'},
    'FIXO (수비)': {'emoji': '🛡️', 'label': '🛡️ FIXO', 'color': 'green'},
    'GOLEIRO (키퍼)': {'emoji': '🧤', 'label': '🧤 GOLEIRO', 'color': 'gray'}
}
FIELD_POSITIONS = ['PIVO (공격)', 'ALA_L (좌윙)', 'ALA_R (우윙)', 'FIXO (수비)']
GK_POSITION = 'GOLEIRO (키퍼)'
ALL_POSITIONS = FIELD_POSITIONS + [GK_POSITION]

st.set_page_config(page_title="KOKO FC 라인업 매니저", layout="centered")

# CSS 커스텀 지연 스타일 주입 (체크박스 해제 시 흐리게 처리하는 고난도 셀렉터 유지)
st.markdown("""
    <style>
    .stCheckbox [aria-checked="false"] ~ div p {
        opacity: 0.35 !important;
        text-decoration: line-through !important;
        color: #9CA3AF !important;
    }
    div[data-testid="stForm"] {
        border-radius: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 구글 시트 연동 및 캐싱
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
        st.error(f"구글 시트 로드 에러: {e}")
        return {}

# 3. 세션 상태 초기화 및 동기화
if 'first_load_done' not in st.session_state:
    st.session_state.players_dict = load_players_from_db()
    st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}
    st.session_state.lineups = None
    st.session_state.first_load_done = True

# 데이터 동기화 안전장치
for p in st.session_state.players_dict.keys():
    if p not in st.session_state.attendance:
        st.session_state.attendance[p] = True

# 4. 다이얼로그 (팝업창)
@st.dialog("🎯 희망 포지션 수정")
def edit_position_dialog(player_name):
    st.write(f"🏃 **{player_name}** 선수의 선호 포지션을 설정하세요.")
    current_wishes = st.session_state.players_dict[player_name]
    
    new_wishes = st.multiselect(
        "포지션 (미선택 시 전포지션 가능)",
        options=ALL_POSITIONS,
        default=[p for p in current_wishes if p in ALL_POSITIONS],
        format_func=lambda x: POS_CONFIG[x]['label']
    )
    
    if st.button("💾 변경사항 저장", use_container_width=True, type="primary"):
        st.session_state.players_dict[player_name] = new_wishes if new_wishes else ALL_POSITIONS.copy()
        st.success("수정 완료!")
        st.rerun()

# 5. [UX 개선] 사이드바로 설정 창 격리하기
with st.sidebar:
    st.title("😈 KOKO FC 기획실")
    st.subheader("⚙️ 경기 및 선수 세팅")
    
    total_quarters = st.number_input("오늘 경기 총 쿼터 수", min_value=1, max_value=12, value=7)
    
    with st.form(key="player_add_form", clear_on_submit=True):
        st.write("**➕ 신규 임시 선수 등록**")
        name_input = st.text_input("선수 이름", placeholder="홍길동")
        wished_input = st.multiselect(
            "희망 포지션", 
            options=ALL_POSITIONS,
            format_func=lambda x: POS_CONFIG[x]['label']
        )
        if st.form_submit_button("등록하기", use_container_width=True):
            name = name_input.strip()
            if name:
                if name in st.session_state.players_dict:
                    st.warning("이미 존재하는 이름입니다.")
                else:
                    st.session_state.players_dict[name] = wished_input if wished_input else ALL_POSITIONS.copy()
                    st.session_state.attendance[name] = True
                    st.success(f"{name} 등록 완료!")
                    st.rerun()
            else:
                st.error("이름을 입력해주세요.")

    if st.button("🔄 구글 시트 수동 동기화", use_container_width=True):
        st.cache_data.clear()
        st.session_state.players_dict = load_players_from_db()
        st.session_state.attendance = {p: True for p in st.session_state.players_dict.keys()}
        st.success("최신 명단 동기화 완료!")
        st.rerun()

# 6. 메인 화면 레이아웃 시작
st.title("⚽ KOKO FC 라인업 매니저")
st.markdown("---")

# 7. 참석 명단 관리부 (메인 센터 배치)
st.subheader(f"👥 참석 체크 리스트 ({len(st.session_state.players_dict)}명 등록됨)")

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
            
            # 레이아웃 비율 고정하여 가로 정렬 안정화
            col_left, col_mid, col_right = st.columns([1.5, 3.5, 1.0])
            
            with col_left:
                selected = st.checkbox(f"🏃 {player}", value=is_active, key=f"chk_{player}")
                st.session_state.attendance[player] = selected
                
            with col_mid:
                # 미려한 인라인 플렉스 배지 스크립트
                tag_htmls = []
                for p in positions:
                    if p in POS_CONFIG:
                        label = POS_CONFIG[p]['label']
                        style = TAG_STYLES.get(p, '')
                        tag_htmls.append(f"<span style='padding: 2px 6px; margin: 2px; border-radius: 4px; font-size: 11px; font-weight: 600; {style}'>{label}</span>")
                opacity_val = "1.0" if selected else "0.3"
                st.markdown(f"<div style='display: flex; flex-wrap: wrap; align-items: center; min-height: 32px; opacity: {opacity_val};'>{''.join(tag_htmls)}</div>", unsafe_allow_html=True)
                
            with col_right:
                btn_c1, btn_c2 = st.columns(2)
                with btn_c1:
                    if st.button("⚙️", key=f"ed_{player}", help="포지션 수정", use_container_width=True):
                        edit_position_dialog(player)
                with btn_c2:
                    if st.button("❌", key=f"del_{player}", help="선수 삭제", use_container_width=True):
                        del st.session_state.players_dict[player]
                        if player in st.session_state.attendance: del st.session_state.attendance[player]
                        st.rerun()
else:
    st.info("등록된 선수가 없습니다. 왼쪽 사이드바에서 동기화하거나 등록해주세요.")

# 8. 알고리즘 로직 (동일하게 유지하되 데이터 딕셔너리 안전장치 보강)
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
        
        # GK 선정
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
        
        # 필드진 선정
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

# 9. 실행 및 결과 출력
if st.button("🚀 KOKO FC 라인업 자동 생성", type="primary", use_container_width=True):
    active_count = sum(1 for att in st.session_state.attendance.values() if att)
    if active_count < 5:
        st.error("체크된 참석 선수가 최소 5명 이상이어야 합니다.")
    else:
        st.session_state.lineups = generate_fair_lineups(st.session_state.players_dict, st.session_state.attendance, total_quarters)

if st.session_state.lineups:
    st.subheader("📋 경기 라인업 결과")
    
    # 카톡 복사 텍스트 포맷팅
    kakao_text = "⚽ KOKO FC 경기 라인업 ⚽\n\n"
    for quarter, data in st.session_state.lineups.items():
        kakao_text += f"-----[{quarter}]-----\n"
        kakao_text += f"🔱 PIVO : {data['starters'][0] or '미지정'}\n"
        kakao_text += f"◀️ ALA_L : {data['starters'][1] or '미지정'}\n"
        kakao_text += f"▶️ ALA_R : {data['starters'][2] or '미정'}\n"
        kakao_text += f"🛡️ FIXO : {data['starters'][3] or '미지정'}\n"
        kakao_text += f"🧤 GOLEIRO : {data['starters'][4] or '미정'}\n\n"

    # 복사 내장 스크립트 버튼 (그라디언트 + 그림자 효과 향상)
    html_button_code = f"""
    <button onclick="copyToClipboard()" style="width: 100%; background: linear-gradient(135deg, #FEE500, #FACC15); color: #381E1F; border: none; padding: 12px; font-size: 14px; font-weight: bold; border-radius: 8px; cursor: pointer; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); transition: transform 0.1s;">💬 카카오톡 공유용 라인업 복사하기</button>
    <script>
    function copyToClipboard() {{
        var textToCopy = `{kakao_text}`;
        var textArea = document.createElement("textarea");
        textArea.value = textToCopy;
        textArea.style.position = "fixed";
        document.body.appendChild(textArea);
        textArea.select();
        try {{
            if(document.execCommand('copy')) {{ alert('📋 카톡 공유용 라인업이 복사되었습니다!'); }}
        }} catch (err) {{
            navigator.clipboard.writeText(textToCopy).then(function() {{ alert('📋 카톡 공유용 라인업이 복사되었습니다!'); }});
        }}
        document.body.removeChild(textArea);
    }}
    </script>"""
    st.components.v1.html(html_button_code, height=50)
    
    # 모바일/앱 인앱 브라우저용 백업 텍스트 에어리어 (안전빵 대안 제공)
    with st.expander("ℹ️ 카톡 복사 버튼이 안 눌리나요? (여기서 수동 복사)"):
        st.code(kakao_text, language="text")

    # 메인 표 (유저 수정 가용)
    edited_data = []
    for quarter, data in st.session_state.lineups.items():
        row = {"쿼터": quarter}
        for idx, pos in enumerate(ALL_POSITIONS):
            row[POS_CONFIG[pos]['label']] = data["starters"][idx] or "미지정"
        edited_data.append(row)
        
    st.info("💡 팁: 생성된 표의 셀을 더블클릭하면 대기 인원이나 전술에 맞게 이름을 직접 바꿀 수 있습니다.")
    st.data_editor(edited_data, use_container_width=True, num_rows="fixed")
    
    # 10. 고품격 출전 스탯 테이블 통계 (HTML/CSS 인젝션 정밀화)
    st.subheader("📊 포지션별 출전 분배 현황")
    last_quarter = list(st.session_state.lineups.keys())[-1]
    final_fields = st.session_state.lineups[last_quarter]["field_snapshot"]
    final_gks = st.session_state.lineups[last_quarter]["gk_snapshot"]
    final_history = st.session_state.lineups[last_quarter]["history_snapshot"]
    
    stats_data = []
    for name in final_fields.keys():
        p_hist = final_history.get(name, {})
        stats_data.append({
            "선수명": name,
            "🧤 GOLEIRO": f"{final_gks.get(name, 0)}회",
            "🏃 필드 합계": f"{final_fields.get(name, 0)}회",
            "🔱 PIVO": f"{p_hist.get('PIVO (공격)', 0)}회",
            "◀️ ALA_L": f"{p_hist.get('ALA_L (좌윙)', 0)}회",
            "▶️ ALA_R": f"{p_hist.get('ALA_R (우윙)', 0)}회",
            "🛡️ FIXO": f"{p_hist.get('FIXO (수비)', 0)}회"
        })
    
    df_stats = pd.DataFrame(stats_data)
    tbody_content = df_stats.to_html(index=False, header=False)
    tbody_content = tbody_content.split('<tbody>')[1].split('</tbody>')[0] if '<tbody>' in tbody_content else ''
    
    custom_table_html = f"""
    <div style="overflow-x: auto; border-radius: 10px; border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
        <table style="width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 13px; text-align: center;">
            <thead>
                <tr style="background-color: #F8FAFC; border-bottom: 2px solid #E2E8F0;">
                    <th rowspan="2" style="padding: 12px; border-right: 1px solid #E2E8F0; color: #475569;">선수명</th>
                    <th rowspan="2" style="padding: 12px; border-right: 1px solid #E2E8F0; color: #475569;">🧤 GK</th>
                    <th rowspan="2" style="padding: 12px; border-right: 2px solid #E2E8F0; color: #475569; background-color: #F0FDF4;">🏃 필드 합계</th>
                    <th colspan="4" style="padding: 8px; border-bottom: 1px solid #E2E8F0; color: #1E293B; background-color: #F1F5F9; font-weight: bold;">상세 필드 포지션 현황</th>
                </tr>
                <tr style="background-color: #F8FAFC; border-bottom: 1px solid #E2E8F0;">
                    <th style="padding: 8px; border-right: 1px solid #EDF2F7; color: #64748B;">🔱 PIVO</th>
                    <th style="padding: 8px; border-right: 1px solid #EDF2F7; color: #64748B;">◀️ ALA_L</th>
                    <th style="padding: 8px; border-right: 1px solid #EDF2F7; color: #64748B;">▶️ ALA_R</th>
                    <th style="padding: 8px; color: #64748B;">🛡️ FIXO</th>
                </tr>
            </thead>
            <tbody style="background-color: white; color: #334155;">
                {tbody_content}
            </tbody>
        </table>
    </div>
    <style>
        /* 트랜지션 및 테이블 내부 TD 미세조정 CSS 인터셉트 */
        tbody tr {{ border-bottom: 1px solid #F1F5F9; transition: background 0.15s; }}
        tbody tr:hover {{ background-color: #F8FAFC; }}
        tbody td {{ padding: 10px 8px; }}
        tbody td:first-child {{ font-weight: bold; color: #0F172A; border-right: 1px solid #E2E8F0; }}
        tbody td:nth-child(2) {{ border-right: 1px solid #E2E8F0; }}
        tbody td:nth-child(3) {{ border-right: 2px solid #E2E8F0; font-weight: 600; background-color: #F9FEEB; }}
        tbody td:nth-child(4), tbody td:nth-child(5), tbody td:nth-child(6) {{ border-right: 1px solid #F1F5F9; }}
    </style>
    """
    st.html(custom_table_html)
