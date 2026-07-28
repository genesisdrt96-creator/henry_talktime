import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import os, glob

# --- 1. CẤU HÌNH TRANG & UI LUXURY ---
st.set_page_config(page_title="Dream Talent - Henry Master Hub", layout="wide")

# XỬ LÝ MÚI GIỜ MIỀN ĐÔNG HOA KỲ (EST/EDT)
tz_US_Eastern = pytz.timezone('US/Eastern')
now = datetime.now(tz_US_Eastern)
static_time = now.strftime("%m/%d/%Y | %H:%M")
file_date = now.strftime("%m-%d-%Y")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #050E3C 0%, #1e3a8a 100%);
        color: white; padding: 16px; border-radius: 12px;
        text-align: center; font-weight: 900; font-size: 24px; margin-bottom: 15px;
        letter-spacing: 0.3px;
    }
    .metric-container { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 15px; }
    .metric-box {
        background-color: white; padding: 6px 12px; border-radius: 10px; flex: 1; text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;
    }
    .metric-title { color: #000000; font-size: 13px; font-weight: 900; margin-bottom: -2px; text-transform: uppercase; }
    .metric-value { color: #000000; font-size: 28px; font-weight: 900; line-height: 1.2; }
    /* ===== KPI CARDS (tông NHẠT, căn giữa, chữ to) ===== */
    .kpi-row { display: flex; gap: 14px; margin: 4px 0 18px 0; flex-wrap: wrap; }
    .kpi-card {
        flex: 1; min-width: 168px; text-align: center;
        background: #FFFFFF;
        border-radius: 18px; padding: 18px 16px;
        box-shadow: 0 6px 18px rgba(30,58,138,0.07);
        border: 1px solid #E6ECF5;
    }
    .kpi-ico {
        width:48px; height:48px; border-radius:14px; display:flex;
        align-items:center; justify-content:center; font-size:23px; margin:0 auto 10px auto;
    }
    .kpi-label { font-size:14px; font-weight:800; letter-spacing:.5px; text-transform:uppercase; color:#64748B; }
    .kpi-value { font-size:36px; font-weight:900; line-height:1.15; margin-top:4px; color:#12326B; }
    .kpi-sub   { font-size:14px; font-weight:700; color:#3B82F6; margin-top:2px; }
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        border: none !important; color: #0f172a !important;
        font-weight: 900 !important; font-size: 16px !important; padding: 11px !important;
    }
    /* Tiêu đề điều hướng trong sidebar */
    .nav-title {
        color: #050E3C; font-size: 16px; font-weight: 900; text-transform: uppercase;
        letter-spacing: 0.5px; margin: 4px 0 8px 0; text-align: center;
    }
    /* Nút điều hướng trang: to, bo góc, dễ bấm */
    section[data-testid="stSidebar"] .stButton > button {
        font-size: 17px !important; font-weight: 900 !important;
        padding: 15px 10px !important; border-radius: 12px !important;
        border: 2px solid #050E3C !important; margin-bottom: 6px !important;
        transition: all 0.15s ease;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(5,14,60,0.25) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE (ĐÃ CẬP NHẬT THEO YÊU CẦU CỦA HENRY) ---
STAFF_CONFIG = {
   "Andres Nguyen": "GOLD", 
    "Charlie Nguyen": "GOLD", 
    "Alan Nguyen": "GOLD", 
    "Rio Le": "GOLD", 
    "Ryan Le": "GOLD",
    "Amy Tran": "SILVER",
    "William Nguyen": "SILVER",
    "Thierry Phung": "BRONZE",
    "David Vo": "BRONZE", 
    "Kathy Bui": "BRONZE",
    "Ivan Huynh": "Associated", 
    "Jayce Mai": "Associated", 
    "Jolie Nguyen": "Associated", 
    "Louisa Ngo": "Associated",
    "Tony Pham": "Associated",
    "Katny Duong": "Associated",
    "Liam Hoang": "Probation",
    "Claire Dinh": "Probation", 
    "Mia Bui": "Probation",
    "Niko Nguyen": "Probation",
    "Martin Tran": "Probation",
    "Ray Duong": "Probation",
    "Marky Huynh": "Probation"
}
STAFF_LIST = list(STAFF_CONFIG.keys())
LEVEL_TARGETS = {"GOLD": 9000, "SILVER": 9000, "BRONZE": 9000, "Associated": 9000, "Probation": 9000}  # 9000s = 2h30 cho tất cả
LEVEL_COLORS = {"GOLD": "#FDE9B8", "SILVER": "#E4EAF1", "BRONZE": "#F1DAC4", "Associated": "#DAE6FB", "Probation": "#D2F0E1"}
LEVEL_TEXT   = {"GOLD": "#8A6D0B", "SILVER": "#475569", "BRONZE": "#9A5A24", "Associated": "#1E40AF", "Probation": "#0F766E"}

# Cuộc gọi ngắn hơn ngưỡng này coi là blip nối máy, không tính talktime
REAL_TALK_MIN_SEC = 20

def to_seconds(s):
    if pd.isna(s) or str(s).lower() == 'in progress' or s == '-': return 0
    try:
        parts = str(s).strip().split(':')
        if len(parts) == 3: return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2: return int(parts[0]) * 60 + int(parts[1])
        return 0
    except: return 0

def format_time(seconds):
    if seconds <= 0: return "00:00:00"
    h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# --- 3. SESSION STATE ---
if 'input_df' not in st.session_state:
    st.session_state.input_df = pd.DataFrame({
        "Sales Name": STAFF_LIST, "Chốt $": 0.0, "Xin OFF": False, "Giảm số P": 0.0
    }).set_index("Sales Name")

def update_input():
    # Ghi theo TÊN (không theo vị trí) để tránh lệch dòng khi file RingCentral
    # không đủ 24 người. row_idx là vị trí trong bảng đang hiển thị (active_staff),
    # nên phải map ngược ra tên trước khi ghi.
    if "editor_v82" in st.session_state:
        active = st.session_state.get('active_staff', [])
        for row_idx, changes in st.session_state["editor_v82"]["edited_rows"].items():
            if row_idx >= len(active):
                continue
            name = active[row_idx]
            for k, v in changes.items():
                st.session_state.input_df.loc[name, k] = v

# --- 4. SIDEBAR ---
st.sidebar.markdown("# 💎 Master Dashboard")
uploaded_file = st.sidebar.file_uploader("📂 Tải file RingCentral", type=["csv"])

# Thư mục lưu dữ liệu Final theo ngày (nằm cạnh file .py)
HISTORY_DIR = "history"
os.makedirs(HISTORY_DIR, exist_ok=True)

# --- ĐIỀU HƯỚNG TRANG (luôn hiện, nút to dễ bấm) ---
if 'page' not in st.session_state:
    st.session_state.page = "📊 Báo cáo & Biểu đồ"
st.sidebar.markdown("---")
st.sidebar.markdown('<div class="nav-title">📄 Chọn trang</div>', unsafe_allow_html=True)
_nav = [("📝 Nhập doanh số & Điều chỉnh", "📝  NHẬP DOANH SỐ"),
        ("📊 Báo cáo & Biểu đồ", "📊  BÁO CÁO & BIỂU ĐỒ"),
        ("📅 Lịch sử", "📅  LỊCH SỬ (NGÀY CŨ)")]
for _val, _label in _nav:
    if st.sidebar.button(_label, use_container_width=True,
                         type=("primary" if st.session_state.page == _val else "secondary")):
        st.session_state.page = _val; st.rerun()
page = st.session_state.page

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file)
    df_raw.columns = df_raw.columns.str.strip()

    # --- BƯỚC LỌC 1: CHỈ GIỮ OUTGOING — XÓA THẲNG MỌI DÒNG INCOMING ---
    n_incoming = 0
    if 'Direction' in df_raw.columns:
        _dir = df_raw['Direction'].astype(str).str.strip().str.lower()
        n_incoming = int((_dir == 'incoming').sum())
        df_raw = df_raw[_dir == 'outgoing']          # bỏ Incoming + mọi dòng không phải Outgoing
        if n_incoming:
            st.sidebar.caption(f"🚫 Đã loại {n_incoming} dòng Incoming khỏi talktime.")
    else:
        st.warning("⚠️ Không tìm thấy cột 'Direction'. Vui lòng kiểm tra lại định dạng file.")

    # --- BƯỚC LỌC 2: BỎ CALL TRANSFER (lọc theo Action, KHÔNG theo Type) ---
    # Sửa quan trọng: RingCentral đôi khi ghi cuộc VoIP Call thật nhưng để TRỐNG cột Type.
    # Nếu lọc 'Type == Voice' sẽ vô tình bỏ mất các cuộc thật này (kể cả cuộc kết nối 5-7 phút).
    # Chỉ cần loại đúng dòng Transfer (nguồn nhân bản duration) là đủ.
    if 'Action' in df_raw.columns:
        df_raw = df_raw[df_raw['Action'].astype(str).str.strip().str.lower() != 'transfer']
    elif 'Type' in df_raw.columns:   # dự phòng nếu file không có cột Action
        df_raw = df_raw[df_raw['Type'].astype(str).str.strip().str.lower() == 'voice']
    else:
        st.warning("⚠️ Không tìm thấy cột 'Action' lẫn 'Type'. Không thể lọc Transfer.")

    df_raw['Ext_Name'] = df_raw['Extension'].str.split(' - ', n=1).str[1].fillna("Unknown")
    df_raw['Sec'] = df_raw['Duration'].apply(to_seconds)
    # LƯU Ý: GIỮ cả leg ngắn (< 20s) theo yêu cầu — không lọc blip, không merge overlap.

    # BÁO CÁO TẤT CẢ nhân viên theo đúng thứ tự STAFF_LIST (không lọc bỏ ai).
    # Người không xuất hiện trong file RingCentral -> nhóm "không có data" (ghi chú).
    active_in_file = df_raw['Ext_Name'].unique()
    active_staff = list(STAFF_LIST)                       # thứ tự report cố định
    no_data_staff = [n for n in active_staff if n not in active_in_file]
    NO_DATA_SET = set(no_data_staff)

    df_active = df_raw[df_raw['Ext_Name'].isin(active_staff)]
    if len(df_active):
        # TALKTIME = TỔNG duration các leg Voice còn lại (cộng thẳng, không union).
        stats = df_active.groupby('Ext_Name').agg(
            Actual_Sec=('Sec', 'sum'),
            Tong_Cuoc_Goi=('Sec', 'count'),
            Int_5p=('Sec', lambda x: int((x >= 300).sum())),
            Int_10p=('Sec', lambda x: int((x >= 600).sum())),
            Int_30p=('Sec', lambda x: int((x >= 1800).sum())),
        ).reindex(active_staff).fillna(0)
    else:
        stats = pd.DataFrame(
            0, index=active_staff,
            columns=['Actual_Sec', 'Tong_Cuoc_Goi', 'Int_5p', 'Int_10p', 'Int_30p']
        )

    st.session_state['active_staff'] = active_staff
    current_input_display = st.session_state.input_df.loc[active_staff]

    # --- TÍNH TOÁN (chạy chung cho cả 2 trang) ---
    final_df = pd.concat([current_input_display, stats], axis=1).fillna(0).reset_index()
    final_df.rename(columns={'index': 'Sales Name'}, inplace=True)

    def calculate_metrics(row):
        name = row['Sales Name']; lvl = STAFF_CONFIG.get(name, "Probation"); target_orig = LEVEL_TARGETS.get(lvl, 9000); actual = row['Actual_Sec']
        if row['Xin OFF']: return pd.Series([lvl, target_orig, actual, 0, 0.0, "OFF"])
        sales = row['Chốt $']
        # Không có mặt trong file RingCentral và cũng chưa chốt $ -> đánh dấu NO DATA (đưa vào ghi chú)
        if name in NO_DATA_SET and sales == 0:
            return pd.Series([lvl, target_orig, 0, 0, 0.0, "NO DATA"])
        bonus = 1800 if 300 <= sales < 500 else (2700 if 500 <= sales < 1000 else (5400 if 1000 <= sales < 2000 else 0))
        is_done = sales >= 2000; total_red = (target_orig if is_done else (bonus + row['Giảm số P'] * 60))
        target_final = max(0, target_orig - total_red); pct = 100.0 if (is_done or target_final <= 0) else (actual / target_final * 100)
        return pd.Series([lvl, target_final, actual, total_red, round(float(pct), 1), "GOOD JOB" if pct >= 100.0 or is_done else "Come on!"])

    final_df[['🏅 LVL', 'target_val', 'actual_val', 'red_val', 'pct_val', '📊 RESULT']] = final_df.apply(calculate_metrics, axis=1)
    # Talktime QUY ĐỔI = talktime thật + phần giờ được cộng bù (hoặc trừ). Done (red>=9000) -> giữ talktime thật.
    final_df['effective_sec'] = final_df.apply(
        lambda r: r['actual_val'] if r['red_val'] >= 9000 else r['actual_val'] + r['red_val'], axis=1)
    # GIỮ THỨ TỰ CỐ ĐỊNH theo STAFF_LIST (không sort theo hiệu suất)
    final_df = final_df.reset_index(drop=True)

# ==================== TRANG 1: NHẬP LIỆU ====================
if uploaded_file and page == "📝 Nhập doanh số & Điều chỉnh":
    st.subheader("📝 BẢNG NHẬP DOANH SỐ & ĐIỀU CHỈNH")
    st.caption("Nhập xong, chuyển sang trang **📊 Báo cáo & Biểu đồ** ở thanh bên để xem kết quả.")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.data_editor(current_input_display, use_container_width=True, key="editor_v82",
                       on_change=update_input, height=((len(active_staff)*35)+40))

# ==================== TRANG 2: BÁO CÁO ====================
if uploaded_file and page == "📊 Báo cáo & Biểu đồ":
    # (Tiêu đề + KPI được hiển thị trong khối bảng HTML bên dưới — không lặp lại ở đây)
    t_p = int(final_df['Chốt $'].sum())
    t_t = format_time(final_df['Actual_Sec'].sum())
    t_c = int(final_df['Tong_Cuoc_Goi'].sum())
    _valid = final_df[~final_df['📊 RESULT'].isin(["OFF", "NO DATA"])]
    team_pct = round(_valid['actual_val'].sum() / _valid['target_val'].sum() * 100, 1) if _valid['target_val'].sum() > 0 else 0.0
    n_done = int((final_df['📊 RESULT'] == "GOOD JOB").sum())
    n_active = int(len(_valid))

    # --- 8. BẢNG HIỂN THỊ ---
    disp_df = pd.DataFrame()
    disp_df['👤 SALES'] = final_df['Sales Name']; disp_df['🏅 LVL'] = final_df['🏅 LVL']
    disp_df['💵 CHỐT $'] = final_df['Chốt $']

    def _fmt_goal(r):
        return "—" if r['📊 RESULT'] == "NO DATA" else format_time(r['target_val'])
    def _fmt_call(r):
        return "—" if r['📊 RESULT'] == "NO DATA" else format_time(r['actual_val'])
    def _fmt_eff(r):
        return "—" if r['📊 RESULT'] == "NO DATA" else format_time(r['effective_sec'])
    disp_df['🎯 GOAL'] = final_df.apply(_fmt_goal, axis=1)
    disp_df['⏱️ CALL'] = final_df.apply(_fmt_call, axis=1)
    disp_df['🧮 QUY ĐỔI'] = final_df.apply(_fmt_eff, axis=1)          # talktime sau cộng/trừ giờ
    disp_df['📉 GIẢM TALKTIME'] = final_df.apply(
        lambda r: "—" if r['📊 RESULT'] == "NO DATA" else ("🏆 DONE" if r['red_val'] >= 9000 else f"{int(r['red_val']//60)}p"), axis=1)
    disp_df['% HOÀN THÀNH'] = final_df['pct_val']
    disp_df['🔥 5P'] = final_df['Int_5p'].astype(int); disp_df['🔥 10P'] = final_df['Int_10p'].astype(int)
    disp_df['🔥 30P'] = final_df['Int_30p'].astype(int); disp_df['📊 RESULT'] = final_df['📊 RESULT']

    # --- HÀNG TỔNG ---
    valid = final_df[~final_df['📊 RESULT'].isin(["OFF", "NO DATA"])]
    tot_target = valid['target_val'].sum()
    tot_actual = valid['actual_val'].sum()
    tot_pct = round(tot_actual / tot_target * 100, 1) if tot_target > 0 else 0.0
    total_row = {
        '👤 SALES': '🔷 TOTAL', '🏅 LVL': '',
        '💵 CHỐT $': float(final_df['Chốt $'].sum()),
        '🎯 GOAL': format_time(tot_target),
        '⏱️ CALL': format_time(final_df['actual_val'].sum()),
        '🧮 QUY ĐỔI': format_time(valid['effective_sec'].sum()),
        '📉 GIẢM TALKTIME': '',
        '% HOÀN THÀNH': tot_pct,
        '🔥 5P': int(final_df['Int_5p'].sum()),
        '🔥 10P': int(final_df['Int_10p'].sum()),
        '🔥 30P': int(final_df['Int_30p'].sum()),
        '📊 RESULT': '',
    }
    disp_df = pd.concat([disp_df, pd.DataFrame([total_row])], ignore_index=True)
    # (Bảng chính giờ là bảng HTML toàn cảnh bên dưới; disp_df vẫn dùng để export CSV.)

    # --- GHI CHÚ: nhân viên không có dữ liệu talktime ---
    if no_data_staff:
        st.warning(f"📝 **Không có dữ liệu talktime ({len(no_data_staff)}):** " + " • ".join(no_data_staff))

    # ================= CHẾ ĐỘ TOÀN MÀN HÌNH (tiêu đề + KPI + bảng cùng lúc) =================
    def _bar(pct, label, fill="#8FB0D6"):
        p = max(0, min(pct, 100))
        return (f'<div class="pbar"><div class="pfill" style="width:{p:.0f}%;background:{fill};"></div>'
                f'<span>{label}</span></div>')

    rows_html = ""
    for _, r in final_df.iterrows():
        res = r['📊 RESULT']; lvl = r['🏅 LVL']
        if res == "NO DATA":
            rows_html += (f'<tr class="nod"><td>{r["Sales Name"]}</td><td>{lvl}</td>'
                          f'<td>—</td><td>—</td><td>—</td><td>—</td><td>—</td>'
                          f'<td>{int(r["Int_5p"])}</td><td>{int(r["Int_10p"])}</td><td>{int(r["Int_30p"])}</td>'
                          f'<td class="badge nodb">NO DATA</td></tr>')
            continue
        lvl_bg = LEVEL_COLORS.get(lvl, "#FFFFFF"); lvl_tx = LEVEL_TEXT.get(lvl, "#12326B")
        chot = f"${int(r['Chốt $']):,}" if r['Chốt $'] > 0 else "$0"
        chot_style = 'style="background:#FEF3C7;color:#92400E;"' if r['Chốt $'] > 0 else ''
        eff_bar = _bar(r['effective_sec'] / 9000 * 100, format_time(r['effective_sec']))
        pct_bar = _bar(r['pct_val'], f"{r['pct_val']:.0f}%")
        if res == "GOOD JOB": badge = '<td class="badge okb">GOOD JOB</td>'
        elif res == "OFF":    badge = '<td class="badge offb">OFF</td>'
        else:                 badge = '<td class="badge cmb">Come on!</td>'
        rows_html += (f'<tr><td>{r["Sales Name"]}</td>'
                      f'<td style="background:{lvl_bg};color:{lvl_tx};">{lvl}</td>'
                      f'<td {chot_style}>{chot}</td>'
                      f'<td>{format_time(r["target_val"])}</td>'
                      f'<td>{format_time(r["actual_val"])}</td>'
                      f'<td>{eff_bar}</td><td>{pct_bar}</td>'
                      f'<td>{int(r["Int_5p"])}</td><td>{int(r["Int_10p"])}</td><td>{int(r["Int_30p"])}</td>'
                      f'{badge}</tr>')
    # hàng tổng
    rows_html += (f'<tr class="tot"><td>TOTAL</td><td></td>'
                  f'<td>${int(final_df["Chốt $"].sum()):,}</td>'
                  f'<td>{format_time(tot_target)}</td>'
                  f'<td>{format_time(final_df["actual_val"].sum())}</td>'
                  f'<td>{format_time(valid["effective_sec"].sum())}</td>'
                  f'<td>{tot_pct:.0f}%</td>'
                  f'<td>{int(final_df["Int_5p"].sum())}</td><td>{int(final_df["Int_10p"].sum())}</td>'
                  f'<td>{int(final_df["Int_30p"].sum())}</td><td></td></tr>')

    kpi_html = f"""
      <div class="kpis">
        <div class="kpi"><div class="ic" style="background:#FEF0D6;">💰</div><div class="lb">Total Premium</div><div class="vl">${t_p:,}</div></div>
        <div class="kpi"><div class="ic" style="background:#D9F0FB;">⏱️</div><div class="lb">Total Talktime</div><div class="vl">{t_t}</div></div>
        <div class="kpi"><div class="ic" style="background:#E4E7FB;">📞</div><div class="lb">Outgoing Calls</div><div class="vl">{t_c:,}</div></div>
        <div class="kpi"><div class="ic" style="background:#D6F5E5;">✅</div><div class="lb">Team hoàn thành</div><div class="vl">{team_pct:.0f}%</div></div>
        <div class="kpi"><div class="ic" style="background:#FCEFCF;">🏆</div><div class="lb">Đạt mục tiêu</div><div class="vl">{n_done}<span style="font-size:20px;color:#94A3B8;">/{n_active}</span></div></div>
      </div>"""

    n_rows = len(final_df) + 1
    box_h = 250 + n_rows * 52 + 80
    full_html = f"""
    <div id="reportBox" class="wrap">
      <button class="fsbtn" onclick="goFS()">⛶ Toàn màn hình</button>
      <div class="title">🏆 WORKING RESULTS STATISTICS | {static_time} (EST)</div>
      {kpi_html}
      <table>
        <thead><tr>
          <th>SALES</th><th>LVL</th><th>CHỐT $</th><th>GOAL</th><th>CALL</th>
          <th>QUY ĐỔI</th><th>% HOÀN THÀNH</th><th>5P</th><th>10P</th><th>30P</th><th>RESULT</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    <style>
      * {{ box-sizing:border-box; font-family:'Segoe UI',Roboto,Arial,sans-serif; }}
      body {{ margin:0; }}
      .wrap {{ padding:16px; background:#F6F9FF; position:relative; }}
      #reportBox:fullscreen {{ overflow:auto; }}
      .fsbtn {{ position:absolute; right:18px; top:18px; z-index:9; background:#fff; color:#33507A;
                border:1px solid #CBD8EC; border-radius:10px; padding:9px 15px; font-weight:800;
                font-size:14px; cursor:pointer; box-shadow:0 2px 6px rgba(30,58,138,.12); }}
      .fsbtn:hover {{ background:#EEF4FF; }}
      .title {{ background:linear-gradient(135deg,#6E8FBE,#8AA7CE); color:#fff; text-align:center;
                font-weight:900; font-size:25px; padding:18px; border-radius:14px; letter-spacing:.3px; }}
      .kpis {{ display:flex; gap:14px; margin:16px 0; flex-wrap:wrap; }}
      .kpi {{ flex:1; min-width:168px; text-align:center; background:#fff; border:1px solid #E6ECF5;
              border-radius:16px; padding:16px; box-shadow:0 6px 16px rgba(30,58,138,.07); }}
      .kpi .ic {{ width:48px;height:48px;border-radius:14px;margin:0 auto 8px;display:flex;
                  align-items:center;justify-content:center;font-size:23px; }}
      .kpi .lb {{ font-size:14px;font-weight:800;text-transform:uppercase;letter-spacing:.5px;color:#6B7A90; }}
      .kpi .vl {{ font-size:34px;font-weight:900;color:#12326B; }}
      table {{ width:100%; border-collapse:separate; border-spacing:0 6px; }}
      th {{ font-size:15px; font-weight:900; color:#3A4A63; text-align:center; padding:7px 5px;
            text-transform:uppercase; letter-spacing:.2px; }}
      td {{ font-size:15px; font-weight:800; text-align:center; padding:8px 5px; background:#fff; color:#1F2A44; }}
      tr td:first-child {{ border-radius:12px 0 0 12px; }}
      tr td:last-child  {{ border-radius:0 12px 12px 0; }}
      tr.nod td {{ background:#F3F6FB; color:#9AA6B8; font-weight:700; }}
      tr.tot td {{ background:#33507A; color:#fff; font-weight:900; font-size:16px; }}
      .pbar {{ position:relative; height:22px; background:#EEF2F8; border-radius:7px; overflow:hidden; }}
      .pfill {{ position:absolute; left:0; top:0; bottom:0; }}
      .pbar span {{ position:relative; z-index:2; line-height:22px; font-weight:900; color:#22314A; font-size:13px; }}
      .badge {{ border-radius:10px; font-weight:900; }}
      .okb {{ background:#DCFCE7; color:#166534; }}
      .cmb {{ background:#FEE2E2; color:#B91C1C; }}
      .offb {{ background:#E2E8F0; color:#475569; }}
      .nodb {{ background:#EEF2F8; color:#94A3B8; }}
    </style>
    <script>
      function goFS() {{
        var el = document.getElementById('reportBox');
        var rq = el.requestFullscreen || el.webkitRequestFullscreen || el.msRequestFullscreen;
        if (rq) {{ rq.call(el).catch(function(){{ alert('Trình duyệt chặn toàn màn hình trong khung này. Hãy nhấn F11 để phóng to cả trang.'); }}); }}
        else {{ alert('Trình duyệt không hỗ trợ. Hãy nhấn F11.'); }}
      }}
    </script>
    """

    st.markdown("#### 📋 Bảng kết quả")
    components.html(full_html, height=box_h, scrolling=True)

    # --- COPY CỘT % ĐỂ DÁN SANG GOOGLE SHEET ---
    with st.expander("📋 Copy cột '% HOÀN THÀNH' để dán sang Google Sheet"):
        st.caption("Bấm biểu tượng copy ở góc phải ô bên dưới → sang Google Sheet, chọn 1 ô rồi Ctrl+V. "
                   "Các dòng sẽ tự đổ xuống thành 1 cột, đúng thứ tự như bảng (kèm dòng TOTAL cuối).")
        pct_with_sign = "\n".join(f"{v:.0f}%" for v in final_df['pct_val']) + f"\n{tot_pct:.0f}%"
        pct_plain = "\n".join(f"{v:.0f}" for v in final_df['pct_val']) + f"\n{tot_pct:.0f}"
        cA, cB = st.columns(2)
        with cA:
            st.markdown("**Có dấu %** (vd 53%)")
            st.code(pct_with_sign, language=None)
        with cB:
            st.markdown("**Số thường** (vd 53, dễ tính toán)")
            st.code(pct_plain, language=None)

    # --- 9. BIỂU ĐỒ (phân nhóm trạng thái + đường mục tiêu 100%) ---
    chart_df = final_df[~final_df['📊 RESULT'].isin(["OFF", "NO DATA"])].copy()
    if len(chart_df):
        def _status(r):
            if r['pct_val'] >= 100 or r['📊 RESULT'] == "GOOD JOB": return "✅ Đạt (≥100%)"
            if r['pct_val'] >= 70: return "🟡 Gần đạt (70–99%)"
            return "🔴 Còn xa (<70%)"
        chart_df['Trạng thái'] = chart_df.apply(_status, axis=1)
        color_map = {"✅ Đạt (≥100%)": "#16a34a", "🟡 Gần đạt (70–99%)": "#f59e0b", "🔴 Còn xa (<70%)": "#dc2626"}
        order = ["✅ Đạt (≥100%)", "🟡 Gần đạt (70–99%)", "🔴 Còn xa (<70%)"]
        chart_df = chart_df.sort_values('pct_val', ascending=False)

        fig = px.bar(chart_df, x='Sales Name', y='pct_val', color='Trạng thái',
                     color_discrete_map=color_map, category_orders={'Trạng thái': order},
                     text='pct_val', height=400,
                     hover_data={'Chốt $': ':$,.0f', 'pct_val': ':.1f'})
        fig.update_traces(texttemplate='%{text:.0f}%', textposition='outside', cliponaxis=False)
        fig.add_hline(y=100, line_dash="dash", line_color="#050E3C",
                      annotation_text="Mục tiêu 100%", annotation_position="top left")
        fig.update_layout(
            xaxis={'categoryorder': 'total descending', 'title': None},
            yaxis_title="% Hoàn thành", legend_title=None, plot_bgcolor='white',
            margin=dict(t=40, b=0, l=0, r=0), uniformtext_minsize=8, uniformtext_mode='hide',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

    # --- 9b. BIỂU ĐỒ ĐƯỜNG: CUỘC GỌI CHẤT LƯỢNG (≥5 PHÚT) ---
    line_df = final_df[~final_df['📊 RESULT'].isin(["OFF", "NO DATA"])].copy()
    if len(line_df):
        tot_5p = int(final_df['Int_5p'].sum())
        st.markdown(f'<div class="main-header">📈 CUỘC GỌI CHẤT LƯỢNG ≥5 PHÚT | TỔNG: {tot_5p} CUỘC</div>', unsafe_allow_html=True)
        figl = px.line(line_df, x='Sales Name', y='Int_5p', markers=True, text='Int_5p', height=340)
        figl.update_traces(line=dict(color='#050E3C', width=3),
                           marker=dict(size=10, color='#1e3a8a', line=dict(color='white', width=1.5)),
                           textposition='top center', textfont=dict(size=14, color='#050E3C', family='Arial Black'))
        figl.update_layout(
            xaxis={'title': None, 'tickangle': -40},
            yaxis_title="Số cuộc ≥5 phút", plot_bgcolor='white',
            margin=dict(t=20, b=0, l=0, r=0),
            font=dict(size=13, color='#050E3C'))
        figl.update_yaxes(rangemode='tozero', gridcolor='#e2e8f0')
        st.plotly_chart(figl, use_container_width=True)

    # --- 10. SNAPSHOT (dạng số + có cột Date) ---
    snapshot = final_df[['Sales Name', '🏅 LVL', 'Xin OFF', 'Chốt $',
                         'target_val', 'actual_val', 'effective_sec', 'red_val', 'pct_val',
                         'Tong_Cuoc_Goi', 'Int_5p', 'Int_10p', 'Int_30p', '📊 RESULT']].copy()
    snapshot.insert(0, 'Date', file_date)

    # --- 11. LƯU / EXPORT ---
    st.markdown("---")
    cc1, cc2, cc3 = st.columns([1.4, 1, 1])
    with cc1:
        # LƯU DỮ LIỆU FINAL CỦA NGÀY -> đọc lại được ở trang Lịch sử
        if st.button(f"💾 Lưu Final ngày {file_date}", use_container_width=True, type="primary"):
            path = os.path.join(HISTORY_DIR, f"Final_{file_date}.csv")
            snapshot.to_csv(path, index=False, encoding='utf-8-sig')
            st.success(f"✅ Đã lưu: {path}")
    with cc2:
        st.download_button("📥 Tải bảng (CSV)", disp_df.to_csv(index=False).encode('utf-8-sig'),
                           f"Report_{file_date}.csv", use_container_width=True)
    with cc3:
        st.download_button("📦 Tải snapshot", snapshot.to_csv(index=False).encode('utf-8-sig'),
                           f"Snapshot_{file_date}.csv", use_container_width=True)
    saved_path = os.path.join(HISTORY_DIR, f"Final_{file_date}.csv")
    if os.path.exists(saved_path):
        st.caption(f"📁 Ngày {file_date} đã có bản lưu. Bấm 'Lưu' lần nữa sẽ ghi đè.")

# ==================== TRANG 3: LỊCH SỬ ====================
if page == "📅 Lịch sử":
    st.markdown('<div class="main-header">📅 XEM LẠI DỮ LIỆU FINAL CÁC NGÀY</div>', unsafe_allow_html=True)
    files = sorted(glob.glob(os.path.join(HISTORY_DIR, "Final_*.csv")), reverse=True)
    if not files:
        st.info("Chưa có ngày nào được lưu. Vào trang 📊 Báo cáo → bấm '💾 Lưu Final' để lưu lại.")
    else:
        dates = [os.path.basename(f).replace("Final_", "").replace(".csv", "") for f in files]
        sel = st.selectbox("Chọn ngày cần xem lại", dates)
        sdf = pd.read_csv(os.path.join(HISTORY_DIR, f"Final_{sel}.csv"))

        # KPI của ngày đã lưu
        v = sdf[~sdf['📊 RESULT'].isin(["OFF", "NO DATA"])]
        tp = int(sdf['Chốt $'].sum()); tt = format_time(sdf['actual_val'].sum())
        tc = int(sdf['Tong_Cuoc_Goi'].sum())
        tpct = round(v['actual_val'].sum() / v['target_val'].sum() * 100, 1) if v['target_val'].sum() > 0 else 0.0
        nd = int((sdf['📊 RESULT'] == "GOOD JOB").sum())
        st.markdown(f"""<div class="kpi-row">
            <div class="kpi-card"><div class="kpi-ico" style="background:#F59E0B33;">💰</div>
                <div class="kpi-label">Total Premium</div><div class="kpi-value">${tp:,}</div></div>
            <div class="kpi-card"><div class="kpi-ico" style="background:#38BDF833;">⏱️</div>
                <div class="kpi-label">Total Talktime</div><div class="kpi-value">{tt}</div></div>
            <div class="kpi-card"><div class="kpi-ico" style="background:#818CF833;">📞</div>
                <div class="kpi-label">Outgoing Calls</div><div class="kpi-value">{tc:,}</div></div>
            <div class="kpi-card"><div class="kpi-ico" style="background:#34D39933;">✅</div>
                <div class="kpi-label">Team hoàn thành</div><div class="kpi-value">{tpct:.1f}%</div></div>
            <div class="kpi-card"><div class="kpi-ico" style="background:#FBBF2433;">🏆</div>
                <div class="kpi-label">Đạt mục tiêu</div><div class="kpi-value">{nd}</div></div>
        </div>""", unsafe_allow_html=True)

        # Bảng ngày đã lưu (định dạng lại thời gian)
        show = pd.DataFrame()
        show['👤 SALES'] = sdf['Sales Name']; show['🏅 LVL'] = sdf['🏅 LVL']
        show['💵 CHỐT $'] = sdf['Chốt $']
        show['🎯 GOAL'] = sdf['target_val'].apply(format_time)
        show['⏱️ CALL'] = sdf['actual_val'].apply(format_time)
        if 'effective_sec' in sdf.columns:
            show['🧮 QUY ĐỔI'] = sdf['effective_sec'].apply(format_time)
        show['% HOÀN THÀNH'] = sdf['pct_val']
        show['🔥 5P'] = sdf['Int_5p']; show['🔥 10P'] = sdf['Int_10p']; show['🔥 30P'] = sdf['Int_30p']
        show['📊 RESULT'] = sdf['📊 RESULT']
        st.dataframe(show, use_container_width=True, hide_index=True, height=(len(sdf)*38 + 50),
            column_config={"💵 CHỐT $": st.column_config.NumberColumn(format="$%d"),
                           "% HOÀN THÀNH": st.column_config.NumberColumn(format="%.0f%%")})
        st.download_button("📥 Tải lại file ngày này", sdf.to_csv(index=False).encode('utf-8-sig'),
                           f"Final_{sel}.csv")

# ==================== CHƯA CÓ FILE ====================
if page != "📅 Lịch sử" and not uploaded_file:
    st.info("👋 Chào Team Henry! Tải file RingCentral ở thanh bên để bắt đầu, hoặc vào trang 📅 Lịch sử để xem ngày cũ.")
