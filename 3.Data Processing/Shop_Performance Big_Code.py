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