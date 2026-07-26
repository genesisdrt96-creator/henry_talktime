import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz

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
        color: white; padding: 15px; border-radius: 12px;
        text-align: center; font-weight: 800; font-size: 22px; margin-bottom: 15px;
    }
    .metric-container { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 15px; }
    .metric-box {
        background-color: white; padding: 5px 10px; border-radius: 10px; flex: 1; text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;
    }
    .metric-title { color: #000000; font-size: 11px; font-weight: 700; margin-bottom: -2px; text-transform: uppercase; }
    .metric-value { color: #000000; font-size: 24px; font-weight: 900; line-height: 1.2; }
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        border: none !important; color: #000000 !important;
        font-weight: 800 !important; font-size: 14px !important; padding: 10px !important;
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
LEVEL_COLORS = {"GOLD": "#FEF3C7", "SILVER": "#F1F5F9", "BRONZE": "#FFEDD5", "Associated": "#DBEAFE", "Probation": "#DCFCE7"}

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
uploaded_file = st.sidebar.file_uploader("📂 1. Tải file RingCentral", type=["csv"])
csv_input_file = st.sidebar.file_uploader("📂 2. Tải file Sales (CSV)", type=["csv"])

if csv_input_file:
    try:
        df_csv = pd.read_csv(csv_input_file)
        df_csv.columns = df_csv.columns.str.strip()
        df_csv = df_csv.set_index("Sales Name")
        st.session_state.input_df.update(df_csv)
        st.sidebar.success("✅ Đã nạp dữ liệu từ CSV!")
    except Exception as e:
        st.sidebar.error(f"Lỗi file CSV: {e}")

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file)
    df_raw.columns = df_raw.columns.str.strip()

    # --- BƯỚC LỌC 1: CHỈ GIỮ OUTGOING ---
    if 'Direction' in df_raw.columns:
        df_raw = df_raw[df_raw['Direction'].astype(str).str.strip() == 'Outgoing']
    else:
        st.warning("⚠️ Không tìm thấy cột 'Direction'. Vui lòng kiểm tra lại định dạng file.")

    # --- BƯỚC LỌC 2: CHỈ GIỮ LEG THẬT (Type == 'Voice') ---
    # Row Transfer để trống cột Type -> tự động bị loại. Đây là bước chống thổi
    # phồng talktime do các leg Transfer nhân bản nguyên duration.
    if 'Type' in df_raw.columns:
        df_raw['Type'] = df_raw['Type'].astype(str).str.strip()
        df_raw = df_raw[df_raw['Type'].str.lower() == 'voice']
    else:
        st.warning("⚠️ Không tìm thấy cột 'Type'. Không thể lọc Transfer — số liệu có thể bị thổi phồng.")

    df_raw['Ext_Name'] = df_raw['Extension'].str.split(' - ', n=1).str[1].fillna("Unknown")
    df_raw['Sec'] = df_raw['Duration'].apply(to_seconds)

    # --- BƯỚC LỌC 3: BỎ BLIP NỐI MÁY QUÁ NGẮN ---
    df_raw = df_raw[df_raw['Sec'] >= REAL_TALK_MIN_SEC]

    # --- DỰNG MỐC THỜI GIAN (Time chỉ có độ phân giải PHÚT) ---
    df_raw['Start'] = pd.to_datetime(
        df_raw['Date'].astype(str).str.strip() + ' ' + df_raw['Time'].astype(str).str.strip(),
        format='%a %m/%d/%Y %I:%M %p', errors='coerce'
    )
    df_raw = df_raw.dropna(subset=['Start'])
    df_raw['End'] = df_raw['Start'] + pd.to_timedelta(df_raw['Sec'], unit='s')

    # --- MERGE INTERVAL: talktime = UNION các khoảng (wall-clock), số cuộc = số phiên ---
    # Các leg VoIP chồng lấn thời gian của cùng một cuộc bị transfer lòng vòng
    # sẽ được gộp thành 1 phiên; talktime tính theo thời gian đường dây thực bận
    # dưới ext của agent, không cộng dồn từng leg.
    def _merge_sessions(g):
        g = g.sort_values('Start')
        talk, cnt, cs, ce = 0, 0, None, None
        sess_max = []
        for s, e, sec in zip(g['Start'], g['End'], g['Sec']):
            if ce is None or s > ce:            # phiên mới (không chồng)
                if ce is not None:
                    talk += (ce - cs).total_seconds()
                cs, ce, cnt = s, e, cnt + 1
                sess_max.append(sec)
            else:                                # chồng lấn -> nới phiên hiện tại
                ce = max(ce, e)
                sess_max[-1] = max(sess_max[-1], sec)
        if ce is not None:
            talk += (ce - cs).total_seconds()
        ss = pd.Series(sess_max, dtype=float)
        return pd.Series({
            'Actual_Sec': talk,
            'Tong_Cuoc_Goi': cnt,
            'Int_5p':  int((ss >= 300).sum()),
            'Int_10p': int((ss >= 600).sum()),
            'Int_30p': int((ss >= 1800).sum()),
        })

    # BÁO CÁO TẤT CẢ nhân viên theo đúng thứ tự STAFF_LIST (không lọc bỏ ai).
    # Người không xuất hiện trong file RingCentral -> nhóm "không có data" (ghi chú).
    active_in_file = df_raw['Ext_Name'].unique()
    active_staff = list(STAFF_LIST)                       # thứ tự report cố định
    no_data_staff = [n for n in active_staff if n not in active_in_file]
    NO_DATA_SET = set(no_data_staff)

    df_active = df_raw[df_raw['Ext_Name'].isin(active_staff)]
    if len(df_active):
        stats = df_active.groupby('Ext_Name').apply(_merge_sessions).reindex(active_staff).fillna(0)
    else:
        stats = pd.DataFrame(
            0, index=active_staff,
            columns=['Actual_Sec', 'Tong_Cuoc_Goi', 'Int_5p', 'Int_10p', 'Int_30p']
        )

    st.session_state['active_staff'] = active_staff
    current_input_display = st.session_state.input_df.loc[active_staff]

    # --- ĐIỀU HƯỚNG TRANG ---
    st.sidebar.markdown("---")
    page = st.sidebar.radio("📄 Chọn trang",
                            ["📝 Nhập doanh số & Điều chỉnh", "📊 Báo cáo & Biểu đồ"],
                            index=0)

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
    st.markdown(f'<div class="main-header">🏆 WORKING RESULTS STATISTICS | {static_time} (EST)</div>', unsafe_allow_html=True)
    t_p, t_t, t_c = int(final_df['Chốt $'].sum()), format_time(final_df['Actual_Sec'].sum()), int(final_df['Tong_Cuoc_Goi'].sum())
    st.markdown(f"""<div class="metric-container">
        <div class="metric-box"><div class="metric-title">💰 Total Premium</div><div class="metric-value">${t_p:,}</div></div>
        <div class="metric-box"><div class="metric-title">⏱️ Total Talktime</div><div class="metric-value">{t_t}</div></div>
        <div class="metric-box"><div class="metric-title">📞 Total Outgoing Calls</div><div class="metric-value">{t_c:,}</div></div>
    </div>""", unsafe_allow_html=True)

    # --- 8. BẢNG HIỂN THỊ ---
    disp_df = pd.DataFrame()
    disp_df['👤 SALES'] = final_df['Sales Name']; disp_df['🏅 LVL'] = final_df['🏅 LVL']
    disp_df['💵 CHỐT $'] = final_df['Chốt $']

    def _fmt_goal(r):
        return "—" if r['📊 RESULT'] == "NO DATA" else format_time(r['target_val'])
    def _fmt_call(r):
        return "—" if r['📊 RESULT'] == "NO DATA" else format_time(r['actual_val'])
    disp_df['🎯 GOAL'] = final_df.apply(_fmt_goal, axis=1)
    disp_df['⏱️ CALL'] = final_df.apply(_fmt_call, axis=1)
    disp_df['📉 GIẢM TALKTIME'] = final_df.apply(
        lambda r: "—" if r['📊 RESULT'] == "NO DATA" else ("🏆 DONE" if r['red_val'] >= 9000 else f"{int(r['red_val']//60)}p"), axis=1)
    disp_df['% HOÀN THÀNH'] = final_df['pct_val']
    disp_df['🔥 5P'] = final_df['Int_5p'].astype(int); disp_df['🔥 10P'] = final_df['Int_10p'].astype(int)
    disp_df['🔥 30P'] = final_df['Int_30p'].astype(int); disp_df['📊 RESULT'] = final_df['📊 RESULT']

    def apply_row_styles(row):
        styles = [''] * len(row); idx = row.name; r = final_df.iloc[idx]
        res = r['📊 RESULT']
        if res == "NO DATA":
            # cả dòng xám nhạt, chữ mờ để dễ nhận ra là không có dữ liệu
            return ['background-color: #f1f5f9; color: #94a3b8;'] * len(row)
        if r['🏅 LVL'] in LEVEL_COLORS: styles[1] = f'background-color: {LEVEL_COLORS[r["🏅 LVL"]]};'
        if r['Chốt $'] > 0: styles[2] = 'background-color: #fee2e2; color: #b91c1c; font-weight: 800;'
        if r['actual_val'] >= r['target_val'] and r['target_val'] > 0:
            styles[4] = 'background-color: #dcfce7; color: #15803d; font-weight: 800;'
        if r['pct_val'] >= 100: styles[6] = 'background-color: #fee2e2; color: #b91c1c; font-weight: 800;'
        if res == "GOOD JOB": styles[10] = 'background-color: #dbeafe; color: #1e40af; font-weight: 800;'
        elif res == "OFF": styles[10] = 'background-color: #f1f5f9; color: #64748b; font-weight: 800;'
        else: styles[10] = 'background-color: #fee2e2; color: #b91c1c; font-weight: 800;'
        return styles

    st.dataframe(disp_df.style.apply(apply_row_styles, axis=1), use_container_width=True, hide_index=True, height=(len(active_staff)*35+50),
        column_config={"💵 CHỐT $": st.column_config.NumberColumn(format="$%d"), "% HOÀN THÀNH": st.column_config.NumberColumn(format="%.1f%%")})

    # --- GHI CHÚ: nhân viên không có dữ liệu talktime ---
    if no_data_staff:
        st.warning(f"📝 **Không có dữ liệu talktime ({len(no_data_staff)}):** " + " • ".join(no_data_staff))

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

    # --- 10. EXPORT ---
    # (a) File hiển thị (như bảng trên)
    st.sidebar.download_button("📥 Export bảng (CSV)", disp_df.to_csv(index=False).encode('utf-8-sig'), f"Report_{file_date}.csv")
    # (b) Snapshot dạng SỐ + có cột Date -> để cộng dồn tuần/tháng sau này
    snapshot = final_df[['Sales Name', '🏅 LVL', 'Xin OFF', 'Chốt $',
                         'target_val', 'actual_val', 'red_val', 'pct_val',
                         'Tong_Cuoc_Goi', 'Int_5p', 'Int_10p', 'Int_30p', '📊 RESULT']].copy()
    snapshot.insert(0, 'Date', file_date)
    st.sidebar.download_button("📦 Export snapshot (gộp tuần/tháng)",
                               snapshot.to_csv(index=False).encode('utf-8-sig'),
                               f"Snapshot_{file_date}.csv")

# ==================== CHƯA CÓ FILE ====================
if not uploaded_file:
    st.info("👋 Chào Team Henry! Hãy tải file RingCentral ở thanh bên để bắt đầu.")
