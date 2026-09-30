# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
import pandas as pd
import numpy as np
import json

# COMMAND ----------

# STEP 0 — load

customers = spark.table("shop_performance.shop_performance_data.shop_customers").toPandas()
orders = spark.table("shop_performance.shop_performance_data.shop_orders").toPandas()
payments = spark.table("shop_performance.shop_performance_data.shop_payments").toPandas()
products = spark.table("shop_performance.shop_performance_data.shop_products").toPandas()
 
log = []
 
 
def note(msg):
    print(msg)
    log.append(msg)
 


# COMMAND ----------

# --- orders: exact duplicate rows -----------------------------------------
dupe_rows = orders.duplicated().sum()
if dupe_rows:
    orders = orders.drop_duplicates()
  
 
# duplicate OrderID with DIFFERENT content would be a harder conflict — check
dupe_ids = orders["OrderID"].duplicated().sum()
if dupe_ids:
  
    orders = orders.drop_duplicates(subset="OrderID", keep="first")

# COMMAND ----------

# --- orders: dates -are kept in the table but excluded from month-by-month trend charts, since they can't be placed on a timeline
orders["OrderDate"] = pd.to_datetime(orders["OrderDate"], errors="coerce")
bad_dates = orders["OrderDate"].isna().sum()
 
payments["PaymentDate"] = pd.to_datetime(payments["PaymentDate"], errors="coerce")

# COMMAND ----------

# --- orders: negative / zero Quantity 
bad_qty = (orders["Quantity"] <= 0) | orders["Quantity"].isna()
n_bad_qty = bad_qty.sum()
if n_bad_qty:

    orders.loc[bad_qty, "Quantity"] = 0

# COMMAND ----------

# --- orders: missing Discount -filled with 0 (no discount applied
missing_discount = orders["Discount"].isna().sum()

if missing_discount:

    orders["Discount"] = orders["Discount"].fillna(0)

# COMMAND ----------

# --- orders: missing PaymentMethod 
# rows had a blank PaymentMethod — labelled "-f"'Unknown' rather than dropped, so these orders still count"towards revenue and order totals.
missing_pm = orders["PaymentMethod"].isna().sum()
if missing_pm:
    note(f"orders: {missing_pm} ")
    orders["PaymentMethod"] = orders["PaymentMethod"].fillna("Unknown")
 

# COMMAND ----------

# --- customers: inconsistent city spelling/casing # filled with "Unknown' so they still appear in city breakdowns instead of disappearing from a group-by
customers["City"] = customers["City"].str.strip().str.title()
 

city_fixes = {"Mashad": "Mashhad"}
n_fixed = customers["City"].isin(city_fixes).sum()
customers["City"] = customers["City"].replace(city_fixes)
 
missing_city = customers["City"].isna().sum()
if missing_city:
    note(f"customers: {missing_city} rows have a blank City — .")
    customers["City"] = customers["City"].fillna("Unknown")
 
missing_age = customers["Age"].isna().sum()

# COMMAND ----------

# combine the tables
# ---------------------------------------------------------------------------
# orders -> products : many-to-one, keep every order line (left join)
df = orders.merge(products, on="ProductID", how="left")
 
# -> customers : many-to-one, left join so orphaned CustomerIDs survive as NaN
df = df.merge(customers, on="CustomerID", how="left", suffixes=("", "_cust"))
df["City"] = df["City"].fillna("Unknown")
df["CustomerSegment"] = df["CustomerSegment"].fillna("Unknown")
 
# -> payments : one payment attempt per order in this dataset, left join so
#    an order with no payment record yet still appears
df = df.merge(
    payments[["OrderID", "PaymentDate", "PaymentStatus"]],
    on="OrderID",
    how="left",
)
df["PaymentStatus"] = df["PaymentStatus"].fillna("Unknown")

# COMMAND ----------

# Business decision: cancelled/returned orders and failed/refunded payments
# did not result in money the shop keeps, so they are excluded from revenue

df["Revenue"] = df["Quantity"] * df["UnitPrice"] * (1 - df["Discount"])

# COMMAND ----------

counts_as_revenue = (df["Status"] == "Completed") & (df["PaymentStatus"] == "Paid")
df["RecognisedRevenue"] = df["Revenue"].where(counts_as_revenue, 0.0)
df["Year"] = df["OrderDate"].dt.year
df["Month"] = df["OrderDate"].dt.month
df["YearMonth"] = df["OrderDate"].dt.to_period("M").astype(str)

# COMMAND ----------

# save the cleaned, joined working file — this is your audit trail
# ---------------------------------------------------------------------------
df.to_csv("cleaned_joined_orders.csv", index=False)
with open("cleaning_log.txt", "w") as f:
    f.write("\n".join(log))
note("\nSaved cleaned_joined_orders.csv and cleaning_log.txt")

# COMMAND ----------

results = {}
 
total_revenue = df["RecognisedRevenue"].sum()
total_orders = df["OrderID"].nunique()
aov = total_revenue / counts_as_revenue.sum() if counts_as_revenue.sum() else 0
results["headline"] = {
    "total_revenue": round(total_revenue, 2),
    "total_orders": int(total_orders),
    "recognised_orders": int(counts_as_revenue.sum()),
    "average_order_value": round(aov, 2),
}
 
monthly = (
    df.dropna(subset=["YearMonth"])
    .groupby("YearMonth")["RecognisedRevenue"]
    .sum()
    .reset_index()
    .sort_values("YearMonth")
)
results["monthly_revenue"] = monthly.to_dict("records")
 
by_category = (
    df.groupby("Category")
    .agg(Revenue=("RecognisedRevenue", "sum"), Units=("Quantity", "sum"))
    .reset_index()
    .sort_values("Revenue", ascending=False)
)
results["by_category"] = by_category.to_dict("records")
 
by_product = (
    df.groupby("ProductName")
    .agg(Revenue=("RecognisedRevenue", "sum"), Units=("Quantity", "sum"))
    .reset_index()
    .sort_values("Revenue", ascending=False)
)
results["by_product"] = by_product.to_dict("records")
 
by_city = (
    df.groupby("City")["RecognisedRevenue"]
    .sum()
    .reset_index()
    .sort_values("RecognisedRevenue", ascending=False)
)
results["by_city"] = by_city.to_dict("records")
 
by_segment = (
    df.groupby("CustomerSegment")["RecognisedRevenue"]
    .sum()
    .reset_index()
    .sort_values("RecognisedRevenue", ascending=False)
)
results["by_segment"] = by_segment.to_dict("records")
 
status_rate = (df["Status"].value_counts(normalize=True) * 100).round(1)
results["status_rate_pct"] = status_rate.to_dict()
 
payment_fail_rate = (
    df.groupby("PaymentMethod")["PaymentStatus"]
    .apply(lambda s: round((s == "Failed").mean() * 100, 1))
    .reset_index(name="FailRatePct")
    .sort_values("FailRatePct", ascending=False)
)
results["payment_fail_rate"] = payment_fail_rate.to_dict("records")
 
df["DiscountBand"] = pd.cut(
    df["Discount"], bins=[-0.01, 0, 0.1, 0.2, 1], labels=["0%", "1-10%", "11-20%", "21%+"]
)
discount_vs_aov = (
    df[counts_as_revenue]
    .groupby("DiscountBand", observed=True)["RecognisedRevenue"]
    .mean()
    .reset_index()
)

# COMMAND ----------

# Display all final result tables
# ---------------------------------------------------------------------------
print("HEADLINE METRICS")
print(json.dumps(results["headline"], indent=2))

print("\nMONTHLY REVENUE")
display(monthly)

print("\nREVENUE BY CATEGORY")
display(by_category)

print("\nREVENUE BY PRODUCT (Top 10)")
display(by_product.head(10))

print("\nREVENUE BY CITY")
display(by_city)

print("\nREVENUE BY CUSTOMER SEGMENT")
display(by_segment)

print("\nORDER STATUS RATE (%)")
print(json.dumps(results["status_rate_pct"], indent=2))

print("\nPAYMENT FAILURE RATE BY METHOD (%)")
display(payment_fail_rate)

print("\nAVG ORDER VALUE BY DISCOUNT BAND")
display(discount_vs_aov)

# COMMAND ----------

# DBTITLE 1,Visualizations — Shop Performance Dashboard
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

plt.style.use("seaborn-v0_8-whitegrid")
fig = plt.figure(figsize=(22, 28))

# Colour palette
PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
           "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

def money(ax, axis="y"):
    """Format axis tick labels as $K/M."""
    t = ax.yaxis if axis == "y" else ax.xaxis
    t.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"${v/1e6:.1f}M" if v >= 1e6 else f"${v/1e3:.0f}K"
    ))

# ── 1. Monthly Revenue Trend ─────────────────────────────────────────────
ax1 = fig.add_subplot(5, 2, 1)
m = monthly[monthly["YearMonth"] != "NaT"].copy()
ax1.plot(m["YearMonth"], m["RecognisedRevenue"], marker="o", linewidth=2, color=PALETTE[0])
ax1.fill_between(m["YearMonth"], m["RecognisedRevenue"], alpha=0.15, color=PALETTE[0])
ax1.set_title("Monthly Recognised Revenue", fontsize=13, fontweight="bold")
ax1.set_ylabel("Revenue")
money(ax1)
ax1.tick_params(axis="x", rotation=90, labelsize=7)

# ── 2. Revenue by Category (bar) ─────────────────────────────────────────
ax2 = fig.add_subplot(5, 2, 2)
cats = by_category.sort_values("Revenue", ascending=True)
ax2.barh(cats["Category"], cats["Revenue"], color=PALETTE[:len(cats)])
ax2.set_title("Revenue by Product Category", fontsize=13, fontweight="bold")
ax2.set_xlabel("Revenue")
money(ax2, axis="x")
for i, v in enumerate(cats["Revenue"]):
    ax2.text(v + 5000, i, f"${v/1e3:.0f}K", va="center", fontsize=8)

# ── 3. Top 10 Products by Revenue (bar) ───────────────────────────────────
ax3 = fig.add_subplot(5, 2, 3)
top10 = by_product.head(10).sort_values("Revenue", ascending=True)
ax3.barh(top10["ProductName"], top10["Revenue"], color=PALETTE[2])
ax3.set_title("Top 10 Products by Revenue", fontsize=13, fontweight="bold")
ax3.set_xlabel("Revenue")
money(ax3, axis="x")
for i, v in enumerate(top10["Revenue"]):
    ax3.text(v + 2000, i, f"${v/1e3:.0f}K", va="center", fontsize=8)

# ── 4. Revenue by City (bar) ──────────────────────────────────────────────
ax4 = fig.add_subplot(5, 2, 4)
cities = by_city[by_city["City"] != "Unknown"].sort_values("RecognisedRevenue", ascending=True)
ax4.barh(cities["City"], cities["RecognisedRevenue"], color=PALETTE[1])
ax4.set_title("Revenue by City", fontsize=13, fontweight="bold")
ax4.set_xlabel("Revenue")
money(ax4, axis="x")
for i, v in enumerate(cities["RecognisedRevenue"]):
    ax4.text(v + 3000, i, f"${v/1e3:.0f}K", va="center", fontsize=8)

# ── 5. Revenue by Customer Segment (pie) ─────────────────────────────────
ax5 = fig.add_subplot(5, 2, 5)
seg = by_segment[by_segment["CustomerSegment"] != "Unknown"]
ax5.pie(seg["RecognisedRevenue"], labels=seg["CustomerSegment"], autopct="%1.1f%%",
        colors=PALETTE[:len(seg)], startangle=90, textprops={"fontsize": 10})
ax5.set_title("Revenue Share by Customer Segment", fontsize=13, fontweight="bold")

# ── 6. Order Status Distribution (pie) ────────────────────────────────────
ax6 = fig.add_subplot(5, 2, 6)
status_data = results["status_rate_pct"]
labels = list(status_data.keys())
sizes = list(status_data.values())
ax6.pie(sizes, labels=labels, autopct="%1.1f%%", colors=["#2ca02c", "#d62728", "#ff7f0e"],
        startangle=90, textprops={"fontsize": 10})
ax6.set_title("Order Status Distribution", fontsize=13, fontweight="bold")

# ── 7. Payment Failure Rate by Method (bar) ──────────────────────────────
ax7 = fig.add_subplot(5, 2, 7)
pf = payment_fail_rate.sort_values("FailRatePct", ascending=True)
ax7.barh(pf["PaymentMethod"], pf["FailRatePct"], color=PALETTE[3])
ax7.set_title("Payment Failure Rate by Method", fontsize=13, fontweight="bold")
ax7.set_xlabel("Failure Rate (%)")
for i, v in enumerate(pf["FailRatePct"]):
    ax7.text(v + 0.05, i, f"{v}%", va="center", fontsize=9)

# ── 8. Avg Order Value by Discount Band (bar) ────────────────────────────
ax8 = fig.add_subplot(5, 2, 8)
db = discount_vs_aov.copy()
ax8.bar(db["DiscountBand"].astype(str), db["RecognisedRevenue"], color=PALETTE[4])
ax8.set_title("Avg Order Value by Discount Band", fontsize=13, fontweight="bold")
ax8.set_ylabel("Avg Order Value ($)")
ax8.set_xlabel("Discount Band")
for i, v in enumerate(db["RecognisedRevenue"]):
    ax8.text(i, v + 1, f"${v:.2f}", ha="center", fontsize=9)

# ── 9. Category Units vs Revenue (dual bar) ───────────────────────────────
ax9 = fig.add_subplot(5, 2, 9)
cat_sorted = by_category.sort_values("Revenue", ascending=False)
x = np.arange(len(cat_sorted))
w = 0.35
bars1 = ax9.bar(x - w/2, cat_sorted["Revenue"], w, label="Revenue", color=PALETTE[0])
ax9.set_ylabel("Revenue")
money(ax9)
ax9b = ax9.twinx()
bars2 = ax9b.bar(x + w/2, cat_sorted["Units"], w, label="Units Sold", color=PALETTE[1])
ax9b.set_ylabel("Units Sold")
ax9.set_xticks(x)
ax9.set_xticklabels(cat_sorted["Category"], rotation=30, ha="right", fontsize=9)
ax9.set_title("Revenue vs Units Sold by Category", fontsize=13, fontweight="bold")
lines1, labels1 = ax9.get_legend_handles_labels()
lines2, labels2 = ax9b.get_legend_handles_labels()
ax9.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=8)

# ── 10. Headline KPI cards ────────────────────────────────────────────────
ax10 = fig.add_subplot(5, 2, 10)
ax10.axis("off")
h = results["headline"]
kpi_text = (
    f"  SHOP PERFORMANCE — HEADLINE KPIs\n"
    f"{'─' * 42}\n"
    f"  Total Revenue          ${h['total_revenue']:,.2f}\n"
    f"  Total Orders           {h['total_orders']:,}\n"
    f"  Recognised Orders      {h['recognised_orders']:,}\n"
    f"  Avg Order Value        ${h['average_order_value']:.2f}\n"
    f"{'─' * 42}\n"
    f"  Period: Jan 2024 – Sep 2026\n"
    f"  Categories: {by_category.shape[0]}  |  Cities: {by_city[by_city['City']!='Unknown'].shape[0]}\n"
    f"  Products: {by_product.shape[0]}"
)
ax10.text(0.05, 0.95, kpi_text, transform=ax10.transAxes,
          fontsize=12, fontfamily="monospace", verticalalignment="top",
          bbox=dict(boxstyle="round,pad=0.8", facecolor="#f0f0f0", edgecolor="#333"))

fig.suptitle("Shop Performance Dashboard", fontsize=18, fontweight="bold", y=0.998)
fig.tight_layout(rect=[0, 0, 1, 0.99])
plt.show()