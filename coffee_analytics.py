"""Perhitungan dashboard yang dapat diverifikasi tanpa menjalankan Streamlit."""

import pandas as pd

DAY_NAMES = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
METRICS = ["total_sales", "total_transactions", "total_units"]


def filter_data(data, start, end, stores, categories, types, products, days, hours):
    dates = data["transaction_date"]
    mask = (
        dates.between(pd.Timestamp(start), pd.Timestamp(end))
        & data["store_location"].isin(stores)
        & data["product_category"].isin(categories)
        & data["product_type"].isin(types)
        & data["day_of_week"].isin(days)
        & data["hour"].between(*hours)
    )
    if products:
        mask &= data["product_id"].isin(products)
    return data.loc[mask].copy()


def summarize(data):
    sales = float(data["sales"].sum())
    transactions = int(data["transaction_id"].nunique())
    units = int(data["transaction_qty"].sum())
    return {
        "total_sales": sales,
        "total_transactions": transactions,
        "total_units": units,
        "average_transaction_value": sales / transactions if transactions else None,
        "units_per_transaction": units / transactions if transactions else None,
    }


def growth(current, previous):
    if previous is None or pd.isna(previous) or previous == 0 or current is None:
        return None
    return (current / previous - 1) * 100


def previous_period(start, end):
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    duration = end - start + pd.Timedelta(days=1)
    return (start - duration).date(), (start - pd.Timedelta(days=1)).date()


def breakdown(data, dimensions):
    result = data.groupby(dimensions, as_index=False, observed=True).agg(
        total_sales=("sales", "sum"),
        total_transactions=("transaction_id", "nunique"),
        total_units=("transaction_qty", "sum"),
    )
    result["average_transaction_value"] = (
        result["total_sales"] / result["total_transactions"].replace(0, float("nan"))
    )
    result["units_per_transaction"] = (
        result["total_units"] / result["total_transactions"].replace(0, float("nan"))
    )
    total = result["total_sales"].sum()
    result["sales_share"] = result["total_sales"] / total * 100 if total else 0.0
    return result.sort_values("total_sales", ascending=False).reset_index(drop=True)


def compare_breakdown(current, previous, dimensions):
    result = current.copy()
    if previous is None:
        result["previous_sales"] = float("nan")
    else:
        baseline = breakdown(previous, dimensions)[dimensions + ["total_sales"]]
        baseline = baseline.rename(columns={"total_sales": "previous_sales"})
        result = result.merge(baseline, on=dimensions, how="outer")
        additive = METRICS + ["sales_share", "previous_sales"]
        result[additive] = result[additive].fillna(0)
    result["growth_pct"] = (
        (result["total_sales"] / result["previous_sales"] - 1) * 100
    ).where(result["previous_sales"].gt(0))
    return result.sort_values("total_sales", ascending=False).reset_index(drop=True)


def daily_summary(data, start, end):
    daily = breakdown(data, ["transaction_date"]).set_index("transaction_date")
    calendar = pd.date_range(start, end, name="transaction_date")
    daily = daily.reindex(calendar)
    daily[METRICS] = daily[METRICS].fillna(0)
    daily["average_transaction_value"] = (
        daily["total_sales"] / daily["total_transactions"].replace(0, float("nan"))
    )
    return daily.reset_index()


def trend_summary(data, start, end, frequency="D"):
    daily = daily_summary(data, start, end).set_index("transaction_date")
    if frequency != "D":
        daily = daily[METRICS].resample(frequency).sum()
    daily["average_transaction_value"] = (
        daily["total_sales"] / daily["total_transactions"].replace(0, float("nan"))
    )
    return daily.reset_index()


def monthly_summary(data, start, end, source_dates):
    periods = pd.period_range(start, end, freq="M")
    monthly = breakdown(data, ["month"]).set_index("month")
    monthly = monthly.reindex(periods.astype(str))
    monthly.index.name = "month"
    monthly[METRICS] = monthly[METRICS].fillna(0)
    monthly["average_transaction_value"] = (
        monthly["total_sales"] / monthly["total_transactions"].replace(0, float("nan"))
    )
    source_dates = set(pd.DatetimeIndex(source_dates).normalize())
    statuses = []
    for period in periods:
        full_month = pd.date_range(period.start_time, period.end_time.normalize())
        is_full = (
            pd.Timestamp(start) <= period.start_time
            and pd.Timestamp(end) >= period.end_time.normalize()
            and all(day in source_dates for day in full_month)
        )
        statuses.append("Penuh" if is_full else "Parsial / cakupan tidak lengkap")
    monthly["coverage"] = statuses
    complete = monthly["coverage"].eq("Penuh")
    comparable = complete & complete.shift(1, fill_value=False)
    for metric, column in [
        ("total_sales", "growth_pct"),
        ("total_transactions", "transaction_growth_pct"),
        ("average_transaction_value", "average_growth_pct"),
    ]:
        previous = monthly[metric].shift(1)
        monthly[column] = ((monthly[metric] / previous - 1) * 100).where(
            comparable & previous.gt(0)
        )
    return monthly.reset_index()


def product_summary(data):
    dimensions = ["product_id", "product_detail", "product_category", "product_type"]
    products = breakdown(data, dimensions)
    prices = data.groupby("product_id", as_index=False).agg(
        min_price=("unit_price", "min"),
        max_price=("unit_price", "max"),
        price_count=("unit_price", "nunique"),
    )
    products = products.merge(prices, on="product_id", how="left")
    products["weighted_unit_price"] = (
        products["total_sales"] / products["total_units"].replace(0, float("nan"))
    )
    products["cumulative_share"] = products["sales_share"].cumsum()
    return products


def hourly_profile(data, start, end, days, hours, normalized=False):
    day_range = sorted(days)
    hour_range = list(range(hours[0], hours[1] + 1))
    counts = data.groupby(["day_of_week", "hour"])["transaction_id"].nunique()
    index = pd.MultiIndex.from_product(
        [day_range, hour_range], names=["day_of_week", "hour"]
    )
    counts = counts.reindex(index, fill_value=0).unstack("hour").astype(float)
    if normalized:
        calendar = pd.Series(pd.date_range(start, end).dayofweek).value_counts()
        denominator = calendar.reindex(day_range, fill_value=0).replace(0, float("nan"))
        counts = counts.div(denominator, axis=0)
    counts.index = [DAY_NAMES[day] for day in counts.index]
    counts.columns = [f"{hour:02d}:00" for hour in counts.columns]
    return counts


def scenario(sales, transaction_target, average_target):
    projected = sales * (1 + transaction_target / 100) * (1 + average_target / 100)
    return {
        "projected_sales": projected,
        "additional_sales": projected - sales,
        "growth_pct": growth(projected, sales),
    }


def recommendations(data, monthly):
    total = summarize(data)
    stores = breakdown(data, ["store_location"])
    categories = breakdown(data, ["product_category"])
    products = product_summary(data)
    hours = breakdown(data, ["hour"]).sort_values("total_transactions", ascending=False)
    if data.empty:
        return []
    category, product, peak = categories.iloc[0], products.iloc[0], hours.iloc[0]
    result = [
        {
            "prioritas": "1. Produk",
            "dasar": f"{category['product_category']}: {category['sales_share']:.2f}% penjualan; produk teratas: {product['product_detail']} (ID {product['product_id']}).",
            "keputusan": "Prioritaskan pemeriksaan persediaan kategori dan produk utama, lalu tinjau frekuensi kehabisan stok dari catatan gerai.",
            "indikator": "Penjualan produk dan unit terjual",
        },
        {
            "prioritas": "2. Operasional",
            "dasar": f"Jam {int(peak['hour']):02d}:00 mencatat {int(peak['total_transactions']):,} transaksi dalam periode terpilih.",
            "keputusan": "Sesuaikan kesiapan staf dan persediaan pada jam sibuk setelah memeriksa kapasitas layanan.",
            "indikator": "Transaksi dan penjualan pada jam sibuk",
        },
    ]
    store = stores.sort_values("average_transaction_value").iloc[0]
    result.append(
        {
            "prioritas": "3. Nilai pembelian",
            "dasar": f"{store['store_location']}: rata-rata {store['average_transaction_value']:.2f}; rata-rata cakupan terpilih {total['average_transaction_value']:.2f}.",
            "keputusan": f"Uji penawaran produk pelengkap di {store['store_location']}; pilih pasangan produk sesuai kategori yang tersedia dan pantau respons.",
            "indikator": "Rata-rata nilai transaksi dan unit per transaksi",
        }
    )
    if len(stores) > 1:
        result.append(
            {
                "prioritas": "4. Gerai",
                "dasar": f"{stores.iloc[0]['store_location']} memiliki penjualan tertinggi dalam cakupan terpilih.",
                "keputusan": "Bandingkan bauran produk dan pola waktu antar gerai untuk memilih uji promosi lokal pada gerai dengan peluang yang terukur.",
                "indikator": "Penjualan, transaksi, dan pertumbuhan setiap gerai",
            }
        )
    valid = monthly.dropna(subset=["growth_pct"])
    if not valid.empty:
        latest = valid.iloc[-1]
        result.append(
            {
                "prioritas": "5. Pertumbuhan",
                "dasar": f"Pertumbuhan bulan penuh {latest['month']}: {latest['growth_pct']:.2f}%; transaksi {latest['transaction_growth_pct']:.2f}%.",
                "keputusan": "Telusuri kontribusi perubahan transaksi dan nilai transaksi; evaluasi tindakan dengan periode pembanding yang setara.",
                "indikator": "Pertumbuhan penjualan, transaksi, dan nilai transaksi",
            }
        )
    return result
