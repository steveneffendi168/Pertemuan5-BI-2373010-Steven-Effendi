"""Dashboard praktikum BI: Coffee Shop Sales."""

from io import BytesIO
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from coffee_analytics import (
    DAY_NAMES, breakdown, compare_breakdown, daily_summary, filter_data, growth,
    hourly_profile, monthly_summary, previous_period, product_summary,
    recommendations, scenario, summarize, trend_summary,
)

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data_prepared" / "coffee_sales_prepared.csv"
AUDIT_FILE = ROOT / "data_prepared" / "audit_report.json"
COLORS = ["#167A59", "#D35F55", "#417FB0", "#D6A530", "#82649C", "#5A9290", "#A66B7B", "#757E83", "#93AC55"]
METRIC_NAMES = {
    "Penjualan": "total_sales", "Transaksi": "total_transactions",
    "Unit terjual": "total_units", "Nilai per transaksi": "average_transaction_value",
}
LABELS = {
    "transaction_id": "ID transaksi", "transaction_date": "Tanggal",
    "transaction_time": "Waktu", "transaction_qty": "Jumlah unit",
    "store_location": "Gerai", "product_id": "ID produk",
    "product_detail": "Produk", "product_category": "Kategori",
    "product_type": "Tipe produk", "unit_price": "Harga unit", "sales": "Penjualan",
    "month": "Bulan", "hour": "Jam", "day_name_id": "Hari",
    "total_sales": "Total penjualan", "total_transactions": "Transaksi tercatat",
    "total_units": "Unit terjual", "average_transaction_value": "Nilai per transaksi",
    "units_per_transaction": "Unit per transaksi", "sales_share": "Kontribusi (%)",
    "growth_pct": "Pertumbuhan penjualan (%)", "coverage": "Cakupan bulan",
    "transaction_growth_pct": "Pertumbuhan transaksi (%)",
    "average_growth_pct": "Pertumbuhan nilai transaksi (%)",
    "previous_sales": "Penjualan pembanding", "cumulative_share": "Kontribusi kumulatif (%)",
    "min_price": "Harga minimum", "max_price": "Harga maksimum",
    "price_count": "Jumlah variasi harga", "weighted_unit_price": "Harga rata-rata tertimbang",
    "sales_per_day": "Penjualan / hari kalender", "transactions_per_day": "Transaksi / hari kalender",
    "day_of_week": "Urutan hari",
}
FILTER_KEYS = [
    "preset", "dates", "stores", "categories", "types", "products", "days",
    "hours", "comparison_mode", "comparison_dates",
]

st.set_page_config(page_title="Coffee Shop Sales | Analisis Bisnis", page_icon=":material/local_cafe:", layout="wide")
st.html("""
<style>
 .stMainBlockContainer {max-width: 1540px; padding-top: 2rem; padding-bottom: 3rem;}
 h1 {font-size: 2rem !important; letter-spacing: 0 !important;}
 h2 {font-size: 1.4rem !important; letter-spacing: 0 !important;}
 h3 {font-size: 1.1rem !important; letter-spacing: 0 !important;}
 [data-testid="stMetric"] {padding: 16px; border: 1px solid #DDE4E0; border-radius: 6px; background: #FFFFFF; min-height: 116px;}
 [data-testid="stMetricValue"] {font-size: 1.75rem; overflow-wrap: anywhere;}
 [data-testid="stMetricLabel"] {font-size: .85rem;}
 [data-testid="stSidebar"] h2 {font-size: 1.15rem !important;}
 [data-testid="stSidebar"] .stButton button {width: 100%;}
 [data-testid="stCaptionContainer"] {color: #59675F;}
 @media (max-width: 760px) {
   .stMainBlockContainer {padding: 4rem .8rem 2rem;}
   h1 {font-size: 1.6rem !important;}
   [data-testid="stHorizontalBlock"] {flex-wrap: wrap; gap: .8rem;}
   [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {min-width: min(260px, 100%) !important; flex: 1 1 260px !important; width: 100% !important;}
   [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="stColumn"] {min-width: min(150px, 100%) !important; flex: 1 1 150px !important;}
   [data-testid="stMetricValue"] {font-size: 1.25rem;}
   [data-testid="stMetricLabel"] p {white-space: normal; overflow-wrap: anywhere;}
 }
</style>
""")


@st.cache_data(show_spinner=False)
def load_data(path, modified_time):
    data = pd.read_csv(path)
    required = {"transaction_id", "transaction_date", "transaction_qty", "store_location",
                "product_id", "unit_price", "product_category", "product_type", "product_detail", "sales", "hour"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Kolom wajib tidak tersedia: {', '.join(sorted(missing))}")
    data["transaction_date"] = pd.to_datetime(data["transaction_date"]).dt.normalize()
    if data.empty or data["transaction_date"].isna().any():
        raise ValueError("Data kosong atau tanggal tidak valid.")
    data["month"] = data["transaction_date"].dt.strftime("%Y-%m")
    data["day_of_week"] = data["transaction_date"].dt.dayofweek
    data["day_name_id"] = data["day_of_week"].map(dict(enumerate(DAY_NAMES)))
    return data


def fmt(value, decimals=2):
    if value is None or pd.isna(value):
        return "Belum tersedia"
    return f"{value:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def pct(value):
    return f"{fmt(value)}%" if value is not None and pd.notna(value) else "Belum tersedia"


def delta(value, baseline):
    result = growth(value, baseline)
    return f"{fmt(result)}%" if result is not None else None


def table(frame, height="auto", key=None):
    counts = {"transaction_id", "product_id", "store_id", "transaction_qty", "total_transactions", "total_units", "price_count", "hour", "day_of_week", "Hasil", "Jumlah kosong"}
    formats = {
        LABELS.get(column, column): "{:,.0f}" if column in counts else "{:,.2f}"
        for column in frame.select_dtypes(include="number").columns
    }
    shown = frame.rename(columns=LABELS).copy()
    if "Tanggal" in shown:
        shown["Tanggal"] = pd.to_datetime(shown["Tanggal"]).dt.strftime("%d/%m/%Y")
    st.dataframe(shown.style.format(formats, na_rep="-", decimal=",", thousands="."),
                 width="stretch", height=height, hide_index=True, key=key)


def draw(figure, key, height=360):
    figure.update_layout(
        template="plotly_white", height=height,
        font={"family": "Arial, sans-serif", "size": 12, "color": "#34443B"},
        margin={"l": 12, "r": 20, "t": 24, "b": 20}, colorway=COLORS, separators=",.",
        legend={"orientation": "h", "y": -0.2}, hoverlabel={"bgcolor": "white"},
    )
    figure.update_xaxes(showgrid=False, automargin=True)
    figure.update_yaxes(gridcolor="#EAF0EC", zeroline=False, automargin=True)
    st.plotly_chart(figure, width="stretch", key=key, config={"displaylogo": False, "scrollZoom": False})


def bar(frame, dimension, metric="total_sales", horizontal=False, color=None):
    figure = px.bar(
        frame.sort_values(metric, ascending=horizontal),
        x=metric if horizontal else dimension, y=dimension if horizontal else metric,
        orientation="h" if horizontal else "v", color=color,
        color_discrete_sequence=COLORS, labels=LABELS,
    )
    if not color:
        figure.update_traces(marker_color=COLORS[0])
    figure.update_layout(showlegend=bool(color))
    if horizontal:
        figure.update_yaxes(categoryorder="total ascending")
    return figure


def reset_filters():
    for key in FILTER_KEYS:
        st.session_state.pop(key, None)
        st.session_state.pop(f"_{key}_options", None)


def choose(label, options, key, format_func=str):
    previous_options = st.session_state.get(f"_{key}_options", list(options))
    if key not in st.session_state:
        st.session_state[key] = list(options)
    elif st.session_state[key] == previous_options:
        st.session_state[key] = list(options)
    else:
        st.session_state[key] = [value for value in st.session_state[key] if value in options]
    st.session_state[f"_{key}_options"] = list(options)
    return st.multiselect(label, options, key=key, format_func=format_func)


def csv_download(frame, name, key):
    st.download_button("Unduh CSV", frame.to_csv(index=False).encode("utf-8-sig"),
                       file_name=name, mime="text/csv", icon=":material/download:", key=key)


def open_decisions():
    st.session_state["view"] = "Keputusan"


def report_markdown(data, monthly, actions, start, end, scope, comparison_note):
    values = summarize(data)
    lines = [
        "# Analisis Coffee Shop Sales", "", "## Tujuan bisnis", "",
        "Meningkatkan penjualan coffee shop melalui pertumbuhan aktivitas pembelian, peningkatan nilai penjualan, dan pengelolaan gerai serta produk berdasarkan data.",
        "", "## Cakupan", "", f"Periode: {start:%d/%m/%Y} - {end:%d/%m/%Y}.",
        scope, comparison_note, "", "## Indikator", "",
        f"- Total penjualan: {fmt(values['total_sales'])}",
        f"- Transaksi tercatat: {fmt(values['total_transactions'], 0)}",
        f"- Unit terjual: {fmt(values['total_units'], 0)}",
        f"- Rata-rata nilai transaksi: {fmt(values['average_transaction_value'])}",
        f"- Unit per transaksi: {fmt(values['units_per_transaction'])}",
        "", "## Ringkasan bulanan", "",
        "| Bulan | Penjualan | Transaksi | Pertumbuhan | Cakupan |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in monthly.to_dict("records"):
        lines.append(f"| {row['month']} | {fmt(row['total_sales'])} | {fmt(row['total_transactions'], 0)} | {pct(row['growth_pct'])} | {row['coverage']} |")
    lines += ["", "## Keputusan yang diusulkan", ""]
    for action in actions:
        lines += [f"### {action['prioritas']}", "", action["dasar"], "", action["keputusan"], "", f"Evaluasi: {action['indikator']}.", ""]
    lines += ["## Batas interpretasi", "",
              "Mata uang tidak dinyatakan pada sumber. Transaksi tercatat bukan pelanggan unik dan belum dipastikan sebagai seluruh isi struk. Data tidak memuat biaya, laba, stok aktual, durasi layanan, atau riwayat promosi. Rekomendasi adalah usulan untuk diuji."]
    return "\n".join(lines)


def excel_summary(total, monthly, stores, products, categories, hours):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, frame in {
            "Indikator": pd.DataFrame([total]), "Bulanan": monthly, "Gerai": stores,
            "Produk": products, "Kategori": categories, "Jam": hours,
        }.items():
            frame.rename(columns=LABELS).to_excel(writer, sheet_name=name, index=False)
    return output.getvalue()


if not DATA_FILE.is_file():
    st.error("Data siap analisis belum tersedia. Jalankan audit_prepare_coffee.py.")
    st.stop()
try:
    df = load_data(str(DATA_FILE), DATA_FILE.stat().st_mtime_ns)
except (ValueError, OSError, pd.errors.ParserError) as error:
    st.error(f"Data belum dapat dibaca: {error}")
    st.stop()

date_min, date_max = df["transaction_date"].min().date(), df["transaction_date"].max().date()
with st.sidebar:
    st.markdown("## Coffee Shop Sales")
    st.caption("BUSINESS INTELLIGENCE / PERTEMUAN 5")
    st.divider()
    st.subheader("Cakupan analisis")
    preset = st.selectbox("Periode", ["Seluruh data", "Bulan terakhir", "30 hari terakhir", "Kustom"], key="preset")
    if preset == "Kustom":
        dates = st.date_input("Rentang tanggal", value=(date_min, date_max), min_value=date_min,
                              max_value=date_max, format="DD/MM/YYYY", key="dates")
    elif preset == "Bulan terakhir":
        dates = (max(date_min, date_max.replace(day=1)), date_max)
    elif preset == "30 hari terakhir":
        dates = (max(date_min, (pd.Timestamp(date_max) - pd.Timedelta(days=29)).date()), date_max)
    else:
        dates = (date_min, date_max)
    selected_stores = choose("Gerai", sorted(df["store_location"].unique()), "stores")
    selected_categories = choose("Kategori", sorted(df["product_category"].unique()), "categories")
    type_options = sorted(df.loc[df["product_category"].isin(selected_categories), "product_type"].unique())
    selected_types = choose("Tipe produk", type_options, "types")
    candidates = df.loc[df["product_category"].isin(selected_categories) & df["product_type"].isin(selected_types)]
    product_names = candidates.drop_duplicates("product_id").set_index("product_id")["product_detail"].to_dict()
    selected_products = st.session_state.get("products", [])
    st.session_state["products"] = [product for product in selected_products if product in product_names]
    selected_products = st.multiselect("Produk tertentu", sorted(product_names), key="products",
                                      format_func=lambda value: f"{product_names[value]} (ID {value})",
                                      placeholder="Semua produk")
    with st.expander("Hari dan jam"):
        selected_days = choose("Hari", list(range(7)), "days", lambda value: DAY_NAMES[value])
        selected_hours = st.slider("Jam transaksi", 0, 23, (0, 23), format="%d:00", key="hours")
    with st.expander("Periode pembanding"):
        comparison_mode = st.selectbox("Pembanding", ["Tanpa pembanding", "Periode sebelumnya", "Rentang kustom"], key="comparison_mode")
        if comparison_mode == "Rentang kustom":
            comparison_dates = st.date_input("Tanggal pembanding", (date_min, date_max), min_value=date_min,
                                             max_value=date_max, format="DD/MM/YYYY", key="comparison_dates")
        else:
            comparison_dates = None
    st.button("Reset filter", icon=":material/restart_alt:", on_click=reset_filters, key="filter_reset")
    st.divider()
    st.caption(f"Sumber: {date_min:%d/%m/%Y} - {date_max:%d/%m/%Y}")
    st.caption("Mata uang tidak dinyatakan dalam file sumber.")

st.title("Coffee Shop Sales")
if len(dates) != 2:
    st.info("Rentang tanggal belum lengkap.")
    st.stop()
start, end = dates
if start > end:
    st.warning("Tanggal awal harus mendahului tanggal akhir.")
    st.stop()
scope = (
    f"Gerai: {', '.join(selected_stores) or '-'}; kategori: {', '.join(selected_categories) or '-'}; "
    f"tipe: {', '.join(selected_types) or '-'}; produk: {', '.join(str(value) for value in selected_products) or 'semua'}; "
    f"hari: {', '.join(DAY_NAMES[value] for value in selected_days) or '-'}; jam: {selected_hours[0]:02d}:00-{selected_hours[1]:02d}:59."
)
st.caption(f"{start:%d %b %Y} - {end:%d %b %Y}  /  {len(selected_stores)} gerai  /  {len(selected_categories)} kategori")
if "view" not in st.session_state:
    st.session_state["view"] = "Ringkasan"
view = st.segmented_control("Analisis", ["Ringkasan", "Tren", "Gerai", "Produk", "Waktu", "Keputusan", "Data & Audit"],
                            required=True, key="view", wrap=True, label_visibility="collapsed")

kwargs = dict(stores=selected_stores, categories=selected_categories, types=selected_types,
              products=selected_products, days=selected_days, hours=selected_hours)
data = filter_data(df, start, end, **kwargs)
if data.empty:
    st.info("Tidak ada transaksi pada cakupan yang dipilih.")
    st.button("Pulihkan seluruh data", icon=":material/restart_alt:", on_click=reset_filters)
    st.stop()

baseline, baseline_total = None, None
comparison_note = "Tanpa periode pembanding."
if comparison_mode != "Tanpa pembanding":
    compared_dates = previous_period(start, end) if comparison_mode == "Periode sebelumnya" else comparison_dates
    if compared_dates is None or len(compared_dates) != 2:
        comparison_note = "Rentang pembanding belum lengkap; perubahan belum dihitung."
    else:
        before_start, before_end = compared_dates
        if before_start < date_min or before_end > date_max or before_start > before_end:
            comparison_note = "Periode pembanding berada di luar cakupan sumber; perubahan belum dihitung."
        else:
            baseline = filter_data(df, before_start, before_end, **kwargs)
            baseline_total = summarize(baseline)
            comparison_note = f"Pembanding: {before_start:%d/%m/%Y} - {before_end:%d/%m/%Y}; filter gerai, produk, hari, dan jam sama."
            if (before_end - before_start).days != (end - start).days:
                comparison_note += " Durasi berbeda; perubahan di bawah membandingkan total periode."
            if baseline.empty:
                comparison_note += " Tidak ada transaksi pembanding; persentase perubahan belum tersedia."
st.caption(comparison_note)

total = summarize(data)
monthly = monthly_summary(data, start, end, df["transaction_date"].unique())
stores = compare_breakdown(breakdown(data, ["store_location"]), baseline, ["store_location"])
categories = breakdown(data, ["product_category"])
products = product_summary(data)
hours = breakdown(data, ["hour"]).sort_values("hour")
actions = recommendations(data, monthly)
calendar = pd.date_range(start, end)
selected_calendar_days = int(pd.Series(calendar.dayofweek).isin(selected_days).sum())

for column, label, metric, decimals, help_text in zip(
    st.columns(4), ["Total penjualan", "Transaksi tercatat", "Nilai per transaksi", "Unit terjual"],
    ["total_sales", "total_transactions", "average_transaction_value", "total_units"], [2, 0, 2, 0],
    ["Jumlah kuantitas dikali harga unit. Satuan mata uang mengikuti sumber.",
     "Jumlah ID transaksi unik; belum dipastikan sebagai seluruh struk atau pelanggan unik.",
     "Total penjualan dibagi transaksi tercatat dalam cakupan yang sama.", "Jumlah seluruh kuantitas produk terjual."],
):
    column.metric(label, fmt(total[metric], decimals),
                  delta(total[metric], baseline_total[metric]) if baseline_total else None, help=help_text)
st.divider()

if view == "Ringkasan":
    latest = monthly.iloc[-1]
    one, two, three = st.columns(3)
    one.metric(f"Pertumbuhan {latest['month']}", pct(latest["growth_pct"]),
               help="Perbandingan penjualan dua bulan kalender berturut-turut yang keduanya penuh. Bulan parsial tidak dibandingkan.")
    two.metric("Unit per transaksi", fmt(total["units_per_transaction"]))
    three.metric("Penjualan / hari terpilih", fmt(total["total_sales"] / selected_calendar_days),
                 help="Dibagi jumlah hari kalender sesuai pilihan hari, termasuk hari tanpa catatan; bukan ukuran per hari operasional.")
    left, right = st.columns([1.5, 1])
    with left:
        st.subheader("Perjalanan penjualan")
        fig = px.line(monthly, x="month", y="total_sales", markers=True, labels=LABELS,
                      custom_data=["coverage"], color_discrete_sequence=COLORS)
        fig.update_traces(hovertemplate="%{x}<br>Penjualan: %{y:,.2f}<br>%{customdata[0]}<extra></extra>")
        fig.update_yaxes(rangemode="tozero")
        draw(fig, "overview_trend")
    with right:
        st.subheader("Kontribusi gerai")
        draw(bar(stores, "store_location", horizontal=True), "overview_stores")
    st.subheader("Sinyal bisnis")
    lead = categories.iloc[0]
    peak = hours.sort_values("total_transactions", ascending=False).iloc[0]
    st.markdown(f"**{lead['product_category']}** menyumbang **{pct(lead['sales_share'])}** penjualan. Jam **{int(peak['hour']):02d}:00** mencatat aktivitas terbanyak: **{fmt(peak['total_transactions'], 0)}** transaksi.")
    if pd.notna(latest["growth_pct"]):
        st.write(f"Bulan {latest['month']}: penjualan berubah {pct(latest['growth_pct'])}, transaksi {pct(latest['transaction_growth_pct'])}, dan nilai per transaksi {pct(latest['average_growth_pct'])} dibandingkan bulan sebelumnya.")
    else:
        st.caption("Pertumbuhan bulan terakhir belum tersedia karena bulan pembanding belum penuh, tidak tercakup, atau bernilai nol.")
    st.button("Tinjau keputusan bisnis", icon=":material/insights:", on_click=open_decisions)
    with st.expander("Ringkasan bulanan"):
        table(monthly.drop(columns=["sales_share", "units_per_transaction"], errors="ignore"))
        csv_download(monthly, "ringkasan_bulanan.csv", "overview_monthly_csv")

elif view == "Tren":
    left, right = st.columns(2)
    with left:
        frequency = st.segmented_control("Interval", ["Harian", "Mingguan", "Bulanan"], default="Bulanan", required=True, key="trend_frequency")
    with right:
        metric_label = st.selectbox("Ukuran tren", list(METRIC_NAMES), key="trend_metric")
    metric = METRIC_NAMES[metric_label]
    trend = trend_summary(data, start, end, {"Harian": "D", "Mingguan": "W-SUN", "Bulanan": "MS"}[frequency])
    st.subheader(f"Tren {metric_label.lower()}")
    fig = px.line(trend, x="transaction_date", y=metric, markers=True, labels=LABELS)
    if frequency == "Harian":
        fig.add_scatter(x=trend["transaction_date"], y=trend[metric].rolling(7, min_periods=7).mean(),
                        name="Rata-rata 7 hari", line={"color": COLORS[1], "width": 2})
        fig.data[0].name = "Harian"
        fig.update_layout(showlegend=True)
    fig.update_yaxes(rangemode="tozero")
    draw(fig, "trend_series", 410)
    if frequency != "Harian":
        st.caption("Interval pada tepi rentang tanggal dapat berisi sebagian minggu atau bulan.")
    left, right = st.columns(2)
    valid = monthly.dropna(subset=["growth_pct"])
    with left:
        st.subheader("Pertumbuhan penjualan bulanan")
        if valid.empty:
            st.info("Diperlukan dua bulan kalender penuh berturut-turut dengan penjualan pembanding di atas nol.")
        else:
            fig = px.bar(valid, x="month", y="growth_pct", labels=LABELS, text_auto=".2f")
            fig.update_traces(marker_color=[COLORS[0] if value >= 0 else COLORS[1] for value in valid["growth_pct"]])
            fig.update_yaxes(ticksuffix="%")
            draw(fig, "trend_growth")
    with right:
        st.subheader("Perubahan aktivitas dan nilai pembelian")
        if valid.empty:
            st.info("Perubahan bulanan belum tersedia pada cakupan ini.")
        else:
            changes = valid.melt(id_vars="month", value_vars=["transaction_growth_pct", "average_growth_pct"], var_name="Indikator", value_name="Perubahan (%)")
            changes["Indikator"] = changes["Indikator"].map({"transaction_growth_pct": "Transaksi", "average_growth_pct": "Nilai per transaksi"})
            draw(px.bar(changes, x="month", y="Perubahan (%)", color="Indikator", barmode="group", color_discrete_sequence=COLORS, labels=LABELS), "trend_drivers")
    if baseline is not None and not baseline.empty:
        st.subheader("Penjualan harian pada dua periode")
        current_daily = daily_summary(data, start, end)
        before_daily = daily_summary(baseline, before_start, before_end)
        fig = go.Figure()
        for label, daily, color in [("Periode terpilih", current_daily, COLORS[0]), ("Pembanding", before_daily, COLORS[1])]:
            fig.add_scatter(x=list(range(1, len(daily) + 1)), y=daily["total_sales"], name=label, line={"color": color})
        fig.update_layout(xaxis_title="Hari ke dalam masing-masing periode", yaxis_title="Penjualan")
        draw(fig, "trend_compare")
    st.subheader("Angka bulanan")
    table(monthly.drop(columns=["sales_share", "units_per_transaction"], errors="ignore"))
    csv_download(monthly, "ringkasan_bulanan.csv", "trend_monthly_csv")

elif view == "Gerai":
    metric_label = st.selectbox("Ukuran perbandingan", list(METRIC_NAMES), key="store_metric")
    metric = METRIC_NAMES[metric_label]
    left, right = st.columns(2)
    with left:
        st.subheader("Kinerja antar gerai")
        draw(bar(stores, "store_location", metric, color="store_location"), "store_rank")
    with right:
        st.subheader("Aktivitas dan nilai pembelian")
        fig = px.scatter(stores, x="total_transactions", y="average_transaction_value", size="total_units",
                         color="store_location", hover_name="store_location", size_max=55,
                         color_discrete_sequence=COLORS, labels=LABELS)
        draw(fig, "store_scatter")
    display_stores = stores.copy()
    display_stores["sales_per_day"] = display_stores["total_sales"] / selected_calendar_days
    table(display_stores)
    st.caption("Penjualan per hari memakai hari kalender terpilih, bukan jam buka atau kapasitas gerai.")
    csv_download(display_stores, "perbandingan_gerai.csv", "store_csv")
    st.subheader("Tren bulanan setiap gerai")
    store_month = breakdown(data, ["month", "store_location"])
    store_index = pd.MultiIndex.from_product([monthly["month"], selected_stores], names=["month", "store_location"])
    store_month = store_month.set_index(["month", "store_location"]).reindex(store_index).reset_index()
    store_month["total_sales"] = store_month["total_sales"].fillna(0)
    draw(px.line(store_month, x="month", y="total_sales", color="store_location", markers=True, labels=LABELS, color_discrete_sequence=COLORS), "store_month", 390)
    focus = st.selectbox("Profil gerai", sorted(data["store_location"].unique()), key="store_focus")
    focused = data.loc[data["store_location"].eq(focus)]
    left, right = st.columns(2)
    with left:
        st.subheader(f"Kategori di {focus}")
        draw(bar(breakdown(focused, ["product_category"]), "product_category", horizontal=True), "store_categories")
    with right:
        st.subheader(f"Aktivitas jam di {focus}")
        draw(bar(breakdown(focused, ["hour"]), "hour", "total_transactions"), "store_hours")

elif view == "Produk":
    one, two = st.columns(2)
    with one:
        metric_label = st.selectbox("Peringkat berdasarkan", ["Penjualan", "Transaksi", "Unit terjual"], key="product_metric")
    with two:
        top_n = st.slider("Jumlah produk teratas", 5, 30, 10, step=5, key="product_limit")
    metric = METRIC_NAMES[metric_label]
    ranked = products.sort_values(metric, ascending=False).head(top_n).copy()
    ranked["Produk"] = ranked["product_detail"] + " (ID " + ranked["product_id"].astype(str) + ")"
    threshold_count = min(len(products), int(products["cumulative_share"].lt(80).sum()) + 1)
    one, two, three = st.columns(3)
    one.metric("Produk terjual", fmt(len(products), 0))
    two.metric("Kontribusi 10 produk teratas", pct(products.head(10)["sales_share"].sum()))
    three.metric("Produk untuk 80% penjualan", fmt(threshold_count, 0))
    st.subheader(f"{min(top_n, len(ranked))} produk teratas berdasarkan {metric_label.lower()}")
    draw(bar(ranked, "Produk", metric, horizontal=True), "product_rank", max(360, len(ranked) * 27 + 80))
    left, right = st.columns(2)
    with left:
        st.subheader("Kontribusi kategori")
        draw(bar(categories, "product_category", horizontal=True), "product_categories")
    with right:
        st.subheader("Tipe produk teratas")
        draw(bar(breakdown(data, ["product_type"]).head(10), "product_type", horizontal=True), "product_types")
    st.subheader("Konsentrasi penjualan produk")
    pareto = products.copy()
    pareto["rank"] = list(range(1, len(pareto) + 1))
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=pareto["rank"], y=pareto["total_sales"], name="Penjualan",
                         marker_color=COLORS[0], customdata=pareto["product_detail"],
                         hovertemplate="%{customdata}<br>Penjualan: %{y:,.2f}<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Scatter(x=pareto["rank"], y=pareto["cumulative_share"], name="Kontribusi kumulatif", line={"color": COLORS[1]}), secondary_y=True)
    fig.update_yaxes(title_text="Penjualan", secondary_y=False)
    fig.update_yaxes(title_text="Kontribusi kumulatif (%)", range=[0, 105], secondary_y=True)
    fig.update_xaxes(title_text="Peringkat produk berdasarkan penjualan")
    fig.add_hline(y=80, line_dash="dot", line_color="#757E83", secondary_y=True)
    draw(fig, "product_pareto", 390)
    st.subheader("Daftar kinerja produk")
    search = st.text_input("Cari produk pada tabel", key="product_search")
    compared_products = compare_breakdown(products, baseline, ["product_id", "product_detail", "product_category", "product_type"])
    shown_products = compared_products.loc[compared_products["product_detail"].str.contains(search, case=False, regex=False)]
    table(shown_products, height=430)
    csv_download(shown_products, "kinerja_produk.csv", "product_csv")
    names = products.set_index("product_id")["product_detail"].to_dict()
    focus_id = st.selectbox("Detail produk", products["product_id"].tolist(),
                            format_func=lambda value: f"{names[value]} (ID {value})", key="product_focus")
    focused = data.loc[data["product_id"].eq(focus_id)]
    detail = products.loc[products["product_id"].eq(focus_id)].iloc[0]
    one, two, three = st.columns(3)
    one.metric("Penjualan produk", fmt(detail["total_sales"]))
    two.metric("Unit produk terjual", fmt(detail["total_units"], 0))
    three.metric("Harga rata-rata tertimbang", fmt(detail["weighted_unit_price"]), help="Penjualan dibagi unit terjual; memperhitungkan kuantitas pada tiap harga.")
    st.caption(f"Harga tercatat: {fmt(detail['min_price'])} - {fmt(detail['max_price'])}; {int(detail['price_count'])} variasi. Variasi harga dipertahankan sesuai sumber.")
    detail_month = monthly_summary(focused, start, end, df["transaction_date"].unique())
    draw(px.line(detail_month, x="month", y="total_sales", markers=True, labels=LABELS), "product_detail_trend")

elif view == "Waktu":
    normalize = st.toggle("Rata-rata per hari kalender terpilih", value=True, key="time_normalize")
    peak_hour = hours.sort_values("total_transactions", ascending=False).iloc[0]
    weekdays = breakdown(data, ["day_of_week", "day_name_id"]).sort_values("day_of_week")
    calendar_days = pd.Series(calendar.dayofweek).value_counts()
    weekdays["transactions_per_day"] = weekdays["total_transactions"] / weekdays["day_of_week"].map(calendar_days)
    best_day = weekdays.sort_values("transactions_per_day" if normalize else "total_transactions", ascending=False).iloc[0]
    one, two, three = st.columns(3)
    one.metric("Jam teraktif", f"{int(peak_hour['hour']):02d}:00")
    two.metric("Hari teraktif", best_day["day_name_id"])
    three.metric("Hari dengan catatan", fmt(data["transaction_date"].nunique(), 0), help="Hari yang memiliki transaksi dalam cakupan filter; tidak menyatakan hari buka gerai.")
    left, right = st.columns(2)
    with left:
        st.subheader("Pola pembelian per jam")
        chart_hours = hours.copy()
        chart_hours["Jam"] = chart_hours["hour"].map(lambda value: f"{int(value):02d}:00")
        chart_hours["Aktivitas"] = chart_hours["total_transactions"] / selected_calendar_days if normalize else chart_hours["total_transactions"]
        draw(px.bar(chart_hours, x="Jam", y="Aktivitas", color_discrete_sequence=COLORS), "time_hour")
    with right:
        st.subheader("Pola pembelian per hari")
        weekdays["Aktivitas"] = weekdays["transactions_per_day"] if normalize else weekdays["total_transactions"]
        draw(px.bar(weekdays, x="day_name_id", y="Aktivitas", labels=LABELS, color_discrete_sequence=[COLORS[2]]), "time_day")
    st.subheader("Peta aktivitas hari dan jam")
    heatmap = hourly_profile(data, start, end, selected_days, selected_hours, normalize)
    fig = px.imshow(heatmap, aspect="auto", text_auto=".1f" if normalize else ".0f",
                    color_continuous_scale=["#F3F5F4", "#ABE0C4", "#167A59"],
                    labels={"x": "Jam", "y": "Hari", "color": "Transaksi / hari" if normalize else "Transaksi"})
    draw(fig, "time_heatmap", 390)
    st.caption("Rata-rata dibagi jumlah kemunculan hari kalender dalam rentang terpilih, termasuk tanggal tanpa catatan. Nilai nol tidak otomatis berarti gerai tutup.")
    st.subheader("Aktivitas jam setiap gerai")
    store_hours = data.pivot_table(index="store_location", columns="hour", values="transaction_id", aggfunc="nunique", fill_value=0)
    store_hours.columns = [f"{int(hour):02d}:00" for hour in store_hours.columns]
    if normalize:
        store_hours = store_hours / selected_calendar_days
    draw(px.imshow(store_hours, aspect="auto", color_continuous_scale=["#F3F5F4", "#B9D6EA", "#417FB0"],
                   labels={"x": "Jam", "y": "Gerai", "color": "Transaksi / hari" if normalize else "Transaksi"}), "time_store_heatmap", 300)
    with st.expander("Angka aktivitas per jam dan hari"):
        table(hours)
        table(weekdays.drop(columns=["Aktivitas"], errors="ignore"))
        csv_download(hours, "aktivitas_jam.csv", "time_csv")

elif view == "Keputusan":
    st.subheader("Tujuan bisnis")
    st.write("Meningkatkan penjualan coffee shop melalui pertumbuhan aktivitas pembelian, peningkatan nilai penjualan, dan pengelolaan gerai serta produk berdasarkan data.")
    st.subheader("Prioritas tindakan")
    for action in actions:
        st.markdown(f"#### {action['prioritas']}")
        st.caption(action["dasar"])
        st.write(action["keputusan"])
        st.caption(f"Evaluasi: {action['indikator']}.")
    st.divider()
    st.subheader("Simulasi target penjualan")
    one, two = st.columns(2)
    with one:
        target_transactions = st.number_input("Target kenaikan transaksi (%)", min_value=-100.0, max_value=100.0, value=5.0, step=0.5, key="target_transactions")
    with two:
        target_average = st.number_input("Target kenaikan nilai per transaksi (%)", min_value=-100.0, max_value=100.0, value=3.0, step=0.5, key="target_average")
    projection = scenario(total["total_sales"], target_transactions, target_average)
    one, two, three = st.columns(3)
    one.metric("Penjualan dalam simulasi", fmt(projection["projected_sales"]))
    two.metric("Tambahan nilai penjualan", fmt(projection["additional_sales"]))
    three.metric("Pertumbuhan gabungan", pct(projection["growth_pct"]))
    st.caption("Asumsi: durasi dan cakupan sama dengan periode terpilih; penjualan = transaksi x nilai per transaksi. Target 5% dan 3% adalah contoh yang dapat diubah, bukan hasil prediksi atau target resmi.")
    st.caption("Pelaksanaan tindakan memerlukan evaluasi periode yang setara. Sumber belum memuat biaya, laba, persediaan aktual, antrean, atau riwayat promosi.")
    decision_report = report_markdown(data, monthly, actions, start, end, scope, comparison_note)
    decision_report += f"\n\n## Simulasi target\n\nKenaikan transaksi: {pct(target_transactions)}; kenaikan nilai transaksi: {pct(target_average)}. Penjualan simulasi: {fmt(projection['projected_sales'])}; pertumbuhan gabungan: {pct(projection['growth_pct'])}. Simulasi bersifat asumsi, bukan prediksi.\n"
    st.download_button("Unduh laporan keputusan", decision_report.encode("utf-8"), "laporan_keputusan.md",
                       mime="text/markdown", icon=":material/download:", key="decisions_report")

elif view == "Data & Audit":
    data_tab, summary_tab, audit_tab = st.tabs(["Transaksi", "Ekspor ringkasan", "Audit sumber"])
    with data_tab:
        st.subheader("Transaksi pada cakupan terpilih")
        search = st.text_input("Cari nama produk atau ID transaksi", key="transaction_search")
        searched = data.loc[data["product_detail"].str.contains(search, case=False, regex=False)
                            | data["transaction_id"].astype(str).str.contains(search, regex=False)]
        page_size = st.selectbox("Baris per halaman", [100, 250, 500], key="page_size")
        max_page = max(1, (len(searched) + page_size - 1) // page_size)
        if st.session_state.get("transaction_page", 1) > max_page:
            st.session_state["transaction_page"] = 1
        if "transaction_page" not in st.session_state:
            st.session_state["transaction_page"] = 1
        page = st.number_input("Halaman", min_value=1, max_value=max_page, value=None, step=1, key="transaction_page")
        st.caption(f"{fmt(len(searched), 0)} transaksi ditemukan; halaman {page} dari {max_page}.")
        detail_columns = ["transaction_id", "transaction_date", "transaction_time", "store_location",
                          "product_id", "product_detail", "product_category", "product_type",
                          "transaction_qty", "unit_price", "sales"]
        table(searched.iloc[(page - 1) * page_size:page * page_size][detail_columns], height=480)
        st.download_button("Unduh seluruh transaksi terfilter", data.to_csv(index=False).encode("utf-8-sig"),
                           "transaksi_terfilter.csv", mime="text/csv", icon=":material/download:", key="transactions_csv")
        st.caption(f"Ekspor mencakup {fmt(len(data), 0)} baris sesuai filter global; pencarian tabel hanya membatasi tampilan.")
    with summary_tab:
        st.subheader("Ringkasan analisis")
        table(monthly.drop(columns=["sales_share", "units_per_transaction"], errors="ignore"))
        st.download_button("Unduh ringkasan Excel", excel_summary(total, monthly, stores, products, categories, hours),
                           "ringkasan_coffee_shop.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           icon=":material/download:", key="summary_excel")
        st.download_button("Unduh laporan analisis", report_markdown(data, monthly, actions, start, end, scope, comparison_note).encode("utf-8"),
                           "laporan_analisis.md", mime="text/markdown", icon=":material/download:", key="analysis_report")
    with audit_tab:
        st.subheader("Kualitas sumber data")
        st.caption("Audit berikut berlaku pada seluruh sumber, sebelum filter dashboard.")
        try:
            audit = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            audit = None
        if audit:
            if audit.get("status") == "LULUS AUDIT DASAR":
                st.success(audit["status"])
            else:
                st.warning(audit.get("status", "Status audit belum tersedia"))
            one, two, three = st.columns(3)
            one.metric("Baris sumber", fmt(audit.get("original_rows"), 0))
            two.metric("Nilai kosong sumber", fmt(sum(audit.get("missing_before", {}).values()), 0))
            three.metric("ID transaksi berulang", fmt(audit.get("duplicate_transaction_ids"), 0))
            quality = pd.DataFrame({
                "Pemeriksaan": ["Baris awal", "Baris siap analisis", "Baris duplikat awal", "Produk dengan variasi harga", "Spasi teks diperbaiki", "Tanggal tanpa catatan"],
                "Hasil": [audit.get("original_rows", 0), audit.get("prepared_rows", 0), audit.get("duplicate_rows_before", 0),
                          audit.get("products_with_multiple_prices", 0), sum(audit.get("trimmed_values", {}).values()), len(audit.get("dates_without_records", []))],
            })
            table(quality)
            for issue in audit.get("issues", []):
                st.warning(issue)
            st.download_button("Unduh hasil audit", json.dumps(audit, indent=2, ensure_ascii=False).encode("utf-8"),
                               "audit_report.json", mime="application/json", icon=":material/download:", key="audit_json")
            with st.expander("Nilai kosong per kolom"):
                table(pd.DataFrame(list(audit.get("missing_before", {}).items()), columns=["Kolom", "Jumlah kosong"]))
        else:
            st.warning("Berkas audit belum tersedia atau tidak valid.")
        source_products = product_summary(df)
        with st.expander("Produk dengan variasi harga"):
            table(source_products.loc[source_products["price_count"].gt(1),
                                      ["product_id", "product_detail", "min_price", "max_price", "price_count"]])
        st.subheader("Definisi dan batas interpretasi")
        definitions = pd.DataFrame([
            ["Penjualan", "Kuantitas x harga unit; dijumlahkan sesuai cakupan."],
            ["Transaksi tercatat", "Jumlah ID transaksi unik; bukan pelanggan unik atau ukuran struk yang telah dipastikan."],
            ["Nilai per transaksi", "Total penjualan / transaksi tercatat."],
            ["Pertumbuhan bulanan", "(Penjualan bulan ini / bulan sebelumnya - 1) x 100%; dua bulan kalender penuh."],
            ["Perubahan terhadap pembanding", "(Nilai periode terpilih / nilai periode pembanding - 1) x 100%; filter dimensi sama."],
            ["Harga rata-rata tertimbang", "Penjualan produk / jumlah unit produk."],
            ["Satuan dan cakupan", "Mata uang tidak dinyatakan. Sumber mencakup Januari-Juni 2023."],
            ["Informasi yang belum tersedia", "Biaya, laba, pelanggan unik, stok aktual, durasi layanan, dan riwayat promosi."],
        ], columns=["Indikator", "Definisi"])
        st.dataframe(definitions, hide_index=True, width="stretch", row_height=60)

st.divider()
st.caption(f"{fmt(total['total_transactions'], 0)} transaksi tercatat / {fmt(data['product_id'].nunique(), 0)} produk / {fmt(data['transaction_date'].nunique(), 0)} hari dengan catatan. Transaksi tercatat belum dipastikan sebagai seluruh isi struk pelanggan.")
