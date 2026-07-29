from __future__ import annotations

from datetime import date
import os
from pathlib import Path
import re
from typing import Iterable

import pandas as pd


BASE_DIR = Path(__file__).parent
CURRENT_DATE = pd.Timestamp.today().date()
PRODUCT_TYPES = ["Charger", "Cable", "Charger + Cable Bundle"]
NUMERIC_CHART_FIELDS = {
    "Price Num",
    "Was Price Num",
    "Max Output Power Num",
    "Cable Length Num",
    "Product Value",
    "Bundle Set Count",
    "Available SKUs",
    "Pickup SKUs",
    "Discounted SKUs",
    "Discount Rate",
}
BRAND_COLOR_PALETTE = [
    "#2563EB",
    "#DC2626",
    "#16A34A",
    "#9333EA",
    "#EA580C",
    "#0891B2",
    "#C026D3",
    "#65A30D",
    "#BE123C",
    "#0D9488",
    "#CA8A04",
    "#4F46E5",
    "#E11D48",
    "#0284C7",
    "#7C2D12",
    "#047857",
    "#B45309",
    "#1D4ED8",
    "#A21CAF",
    "#64748B",
]
DISPLAY_FIELDS = [
    "Brand",
    "Model Number / Product ID",
    "Product Name",
    "Pickup or Not",
    "Sold by",
    "Price",
    "Was Price",
    "Rating",
    "Number of Reviews",
    "Pack",
    "Bundle",
    "Connect Type/Ports",
    "Fast Charging",
    "Max Output Power",
    "Cable Length",
    "Charging Tech",
    "Warranty",
]


VALUE_LOGIC = {
    "Charger": {
        "axis": "Product Value (Charger)",
        "text": (
            "Value logic: Chargers are ranked mainly by max output power. "
            "Within the same power tier, more useful ports and charging technologies "
            "such as GaN, PD, PPS, and foldable plug increase value."
        ),
    },
    "Cable": {
        "axis": "Product Value (Cable)",
        "text": (
            "Value logic: Cables are ranked mainly by cable length. "
            "Within the same length tier, higher supported charging power increases value; "
            "connector type and cable technologies such as certification or braided build add extra value."
        ),
    },
    "Charger + Cable Bundle": {
        "axis": "Product Value (Bundle)",
        "text": (
            "Value logic: Bundles are ranked by complete usable charging sets, not simply by item count. "
            "Usable power is limited by the weakest charger-cable pairing; extra items add value only "
            "when they create additional useful charging sets."
        ),
    },
}


def parse_number(value):
    if pd.isna(value) or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").replace("$", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else None


def parse_cable_length(value):
    if pd.isna(value) or value == "":
        return None
    text = str(value).lower().replace("-", " ")
    lengths = []
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:ft|feet|foot|')\b", text):
        lengths.append(float(match.group(1)))
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:m|meter|meters)\b", text):
        lengths.append(round(float(match.group(1)) * 3.28, 2))
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:in|inch|inches|\")\b", text):
        lengths.append(round(float(match.group(1)) / 12, 2))
    return max(lengths) if lengths else None


def parse_tracking_date(column_name):
    if isinstance(column_name, (pd.Timestamp, date)):
        return pd.to_datetime(column_name).date()
    text = str(column_name).strip()
    if not re.match(r"^20\d{2}[-/]\d{1,2}[-/]\d{1,2}$", text):
        return None
    try:
        return pd.to_datetime(text).date()
    except Exception:
        return None


def tracking_date_columns(df):
    columns = []
    for column in df.columns:
        parsed = parse_tracking_date(column)
        if parsed is not None:
            columns.append((column, parsed))
    return sorted(columns, key=lambda item: item[1])


def normalize_brand(value) -> str:
    text = "" if pd.isna(value) else str(value).strip()
    text = re.sub(r"\s+", " ", text).replace("™", "")
    if text.lower() == "liquipel":
        return "Powertek"
    return text if text else "Unknown"


def normalize_product_type(value) -> str:
    text = "" if pd.isna(value) else str(value).strip()
    key = re.sub(r"\s+", " ", text.lower())
    if key in {"charger", "charging adapter", "wall charger"}:
        return "Charger"
    if key in {"cable", "charging cable", "data cable"}:
        return "Cable"
    if "bundle" in key or ("charger" in key and "cable" in key):
        return "Charger + Cable Bundle"
    return text if text else "Unknown"


def normalize_pickup(value) -> str:
    text = "" if pd.isna(value) else str(value).strip().lower()
    if "pickup" in text or "in-store" in text or "instore" in text:
        return "Pickup"
    if "online" in text or "shipping" in text:
        return "Online"
    return "N/A" if not text else str(value).strip().title()


def normalize_yes_no(value) -> str:
    text = "" if pd.isna(value) else str(value).strip().lower()
    if text in {"yes", "y", "true", "fast", "fast charging"}:
        return "Yes"
    if text in {"no", "n", "false"}:
        return "No"
    return "N/A" if not text else str(value).strip().title()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "Pickup or not": "Pickup or Not",
        "URL of Image": "Image URL",
        "Image URL": "Image URL",
        "Model Number": "Model Number / Product ID",
        "Product ID": "Model Number / Product ID",
        "Max output power": "Max Output Power",
        "Max Output Power/W": "Max Output Power",
        "Cable length": "Cable Length",
        "Connect Type": "Connect Type/Ports",
        "Ports": "Connect Type/Ports",
        "Fast charging": "Fast Charging",
        "Charging technology": "Charging Tech",
    }
    df = df.rename(columns=rename).copy()
    defaults = {
        "Channel": "",
        "Product Type": "",
        "Brand": "",
        "Model Number / Product ID": "",
        "Product Name": "",
        "Image URL": "",
        "Pickup or Not": "",
        "Sold by": "",
        "Price": "",
        "Was Price": "",
        "Rating": "",
        "Number of Reviews": "",
        "Pack": "",
        "Bundle": "",
        "Connect Type/Ports": "",
        "Fast Charging": "",
        "Max Output Power": "",
        "Cable Length": "",
        "Charging Tech": "",
        "Warranty": "",
        "Link": "",
    }
    for column, default in defaults.items():
        if column not in df.columns:
            df[column] = default
    return df


def product_type_options(df: pd.DataFrame) -> list[str]:
    seen = {normalize_product_type(value) for value in df.get("Product Type", pd.Series(dtype=str)).dropna()}
    ordered = [item for item in PRODUCT_TYPES if item in seen]
    extras = sorted(item for item in seen if item not in PRODUCT_TYPES and item)
    return ordered + extras or PRODUCT_TYPES


def status_events(row, date_cols):
    events = []
    for column, event_date in date_cols:
        value = row.get(column)
        if pd.isna(value) or value == "":
            continue
        text = str(value).lower()
        if "add" in text:
            events.append((event_date, "available"))
        if "unavailable" in text or "sold out" in text:
            events.append((event_date, "unavailable"))
    return events


def status_on_date(events, query_date):
    status = "unavailable"
    for event_date, event_status in events:
        if event_date <= query_date:
            status = event_status
    return status


def is_discounted(row) -> bool:
    was = row.get("Was Price Num")
    price = row.get("Price Num")
    return pd.notna(was) and pd.notna(price) and was > price


def parse_port_counts(value) -> dict[str, int]:
    text = "" if pd.isna(value) else str(value).upper()

    def count_token(token: str) -> int:
        total = 0
        escaped = re.escape(token)
        for match in re.finditer(rf"(\d+)\s*(?:\*|X)?\s*{escaped}", text):
            total += int(match.group(1))
        text_without_multipliers = re.sub(rf"\d+\s*(?:\*|X)?\s*{escaped}", "", text)
        total += len(re.findall(escaped, text_without_multipliers))
        return total

    usb_c = count_token("USB-C")
    usb_a = count_token("USB-A")
    lightning = len(re.findall(r"LIGHTNING", text))
    total = usb_c + usb_a + lightning
    if total == 0 and text.strip():
        total = 1
    return {"usb_c": usb_c, "usb_a": usb_a, "lightning": lightning, "total": total}


def _contains_any(value, terms: Iterable[str]) -> bool:
    text = "" if pd.isna(value) else str(value).lower()
    return any(term.lower() in text for term in terms)


def _count_bundle_items(value, item_terms: Iterable[str]) -> int:
    text = "" if pd.isna(value) else str(value).lower()
    total = 0
    for term in item_terms:
        escaped = re.escape(term.lower())
        for match in re.finditer(rf"(\d+)\s*(?:x|\*|\s+)?\s*{escaped}s?\b", text):
            total += int(match.group(1))
        if re.search(rf"\b{escaped}s?\b", text) and total == 0:
            total += 1
    return total


def estimate_bundle_set_count(row) -> int:
    product_type = row.get("Product Type Group", "")
    if product_type != "Charger + Cable Bundle":
        return 1
    text = " ".join(
        str(row.get(column, "") or "")
        for column in ["Pack", "Bundle", "Product Name", "Connect Type/Ports"]
    )
    chargers = _count_bundle_items(text, ["charger", "adapter"])
    cables = _count_bundle_items(text, ["cable", "cord"])
    if chargers and cables:
        return max(1, min(chargers, cables))
    if _contains_any(text, ["bundle", "kit", "charger + cable", "charger and cable"]):
        return 1
    return 1


def compute_product_value(row) -> float | None:
    power = row.get("Max Output Power Num")
    product_type = row.get("Product Type Group", "")
    ports = parse_port_counts(row.get("Connect Type/Ports", ""))
    tech = row.get("Charging Tech", "")
    fast = 3 if row.get("Fast Charging Group") == "Yes" else 0

    if product_type == "Cable":
        length = row.get("Cable Length Num")
        if (pd.isna(length) or length is None) and (pd.isna(power) or power is None):
            return None
        length_base = 0 if pd.isna(length) or length is None else float(length) * 100
        power_score = 0 if pd.isna(power) or power is None else float(power)
        connector_score = 4 if _contains_any(row.get("Connect Type/Ports", ""), ["usb-c to usb-c"]) else 2
        tech_score = 0
        tech_score += 3 if _contains_any(tech, ["usb-if", "thunderbolt", "mfi"]) else 0
        tech_score += 2 if _contains_any(tech, ["braided", "usb 3", "usb 4"]) else 0
        return length_base + power_score + connector_score + tech_score + fast

    if pd.isna(power) or power is None:
        return None

    base = float(power) * 10

    if product_type == "Charger":
        tech_score = 0
        tech_score += 4 if _contains_any(tech, ["gan"]) else 0
        tech_score += 3 if _contains_any(tech, ["pd", "pps", "power delivery"]) else 0
        tech_score += 2 if _contains_any(tech, ["foldable", "qc"]) else 0
        port_score = ports["total"] * 2 + ports["usb_c"] * 2
        return base + port_score + tech_score + fast

    if product_type == "Charger + Cable Bundle":
        set_count = row.get("Bundle Set Count", 1)
        if pd.isna(set_count) or not set_count:
            set_count = 1
        connector_score = min(ports["total"], 4) * 2 + ports["usb_c"] * 2
        tech_score = 0
        tech_score += 3 if _contains_any(tech, ["gan", "pd", "pps", "usb-if", "braided"]) else 0
        return base + float(set_count) * 18 + connector_score + tech_score + fast

    return base + fast


def clean_chart_df(df, columns):
    chart_df = df[[column for column in columns if column in df.columns]].copy()
    for column in chart_df.columns:
        if column not in NUMERIC_CHART_FIELDS:
            chart_df[column] = chart_df[column].fillna("").astype(str)
    return chart_df


def prepare_data(raw: pd.DataFrame):
    df = normalize_columns(raw)
    df["Channel"] = df["Channel"].fillna("").astype(str).str.strip()
    df.loc[df["Channel"] == "", "Channel"] = "Unknown"
    df["Channel Group"] = df["Channel"]
    df["Product Type Group"] = df["Product Type"].apply(normalize_product_type)
    df["Brand Group"] = df["Brand"].apply(normalize_brand)
    df["Pickup Group"] = df["Pickup or Not"].apply(normalize_pickup)
    df["Fast Charging Group"] = df["Fast Charging"].apply(normalize_yes_no)
    df["Price Num"] = df["Price"].apply(parse_number)
    df["Was Price Num"] = df["Was Price"].apply(parse_number)
    df["Max Output Power Num"] = df["Max Output Power"].apply(parse_number)
    df["Cable Length Num"] = df["Cable Length"].apply(parse_cable_length)
    df["Power Group"] = df["Max Output Power Num"].apply(lambda value: f"{int(value)}W" if pd.notna(value) else "N/A")
    df["Pack Group"] = df["Pack"].fillna("N/A").astype(str).str.strip()
    df.loc[df["Pack Group"] == "", "Pack Group"] = "N/A"
    df["Charging Tech Group"] = df["Charging Tech"].fillna("N/A").astype(str).str.strip()
    df.loc[df["Charging Tech Group"] == "", "Charging Tech Group"] = "N/A"
    df["Image Source"] = df["Image URL"].fillna("").astype(str).str.strip()
    df["Bundle Set Count"] = df.apply(estimate_bundle_set_count, axis=1)
    df["Product Value"] = df.apply(compute_product_value, axis=1)
    df["Discounted"] = df.apply(is_discounted, axis=1)

    date_cols = tracking_date_columns(df)
    latest_tracking_date = date_cols[-1][1] if date_cols else CURRENT_DATE
    df["Shelf Events"] = df.apply(lambda row: status_events(row, date_cols), axis=1)
    df["Current Shelf Status"] = df["Shelf Events"].apply(lambda events: status_on_date(events, latest_tracking_date))
    return df, date_cols, latest_tracking_date


def read_product_workbook(path_or_file):
    try:
        return pd.read_excel(path_or_file, sheet_name="Product Data")
    except ValueError:
        return pd.read_excel(path_or_file)


def load_data(uploaded_file=None, sheet_csv_url=""):
    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(".xlsx"):
            raw = read_product_workbook(uploaded_file)
        else:
            raw = pd.read_csv(uploaded_file)
    elif sheet_csv_url:
        raw = pd.read_csv(sheet_csv_url)
    else:
        raw = pd.read_csv(BASE_DIR / "data/product_data_sample.csv")
    return prepare_data(raw)


def latest_add_activity(channel_df, date_cols):
    for column, event_date in reversed(date_cols):
        mask = channel_df[column].fillna("").astype(str).str.lower().str.contains("add")
        if mask.any():
            return column, event_date, channel_df.loc[mask].copy()
    return None, None, channel_df.iloc[0:0].copy()


def group_long_tail_counts(series, top_n=10):
    counts = series.value_counts()
    if len(counts) <= top_n:
        return counts.rename_axis("Brand").reset_index(name="Available SKUs")
    head = counts.head(top_n)
    others = pd.Series({"Others": counts.iloc[top_n:].sum()})
    grouped = pd.concat([head, others])
    return grouped.rename_axis("Brand").reset_index(name="Available SKUs")


def build_snapshot(filtered_df, date_cols, latest_tracking_date):
    channel_df = filtered_df.copy()
    channel_df["Snapshot Status"] = channel_df["Shelf Events"].apply(lambda events: status_on_date(events, latest_tracking_date))
    available = channel_df[channel_df["Snapshot Status"] == "available"].copy()
    total_skus = len(channel_df)
    available_skus = len(available)
    unavailable_skus = total_skus - available_skus
    pickup_skus = int((available["Pickup Group"] == "Pickup").sum())
    pickup_coverage = pickup_skus / available_skus if available_skus else 0

    brand_counts = group_long_tail_counts(available["Brand Group"], top_n=10) if not available.empty else pd.DataFrame(columns=["Brand", "Available SKUs"])
    major_brands = list(available["Brand Group"].value_counts().head(8).index)
    available["Major Brand"] = available["Brand Group"].where(available["Brand Group"].isin(major_brands), "Others")
    pickup_df = (
        available.groupby(["Major Brand", "Pickup Group"]).size().reset_index(name="SKUs")
        if not available.empty
        else pd.DataFrame(columns=["Major Brand", "Pickup Group", "SKUs"])
    )
    discount_df = (
        available.groupby("Brand Group")
        .agg(**{"Available SKUs": ("Brand Group", "size"), "Discounted SKUs": ("Discounted", "sum")})
        .reset_index()
        .rename(columns={"Brand Group": "Brand"})
    )
    if not discount_df.empty:
        discount_df["Discount Rate"] = discount_df["Discounted SKUs"] / discount_df["Available SKUs"]
        discount_df = discount_df.sort_values(["Discounted SKUs", "Available SKUs"], ascending=False).head(10)

    _, add_date, new_rows = latest_add_activity(channel_df, date_cols)
    if not new_rows.empty:
        new_table = (
            new_rows.groupby("Brand Group")
            .agg(
                **{
                    "New SKUs": ("Brand Group", "size"),
                    "Products": ("Product Name", lambda values: ", ".join([str(v) for v in values if str(v).strip()][:5])),
                }
            )
            .reset_index()
            .rename(columns={"Brand Group": "Brand"})
            .sort_values(["New SKUs", "Brand"], ascending=[False, True])
        )
    else:
        new_table = pd.DataFrame(columns=["Brand", "New SKUs", "Products"])

    leaders = available["Brand Group"].value_counts().head(3)
    leader_text = ", ".join(f"{brand} ({count})" for brand, count in leaders.items()) if not leaders.empty else "No available SKUs"
    pickup_text = "pickup-driven" if pickup_coverage >= 0.5 else "online-driven"
    discount_leaders = discount_df[discount_df["Discounted SKUs"] > 0].head(3)
    discount_text = ", ".join(f"{row['Brand']} ({int(row['Discounted SKUs'])})" for _, row in discount_leaders.iterrows()) or "No clear discount signal"
    insights = [
        f"Brand leadership: {leader_text} lead the available shelf by SKU count.",
        f"Fulfillment mix: this shelf is {pickup_text}, with {pickup_coverage:.0%} pickup coverage among available SKUs.",
        f"Commercial signal: price drops are strongest at {discount_text}.",
    ]

    quality_notes = []
    for column in ["Product Type", "Price", "Image URL", "Link", "Pickup or Not", "Connect Type/Ports", "Max Output Power"]:
        missing = int(channel_df[column].fillna("").astype(str).str.strip().eq("").sum())
        if missing:
            quality_notes.append(f"{missing} SKU(s) are missing {column}.")
    duplicate_links = int(channel_df[channel_df["Link"].fillna("").astype(str).str.strip() != ""].duplicated(["Link"]).sum())
    if duplicate_links:
        quality_notes.append(f"{duplicate_links} duplicate product link(s) detected.")

    return {
        "available": available,
        "total_skus": total_skus,
        "available_skus": available_skus,
        "unavailable_skus": unavailable_skus,
        "pickup_skus": pickup_skus,
        "pickup_coverage": pickup_coverage,
        "brand_counts": brand_counts,
        "pickup_df": pickup_df,
        "discount_df": discount_df,
        "new_table": new_table,
        "new_date": add_date,
        "insights": insights,
        "quality_note": " ".join(quality_notes) if quality_notes else "No major data quality issues detected.",
    }


def _sorted_options(series):
    values = [str(value) for value in series.dropna().unique() if str(value).strip()]
    return sorted(values, key=lambda item: (item == "N/A", item.lower()))


def _power_options(df):
    powers = sorted(df["Max Output Power Num"].dropna().unique())
    options = [f"{int(power)}W" for power in powers]
    if df["Max Output Power Num"].isna().any():
        options.append("N/A")
    return options


def format_power_range(df):
    values = df["Max Output Power Num"].dropna()
    if values.empty:
        return "N/A"
    return f"{int(values.min())}-{int(values.max())}W"


def _lazy_streamlit():
    import streamlit as st

    return st


def _lazy_altair():
    import altair as alt

    return alt


def render_value_matrix(df, date_cols):
    st = _lazy_streamlit()
    alt = _lazy_altair()

    st.sidebar.header("Controls")
    available_types = product_type_options(df)
    selected_type = st.sidebar.radio("Product Type", available_types, index=0, horizontal=False)
    type_df = df[df["Product Type Group"] == selected_type].copy()

    all_dates = [item[1] for item in date_cols]
    min_date = min(all_dates) if all_dates else date(2026, 1, 1)
    max_date = max(max(all_dates), CURRENT_DATE) if all_dates else CURRENT_DATE
    query_date = st.sidebar.date_input("Query Date", max_date, min_value=min_date, max_value=max_date)
    if isinstance(query_date, tuple):
        query_date = query_date[0]

    type_df["Availability on Query Date"] = type_df["Shelf Events"].apply(lambda events: status_on_date(events, query_date))
    logic = VALUE_LOGIC.get(selected_type, {"axis": "Product Value", "text": ""})

    title_col, mode_col = st.columns([3, 1])
    with title_col:
        st.title("Product Value Matrix")
        st.caption(logic["text"])
    with mode_col:
        display_mode = st.radio("Point Display", ["Product Image", "Brand Color"], horizontal=True)

    channels = st.sidebar.multiselect("Channel", _sorted_options(type_df["Channel Group"]), default=_sorted_options(type_df["Channel Group"]))
    brands = st.sidebar.multiselect("Brand", _sorted_options(type_df["Brand Group"]), default=_sorted_options(type_df["Brand Group"]))
    pickup = st.sidebar.multiselect("Pickup or Not", _sorted_options(type_df["Pickup Group"]), default=_sorted_options(type_df["Pickup Group"]))
    availability = st.sidebar.multiselect("Availability on Query Date", ["available", "unavailable"], default=["available", "unavailable"])
    pack = st.sidebar.multiselect("Pack", _sorted_options(type_df["Pack Group"]), default=_sorted_options(type_df["Pack Group"]))
    fast = st.sidebar.multiselect("Fast Charging", _sorted_options(type_df["Fast Charging Group"]), default=_sorted_options(type_df["Fast Charging Group"]))
    power = st.sidebar.multiselect("Max Output Power", _power_options(type_df), default=_power_options(type_df))
    tech = st.sidebar.multiselect("Charging Tech", _sorted_options(type_df["Charging Tech Group"]), default=_sorted_options(type_df["Charging Tech Group"]))

    mask = (
        type_df["Channel Group"].isin(channels)
        & type_df["Brand Group"].isin(brands)
        & type_df["Pickup Group"].isin(pickup)
        & type_df["Availability on Query Date"].isin(availability)
        & type_df["Pack Group"].isin(pack)
        & type_df["Fast Charging Group"].isin(fast)
        & type_df["Power Group"].isin(power)
        & type_df["Charging Tech Group"].isin(tech)
    )
    plot_df = type_df.loc[mask & type_df["Price Num"].notna() & type_df["Product Value"].notna()].copy()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Shown Products", f"{len(plot_df):,}")
    col2.metric("Available on Query Date", f"{plot_df['Availability on Query Date'].eq('available').sum():,}")
    col3.metric("Median Price", "N/A" if plot_df.empty else f"${plot_df['Price Num'].median():,.2f}")
    col4.metric(
        "Max Output Power Range",
        "N/A" if plot_df.empty else format_power_range(plot_df),
    )

    chart_columns = list(dict.fromkeys(["Price Num", "Product Value", "Image Source", "Link", "Brand Group", *DISPLAY_FIELDS]))
    chart_df = clean_chart_df(plot_df, chart_columns)
    tooltip = [alt.Tooltip(f"{field}:N", title=field) for field in DISPLAY_FIELDS if field in chart_df.columns]
    x_axis = alt.X("Price Num:Q", title="Price ($)", scale=alt.Scale(zero=False))
    y_axis = alt.Y("Product Value:Q", title=logic["axis"], scale=alt.Scale(zero=False))

    if chart_df.empty:
        st.warning("No products match the current filters.")
        return

    brand_domain = sorted(type_df["Brand Group"].dropna().astype(str).unique())
    brand_range = [BRAND_COLOR_PALETTE[index % len(BRAND_COLOR_PALETTE)] for index, _ in enumerate(brand_domain)]

    if display_mode == "Product Image":
        image_df = chart_df[chart_df["Image Source"].astype(str).str.strip() != ""]
        fallback_df = chart_df[chart_df["Image Source"].astype(str).str.strip() == ""]
        layers = []
        if not image_df.empty:
            layers.append(
                alt.Chart(image_df)
                .mark_image(width=46, height=46)
                .encode(x=x_axis, y=y_axis, url="Image Source:N", href="Link:N", tooltip=tooltip)
            )
        if not fallback_df.empty:
            layers.append(
                alt.Chart(fallback_df)
                .mark_circle(size=170, opacity=0.92, stroke="#ffffff", strokeWidth=1.5)
                .encode(
                    x=x_axis,
                    y=y_axis,
                    color=alt.Color("Brand Group:N", title="Brand", scale=alt.Scale(domain=brand_domain, range=brand_range)),
                    href="Link:N",
                    tooltip=tooltip,
                )
            )
        chart = alt.layer(*layers).properties(height=720).interactive()
    else:
        base_chart = alt.Chart(chart_df).encode(x=x_axis, y=y_axis)
        point_chart = base_chart.mark_circle(size=170, opacity=0.92, stroke="#ffffff", strokeWidth=1.5).encode(
            color=alt.Color("Brand Group:N", title="Brand", scale=alt.Scale(domain=brand_domain, range=brand_range)),
            href="Link:N",
            tooltip=tooltip,
        )
        label_chart = base_chart.mark_text(
            align="center",
            baseline="top",
            dy=12,
            fontSize=10,
            fontWeight="normal",
            color="#1f2933",
            opacity=0.46,
        ).encode(text="Brand Group:N")
        chart = (point_chart + label_chart).properties(height=720).interactive()

    st.altair_chart(chart, use_container_width=True)


def render_shelf_snapshot(df, date_cols, latest_tracking_date):
    st = _lazy_streamlit()
    alt = _lazy_altair()

    st.title("Shelf Snapshot")
    channels = _sorted_options(df["Channel Group"])
    selected_channel = st.selectbox("Channel", channels)
    selected_type = st.radio("Product Type", product_type_options(df), index=0, horizontal=True)
    filtered = df[(df["Channel Group"] == selected_channel) & (df["Product Type Group"] == selected_type)].copy()
    snapshot = build_snapshot(filtered, date_cols, latest_tracking_date)

    st.subheader("Insight Summary")
    insight_cols = st.columns(3)
    for col, insight in zip(insight_cols, snapshot["insights"]):
        col.info(insight)

    kpi_cols = st.columns(6)
    kpi_cols[0].metric("Total SKUs", f"{snapshot['total_skus']:,}")
    kpi_cols[1].metric("Available SKUs", f"{snapshot['available_skus']:,}")
    kpi_cols[2].metric("Pickup SKUs", f"{snapshot['pickup_skus']:,}")
    kpi_cols[3].metric("Pickup Coverage", f"{snapshot['pickup_coverage']:.1%}")
    kpi_cols[4].metric("Unavailable SKUs", f"{snapshot['unavailable_skus']:,}")
    kpi_cols[5].metric("Latest Tracking Date", latest_tracking_date.isoformat())

    st.subheader("Brand Shelf Presence")
    brand_chart_df = snapshot["brand_counts"]
    if brand_chart_df.empty:
        st.warning("No available SKUs for this channel and product type.")
    else:
        chart = (
            alt.Chart(brand_chart_df)
            .mark_bar(color="#2563EB")
            .encode(
                x=alt.X("Available SKUs:Q", title="Available SKUs"),
                y=alt.Y("Brand:N", sort="-x", title="Brand"),
                tooltip=["Brand:N", "Available SKUs:Q"],
            )
            .properties(height=max(300, len(brand_chart_df) * 34))
        )
        st.altair_chart(chart, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Pickup Coverage")
        pickup_df = snapshot["pickup_df"]
        if pickup_df.empty:
            st.caption("No pickup data available.")
        else:
            pickup_chart = (
                alt.Chart(pickup_df)
                .mark_bar()
                .encode(
                    x=alt.X("sum(SKUs):Q", title="SKUs"),
                    y=alt.Y("Major Brand:N", sort="-x", title="Brand"),
                    color=alt.Color("Pickup Group:N", scale=alt.Scale(range=["#0F766E", "#F59E0B", "#667085"])),
                    tooltip=["Major Brand:N", "Pickup Group:N", "SKUs:Q"],
                )
                .properties(height=330)
            )
            st.altair_chart(pickup_chart, use_container_width=True)

    with col2:
        st.subheader("Price Drop Signal")
        discount_df = snapshot["discount_df"]
        if discount_df.empty or not (discount_df["Discounted SKUs"] > 0).any():
            st.caption("No discounted SKUs detected.")
        else:
            discount_chart = (
                alt.Chart(discount_df)
                .mark_bar(color="#DC2626")
                .encode(
                    x=alt.X("Discounted SKUs:Q", title="Discounted SKUs"),
                    y=alt.Y("Brand:N", sort="-x", title="Brand"),
                    tooltip=[
                        "Brand:N",
                        "Available SKUs:Q",
                        "Discounted SKUs:Q",
                        alt.Tooltip("Discount Rate:Q", format=".0%"),
                    ],
                )
                .properties(height=330)
            )
            st.altair_chart(discount_chart, use_container_width=True)

    st.subheader("New Entrants")
    if snapshot["new_table"].empty:
        st.caption("No new brands or products detected.")
    else:
        if snapshot["new_date"]:
            st.caption(f"Most recent add activity: {snapshot['new_date'].isoformat()}")
        st.dataframe(snapshot["new_table"], use_container_width=True, hide_index=True)

    st.caption(f"Data quality note: {snapshot['quality_note']}")


def main():
    st = _lazy_streamlit()
    st.set_page_config(page_title="Charger Cable Bundle Dashboard", layout="wide")

    sheet_url = ""
    try:
        sheet_url = st.secrets.get("GOOGLE_SHEET_CSV_URL", "")
    except Exception:
        sheet_url = os.getenv("GOOGLE_SHEET_CSV_URL", "")

    page = st.sidebar.radio("Page", ["Product Value Matrix", "Shelf Snapshot"])
    uploaded = st.sidebar.file_uploader("Data File", type=["csv", "xlsx"])
    if st.sidebar.button("Refresh data"):
        st.cache_data.clear()

    cached_load = st.cache_data(ttl=600)(load_data)
    df, date_cols, latest_tracking_date = cached_load(uploaded, sheet_url)

    if page == "Product Value Matrix":
        render_value_matrix(df, date_cols)
    else:
        render_shelf_snapshot(df, date_cols, latest_tracking_date)


if __name__ == "__main__":
    main()
