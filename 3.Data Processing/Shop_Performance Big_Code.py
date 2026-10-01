# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# DBTITLE 1,Documentation — Issues Found & Corrections
# MAGIC %md
# MAGIC # Shop Performance — Data Cleaning Pipeline
# MAGIC
# MAGIC ## Documentation: Issues Found & Corrections Made
# MAGIC
# MAGIC ### 1. Compute Environment
# MAGIC - **Issue**: Notebook was attached to a Serverless SQL warehouse, which only supports SQL cells. Python cells failed with `Unsupported cell during execution`.
# MAGIC - **Fix**: Switched compute to **Serverless CPU**, which supports Python/pandas execution.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 2. Logging Mechanism (Cell 2)
# MAGIC - **Issue**: `log = []` and `def note(msg)` accumulated cleaning messages for an audit-trail file (`cleaning_log.txt`). This added unnecessary complexity — every cleaning step had to wrap its `print()` in `note()` and store the message.
# MAGIC - **Original syntax**:
# MAGIC   ```python
# MAGIC   log = []
# MAGIC   def note(msg):
# MAGIC       print(msg)
# MAGIC       log.append(msg)
# MAGIC   ```
# MAGIC - **Corrected**: Removed `log` and `note()`. All `note()` calls replaced with `print()`. The `cleaning_log.txt` file write in Cell 12 was removed.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 3. Duplicate Removal (Cell 3)
# MAGIC - **Issue**: Used intermediate count variables (`dupe_rows`, `dupe_ids`) with `if` conditionals before calling `drop_duplicates()`. Since `drop_duplicates()` is a no-op when no duplicates exist, the conditionals were redundant.
# MAGIC - **Original syntax**:
# MAGIC   ```python
# MAGIC   dupe_rows = orders.duplicated().sum()
# MAGIC   if dupe_rows:
# MAGIC       orders = orders.drop_duplicates()
# MAGIC   dupe_ids = orders["OrderID"].duplicated().sum()
# MAGIC   if dupe_ids:
# MAGIC       orders = orders.drop_duplicates(subset="OrderID", keep="first")
# MAGIC   ```
# MAGIC - **Corrected**:
# MAGIC   ```python
# MAGIC   orders = orders.drop_duplicates()
# MAGIC   orders = orders.drop_duplicates(subset="OrderID", keep="first")
# MAGIC   ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 4. Date Parsing (Cell 4)
# MAGIC - **Issue**: Unused variable `bad_dates = orders["OrderDate"].isna().sum()` was calculated but never used (it was meant for the old `note()` logger). Comment also had a stray dash.
# MAGIC - **Corrected**: Removed `bad_dates`. Kept `errors="coerce"` — the simplest approach for handling invalid dates (unparseable values become `NaT`).
# MAGIC   ```python
# MAGIC   orders["OrderDate"] = pd.to_datetime(orders["OrderDate"], errors="coerce")
# MAGIC   payments["PaymentDate"] = pd.to_datetime(payments["PaymentDate"], errors="coerce")
# MAGIC   ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 5. Quantity Cleanup (Cell 5)
# MAGIC - **Issue**: Multi-step pattern — boolean mask, count variable, `if` conditional, and `.loc[]` assignment — all to set non-positive and NaN quantities to 0.
# MAGIC - **Original syntax**:
# MAGIC   ```python
# MAGIC   bad_qty = (orders["Quantity"] <= 0) | orders["Quantity"].isna()
# MAGIC   n_bad_qty = bad_qty.sum()
# MAGIC   if n_bad_qty:
# MAGIC       orders.loc[bad_qty, "Quantity"] = 0
# MAGIC   ```
# MAGIC - **Corrected** — one-liner using `fillna()` + `clip()`:
# MAGIC   ```python
# MAGIC   orders["Quantity"] = orders["Quantity"].fillna(0).clip(lower=0)
# MAGIC   ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 6. Discount Fill (Cell 6)
# MAGIC - **Issue**: Same redundant pattern — count + `if` check + `fillna()`.
# MAGIC - **Original syntax**:
# MAGIC   ```python
# MAGIC   missing_discount = orders["Discount"].isna().sum()
# MAGIC   if missing_discount:
# MAGIC       orders["Discount"] = orders["Discount"].fillna(0)
# MAGIC   ```
# MAGIC - **Corrected**:
# MAGIC   ```python
# MAGIC   orders["Discount"] = orders["Discount"].fillna(0)
# MAGIC   ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 7. PaymentMethod Fill (Cell 7)
# MAGIC - **Issue**: Intermediate `missing_pm` variable and garbled multi-line comment.
# MAGIC - **Corrected**: Single `n_missing` check for the print message, then unconditional `fillna("Unknown")`.
# MAGIC   ```python
# MAGIC   n_missing = orders["PaymentMethod"].isna().sum()
# MAGIC   if n_missing:
# MAGIC       print(f"orders: {n_missing} blank PaymentMethod filled with 'Unknown'")
# MAGIC   orders["PaymentMethod"] = orders["PaymentMethod"].fillna("Unknown")
# MAGIC   ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 8. City Normalization (Cell 8)
# MAGIC - **Issue**: Unused variables (`n_fixed`, `missing_age`), separate `city_fixes` dict variable, and verbose `if`-conditional pattern.
# MAGIC - **Original syntax**:
# MAGIC   ```python
# MAGIC   city_fixes = {"Mashad": "Mashhad"}
# MAGIC   n_fixed = customers["City"].isin(city_fixes).sum()
# MAGIC   customers["City"] = customers["City"].replace(city_fixes)
# MAGIC   missing_city = customers["City"].isna().sum()
# MAGIC   if missing_city:
# MAGIC       print(f"customers: {missing_city} rows have a blank City — .")
# MAGIC       customers["City"] = customers["City"].fillna("Unknown")
# MAGIC   missing_age = customers["Age"].isna().sum()
# MAGIC   ```
# MAGIC - **Corrected**:
# MAGIC   ```python
# MAGIC   customers["City"] = customers["City"].str.strip().str.title()
# MAGIC   customers["City"] = customers["City"].replace({"Mashad": "Mashhad"})
# MAGIC   n_missing = customers["City"].isna().sum()
# MAGIC   if n_missing:
# MAGIC       print(f"customers: {n_missing} blank City filled with 'Unknown'")
# MAGIC   customers["City"] = customers["City"].fillna("Unknown")
# MAGIC   ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 9. Save Step (Cell 12)
# MAGIC - **Issue**: Wrote `cleaning_log.txt` using the accumulated `log` list. On Serverless compute, local file writes don't persist reliably.
# MAGIC - **Original syntax**:
# MAGIC   ```python
# MAGIC   df.to_csv("cleaned_joined_orders.csv", index=False)
# MAGIC   with open("cleaning_log.txt", "w") as f:
# MAGIC       f.write("\n".join(log))
# MAGIC   note("\nSaved cleaned_joined_orders.csv and cleaning_log.txt")
# MAGIC   ```
# MAGIC - **Corrected**:
# MAGIC   ```python
# MAGIC   df.to_csv("cleaned_joined_orders.csv", index=False)
# MAGIC   print("\nSaved cleaned_joined_orders.csv")
# MAGIC   ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 10. Cleaned Table Export (Cell 13 — New)
# MAGIC - **Added**: New cell that saves the cleaned, joined DataFrame as a Unity Catalog table for export to other platforms (Power BI, Tableau, Excel, etc.).
# MAGIC   ```python
# MAGIC   spark_df_clean = spark.createDataFrame(df_export)
# MAGIC   spark_df_clean.write.mode("overwrite").saveAsTable(
# MAGIC       "shop_performance.shop_performance_data.cleaned_joined_orders"
# MAGIC   )
# MAGIC   ```

# COMMAND ----------

import pandas as pd
import numpy as np
import json

# COMMAND ----------

# STEP 0 — load

customers = spark.table("shop_performance.shop_performance_data.shop_customers").toPandas()
orders = spark.table("shop_performance.shop_performance_data.shop_orders").toPandas()
payments = spark.table("shop_performance.shop_performance_data.shop_payments").toPandas()
products = spark.table("shop_performance.shop_performance_data.shop_products").toPandas()



# COMMAND ----------

# --- orders: remove exact duplicate rows, then deduplicate by OrderID
orders = orders.drop_duplicates()
orders = orders.drop_duplicates(subset="OrderID", keep="first")

# COMMAND ----------

# --- orders: parse dates (invalid values become NaT via errors="coerce")
orders["OrderDate"] = pd.to_datetime(orders["OrderDate"], errors="coerce")
payments["PaymentDate"] = pd.to_datetime(payments["PaymentDate"], errors="coerce")

# COMMAND ----------

# --- orders: set negative/zero/NaN Quantity to 0
orders["Quantity"] = orders["Quantity"].fillna(0).clip(lower=0)

# COMMAND ----------

# --- orders: fill missing Discount with 0
orders["Discount"] = orders["Discount"].fillna(0)

# COMMAND ----------

# --- orders: fill missing PaymentMethod with "Unknown"
n_missing = orders["PaymentMethod"].isna().sum()
if n_missing:
    print(f"orders: {n_missing} blank PaymentMethod filled with 'Unknown'")
orders["PaymentMethod"] = orders["PaymentMethod"].fillna("Unknown")
 

# COMMAND ----------

# --- customers: normalize city spelling/casing, fill blanks with "Unknown"
customers["City"] = customers["City"].str.strip().str.title()
customers["City"] = customers["City"].replace({"Mashad": "Mashhad"})

n_missing = customers["City"].isna().sum()
if n_missing:
    print(f"customers: {n_missing} blank City filled with 'Unknown'")
customers["City"] = customers["City"].fillna("Unknown")

# COMMAND ----------

# combine the tables
# ---------------------------------------------------------------------------
# orders -> products : many-to-one, keep every order line (left join)
df = orders.merge(products, on="ProductID", how="left")
 
# -> customers : many-to-one, left join so orphaned CustomerIDs survive as NaN
df = df.merge(
    customers, 
    on="CustomerID", 
    how="left", suffixes=("", "_cust"))

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

# save the cleaned, joined working file — 
# ---------------------------------------------------------------------------
df.to_csv("cleaned_joined_orders.csv", index=False)
print("\nSaved cleaned_joined_orders.csv")

# COMMAND ----------

# DBTITLE 1,Cleaned Table — View & Export
# Display the cleaned, joined table and save as a Unity Catalog table for export
# ---------------------------------------------------------------------------
df_export = df.copy()
# Convert categorical columns to string for Spark compatibility
for col in df_export.select_dtypes(include=["category"]).columns:
    df_export[col] = df_export[col].astype(str)

spark_df_clean = spark.createDataFrame(df_export)
spark_df_clean.write.mode("overwrite").saveAsTable("shop_performance.shop_performance_data.cleaned_joined_orders")

print("Saved to Unity Catalog table: shop_performance.shop_performance_data.cleaned_joined_orders")
print(f"Rows: {df_export.shape[0]}  |  Columns: {df_export.shape[1]}")
display(spark.table("shop_performance.shop_performance_data.cleaned_joined_orders"))

# COMMAND ----------

# Aggregations for display & visualizations
results = {}

total_revenue = df["RecognisedRevenue"].sum()
aov = total_revenue / counts_as_revenue.sum() if counts_as_revenue.sum() else 0
results["headline"] = {
    "total_revenue": round(total_revenue, 2),
    "total_orders": int(df["OrderID"].nunique()),
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

by_category = (
    df.groupby("Category")
    .agg(Revenue=("RecognisedRevenue", "sum"), Units=("Quantity", "sum"))
    .reset_index()
    .sort_values("Revenue", ascending=False)
)

by_product = (
    df.groupby("ProductName")
    .agg(Revenue=("RecognisedRevenue", "sum"), Units=("Quantity", "sum"))
    .reset_index()
    .sort_values("Revenue", ascending=False)
)

by_city = (
    df.groupby("City")["RecognisedRevenue"]
    .sum()
    .reset_index()
    .sort_values("RecognisedRevenue", ascending=False)
)

by_segment = (
    df.groupby("CustomerSegment")["RecognisedRevenue"]
    .sum()
    .reset_index()
    .sort_values("RecognisedRevenue", ascending=False)
)

results["status_rate_pct"] = (df["Status"].value_counts(normalize=True) * 100).round(1).to_dict()

payment_fail_rate = (
    df.groupby("PaymentMethod")["PaymentStatus"]
    .apply(lambda s: round((s == "Failed").mean() * 100, 1))
    .reset_index(name="FailRatePct")
    .sort_values("FailRatePct", ascending=False)
)

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

# DBTITLE 1,Chart 1: Monthly Revenue Trend
# Chart 1: Monthly Revenue Trend (line chart)
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 5))
plt.plot(monthly["YearMonth"], monthly["RecognisedRevenue"], marker="o", color="blue")
plt.title("Monthly Recognised Revenue")
plt.ylabel("Revenue ($)")
plt.xticks(rotation=90, fontsize=7)
plt.tight_layout()
plt.show()

# COMMAND ----------

# DBTITLE 1,Chart 2: Revenue by Category
# Chart 2: Revenue by Product Category (horizontal bar)
plt.figure(figsize=(8, 5))
cat = by_category.sort_values("Revenue")
plt.barh(cat["Category"], cat["Revenue"], color="green")
plt.title("Revenue by Product Category")
plt.xlabel("Revenue ($)")
plt.tight_layout()
plt.show()

# COMMAND ----------

# DBTITLE 1,Chart 3: Top 10 Products by Revenue
# Chart 3: Top 10 Products by Revenue (horizontal bar)
plt.figure(figsize=(8, 5))
top10 = by_product.head(10).sort_values("Revenue")
plt.barh(top10["ProductName"], top10["Revenue"], color="teal")
plt.title("Top 10 Products by Revenue")
plt.xlabel("Revenue ($)")
plt.tight_layout()
plt.show()

# COMMAND ----------

# DBTITLE 1,Chart 4: Revenue by City
# Chart 4: Revenue by City (horizontal bar, excludes Unknown)
plt.figure(figsize=(8, 5))
city = by_city[by_city["City"] != "Unknown"].sort_values("RecognisedRevenue")
plt.barh(city["City"], city["RecognisedRevenue"], color="orange")
plt.title("Revenue by City")
plt.xlabel("Revenue ($)")
plt.tight_layout()
plt.show()

# COMMAND ----------

# DBTITLE 1,Chart 5: Customer Segment Pie
# Chart 5: Revenue Share by Customer Segment (pie chart)
plt.figure(figsize=(7, 7))
seg = by_segment[by_segment["CustomerSegment"] != "Unknown"]
plt.pie(seg["RecognisedRevenue"], labels=seg["CustomerSegment"], autopct="%1.1f%%", startangle=90)
plt.title("Revenue Share by Customer Segment")
plt.tight_layout()
plt.show()

# COMMAND ----------

# DBTITLE 1,Chart 6: Order Status Pie
# Chart 6: Order Status Distribution (pie chart)
plt.figure(figsize=(7, 7))
status_data = results["status_rate_pct"]
plt.pie(list(status_data.values()), labels=list(status_data.keys()), autopct="%1.1f%%", startangle=90)
plt.title("Order Status Distribution")
plt.tight_layout()
plt.show()

# COMMAND ----------

# DBTITLE 1,Chart 7: Payment Failure Rate
# Chart 7: Payment Failure Rate by Method (horizontal bar)
plt.figure(figsize=(8, 5))
pf = payment_fail_rate.sort_values("FailRatePct")
plt.barh(pf["PaymentMethod"], pf["FailRatePct"], color="red")
plt.title("Payment Failure Rate by Method")
plt.xlabel("Failure Rate (%)")
plt.tight_layout()
plt.show()

# COMMAND ----------

# DBTITLE 1,Chart 8: Discount Band
# Chart 8: Avg Order Value by Discount Band (bar chart)
plt.figure(figsize=(7, 5))
plt.bar(discount_vs_aov["DiscountBand"].astype(str), discount_vs_aov["RecognisedRevenue"], color="purple")
plt.title("Avg Order Value by Discount Band")
plt.ylabel("Avg Order Value ($)")
plt.xlabel("Discount Band")
plt.tight_layout()
plt.show()

# COMMAND ----------

# DBTITLE 1,Chart 9: Units vs Revenue
# Chart 9: Revenue vs Units Sold by Category (dual-axis bar)
# twin axis needed because Revenue ($) and Units have very different scales
import numpy as np

fig, ax1 = plt.subplots(figsize=(9, 5))
cat = by_category.sort_values("Revenue", ascending=False)
x = np.arange(len(cat))
w = 0.35

ax1.bar(x - w/2, cat["Revenue"], w, label="Revenue", color="blue")
ax1.set_ylabel("Revenue ($)")
ax2 = ax1.twinx()  # second y-axis for Units
ax2.bar(x + w/2, cat["Units"], w, label="Units", color="orange")
ax2.set_ylabel("Units Sold")
ax1.set_xticks(x)
ax1.set_xticklabels(cat["Category"], rotation=30, ha="right", fontsize=9)
ax1.set_title("Revenue vs Units Sold by Category")
fig.legend(loc="upper right")
plt.tight_layout()
plt.show()

# COMMAND ----------

# DBTITLE 1,Chart 10: Headline KPIs
# Chart 10: Headline KPI Summary (text output)
h = results["headline"]
print("=" * 45)
print("       SHOP PERFORMANCE — HEADLINE KPIs")
print("=" * 45)
print(f"  Total Revenue:        ${h['total_revenue']:,.2f}")
print(f"  Total Orders:         {h['total_orders']:,}")
print(f"  Recognised Orders:    {h['recognised_orders']:,}")
print(f"  Avg Order Value:      ${h['average_order_value']:.2f}")
print("=" * 45)
print(f"  Period:  Jan 2024 – Sep 2026")
print(f"  Categories: {by_category.shape[0]}")
print(f"  Cities:    {by_city[by_city['City'] != 'Unknown'].shape[0]}")
print(f"  Products:  {by_product.shape[0]}")