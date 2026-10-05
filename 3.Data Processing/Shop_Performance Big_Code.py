# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
import pandas as pd
import numpy as np
import json

# COMMAND ----------

# DBTITLE 1,Cell 3 — Load Cleaned Data from Unity Catalog
# STEP 0 — load the cleaned, joined table from Unity Catalog
# (Cleaning & joining already done and saved by Cells 4–14; skip straight to analysis)

df = spark.table("shop_performance.shop_performance_data.cleaned_joined_orders").toPandas()

# Re-create the revenue-recognition mask used by downstream analysis cells
counts_as_revenue = (df["Status"] == "Completed") & (df["PaymentStatus"] == "Paid")

print(f"Loaded cleaned_joined_orders: {df.shape[0]} rows, {df.shape[1]} columns")
display(df.head(5))



# COMMAND ----------

# DBTITLE 1,Check 1 — Duplicate OrderIDs
# Check 1: Duplicate OrderIDs (should be 0)
dupes = df["OrderID"].duplicated().sum()
print(f"Duplicate OrderIDs: {dupes}  (expected: 0)")

# COMMAND ----------

# DBTITLE 1,Check 2 — NaT OrderDates
# Check 2: Invalid dates coerced to NaT (rows preserved)
nat_dates = df["OrderDate"].isna().sum()
print(f"NaT OrderDates: {nat_dates}  (invalid dates -> NaT, rows kept)")

# COMMAND ----------

# DBTITLE 1,Check 3 — Quantity Cleanup
# Check 3: Bad quantities set to 0 (rows preserved)
zero_qty = (df["Quantity"] == 0).sum()
neg_qty = (df["Quantity"] < 0).sum()
print(f"Quantity = 0: {zero_qty}  |  Negative: {neg_qty}  (bad qty -> 0, rows kept)")

# COMMAND ----------

# DBTITLE 1,Check 4 — Discount Fill
# Check 4: Missing Discount filled with 0
missing_disc = df["Discount"].isna().sum()
print(f"Missing Discount (NaN): {missing_disc}  (expected: 0)")

# COMMAND ----------

# DBTITLE 1,Check 5 — PaymentMethod Fill
# Check 5: Missing PaymentMethod filled with "Unknown"
unknown_pm = (df["PaymentMethod"] == "Unknown").sum()
nan_pm = df["PaymentMethod"].isna().sum()
print(f"PaymentMethod='Unknown': {unknown_pm}  |  NaN: {nan_pm}  (NaN expected: 0)")

# COMMAND ----------

# DBTITLE 1,Check 6 — City Normalization
# Check 6: City spelling normalized (Mashad -> Mashhad)
old = (df["City"] == "Mashad").sum()
fixed = (df["City"] == "Mashhad").sum()
print(f"City 'Mashad' (old): {old}  (expected: 0)")
print(f"City 'Mashhad' (corrected): {fixed}")

# COMMAND ----------

# DBTITLE 1,Check 7 — City Unknown Fill
# Check 7: Missing City filled with "Unknown"
unknown_city = (df["City"] == "Unknown").sum()
nan_city = df["City"].isna().sum()
print(f"City='Unknown': {unknown_city}  |  NaN: {nan_city}  (NaN expected: 0)")

# COMMAND ----------

# DBTITLE 1,Check 8 — Revenue Formula
# Check 8: Revenue formula (Quantity * UnitPrice * (1 - Discount))
sample = df[["Quantity", "UnitPrice", "Discount", "Revenue"]].head(5).copy()
sample["CalcRevenue"] = sample["Quantity"] * sample["UnitPrice"] * (1 - sample["Discount"])
sample["Match"] = np.isclose(sample["Revenue"], sample["CalcRevenue"])
display(sample)

# COMMAND ----------

# DBTITLE 1,Check 9 — RecognisedRevenue Logic
# Check 9: RecognisedRevenue only for Completed + Paid orders
non_qual = df[~counts_as_revenue]["RecognisedRevenue"].sum()
print(f"RecognisedRevenue when NOT Completed+Paid: ${non_qual:,.2f}  (expected: $0.00)")

# COMMAND ----------

# DBTITLE 1,Check 10 — Derived Columns
# Check 10: Derived columns present
for col in ["Revenue", "RecognisedRevenue", "Year", "Month", "YearMonth"]:
    status = "present" if col in df.columns else "MISSING"
    print(f"  {col:20s}: {status}")

# COMMAND ----------

# DBTITLE 1,Load Raw Tables + Deduplicate Orders
# Load raw tables for the cleaning pipeline (Cells 13–23)
orders = spark.table("shop_performance.shop_performance_data.shop_orders").toPandas()
payments = spark.table("shop_performance.shop_performance_data.shop_payments").toPandas()
customers = spark.table("shop_performance.shop_performance_data.shop_customers").toPandas()
products = spark.table("shop_performance.shop_performance_data.shop_products").toPandas()

# --- orders: remove exact duplicate rows, then deduplicate by OrderID
before = len(orders)
orders = orders.drop_duplicates()
orders = orders.drop_duplicates(subset="OrderID", keep="first")
after = len(orders)
print(f"Duplicate rows removed: {before - after}  ({before} -> {after})")

# COMMAND ----------

# --- orders: parse dates (invalid values become NaT via errors="coerce")
orders["OrderDate"] = pd.to_datetime(orders["OrderDate"], errors="coerce")
payments["PaymentDate"] = pd.to_datetime(payments["PaymentDate"], errors="coerce")

print(f"OrderDate:  {orders['OrderDate'].isna().sum()} invalid dates -> NaT")
print(f"PaymentDate: {payments['PaymentDate'].isna().sum()} invalid dates -> NaT")

# COMMAND ----------

# --- orders: set negative/zero/NaN Quantity to 0
orders["Quantity"] = orders["Quantity"].fillna(0).clip(lower=0)

print(f"Quantity: {(orders['Quantity'] == 0).sum()} rows set to 0")

# COMMAND ----------

# --- orders: fill missing Discount with 0
orders["Discount"] = orders["Discount"].fillna(0)

print(f"Discount: {orders['Discount'].isna().sum()} remaining NaN (filled with 0)")

# COMMAND ----------

# --- orders: fill missing PaymentMethod with "Unknown"
n_missing = orders["PaymentMethod"].isna().sum()
print(f"PaymentMethod: {n_missing} blank values filled with 'Unknown'")
orders["PaymentMethod"] = orders["PaymentMethod"].fillna("Unknown")

# COMMAND ----------

# --- customers: normalize city spelling/casing, fill blanks with "Unknown"
customers["City"] = customers["City"].str.strip().str.title()
customers["City"] = customers["City"].replace({"Mashad": "Mashhad"})
mashad_fixed = (customers["City"] == "Mashhad").sum()

n_missing = customers["City"].isna().sum()
print(f"City: 'Mashad' -> 'Mashhad' ({mashad_fixed} rows)")
print(f"City: {n_missing} blank values filled with 'Unknown'")
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

# DBTITLE 1,Final Cleaned Table — Export to Excel
# Final cleaned table — ready for Excel export
# ---------------------------------------------------------------------------
# Right-click the table below and choose Download as CSV to open in Excel.
# Or use the to_excel line at the bottom to save directly as .xlsx.

print(f"Final cleaned table: {df.shape[0]:,} rows × {df.shape[1]} columns")
display(df)

# To save as Excel file directly, uncomment the two lines below:
# df.to_excel("cleaned_joined_orders.xlsx", index=False)
# print("Saved cleaned_joined_orders.xlsx")

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