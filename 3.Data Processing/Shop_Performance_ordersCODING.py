# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Importing Libraries
# import pandas as pd
# import numpy as np

# COMMAND ----------

# DBTITLE 1,Data Injestion
#Loading table into pandas dataframe
Orders=spark.table("shop_performance.shop_performance_data.shop_orders")
Orders=Orders.toPandas()
display(Orders)

# COMMAND ----------

# DBTITLE 1,Checking the Data
#shows rows and columns
print("Shape (rows, columns):", Orders.shape)

#shows each column's data type and whether it has missing values
Orders.info()

# previews the first 5 rows
Orders.head()



# COMMAND ----------

# DBTITLE 1,Missing Values
##cleaning the data-

# .isnull().sum()- counts how many blank/missing cells are in each column 
print(Orders.isnull().sum())

# COMMAND ----------

# DBTITLE 1,Duplicate OrderIDs
# .duplicated()-Checking for Duplicate where it counts how many times each OrderID appears. 

duplicate_orders = Orders[Orders.duplicated(subset="OrderID", keep=False)]
print("Number of duplicate OrderID rows:", duplicate_orders.shape[0])
duplicate_orders.sort_values("OrderID")

#Checking the actual duplicate rows side by side, sorted by OrderID, so we see different data under the same ID
dupes = Orders[Orders.duplicated(subset="OrderID", keep=False)].sort_values("OrderID")
dupes.head(20)

# COMMAND ----------

import pandas as pd

# Compute order amounts by joining with Products for UnitPrice
Products = spark.table("shop_performance.shop_performance_data.shop_products").toPandas()
Orders = Orders.merge(Products[['ProductID', 'UnitPrice']], on='ProductID', how='left')
Orders['amount'] = Orders['Quantity'] * Orders['UnitPrice'] * (1 - Orders['Discount'])


duplicate_orders = Orders[Orders.duplicated(subset="OrderID", keep=False)]
print("Number of duplicate OrderID rows:", duplicate_orders.shape[0])

# CHECK VALUE AMOUNTS ---

# Option A: Total value of ALL rows that have duplicate IDs 
total_flagged_value = duplicate_orders['amount'].sum() 
print(f"Total value of all flagged duplicate rows: ${total_flagged_value:,.2f}")

# Checking how much money would be lost or double-counted if these are pure system errors)
excess_dupes = Orders[Orders.duplicated(subset="OrderID", keep='first')]
total_excess_value = excess_dupes['amount'].sum()
print(f"Total value of excess/double-counted rows: ${total_excess_value:,.2f}")

# inspection 
dupes = duplicate_orders.sort_values("OrderID")
dupes.head(20)


# COMMAND ----------

# DBTITLE 1,Numerical Summary
# .describe() :Checking Numerical Values- shows min, max, average and other stats for numeric columns. .
print("\n--- Order quantity & discount ---")
print(Orders[["Quantity", "Discount"]].describe())

# COMMAND ----------

# DBTITLE 1,Negative Quantity Check
#Checking the negative quantity rows-filters to only the rows where Quantity is negative
negative_qty = Orders[Orders["Quantity"] < 0]
print("Count of negative quantity rows:", negative_qty.shape[0])
negative_qty

# COMMAND ----------

import pandas as pd

# 1. Load your orders table
# Replace 'Orders' with your actual DataFrame variable name if already loaded
# df = pd.read_csv('orders.csv') 
df = Orders.copy()

# 2. Convert the date column to datetime format
# Replace 'OrderDate' with your actual date column name (e.g., 'date', 'created_at')
df['OrderDate'] = pd.to_datetime(df['OrderDate'])

# 3. Create a Year-Month period column for clean grouping
df['Month'] = df['OrderDate'].dt.to_period('M')

# 4. Group by Month and aggregate Order Count and Total Revenue
monthly_analysis = df.groupby('Month').agg(
    Total_Orders=('OrderID', 'nunique'),  # Counts unique orders per month
    Total_Revenue=('amount', 'sum')       # Sums up the revenue per month
).reset_index()

# 5. Formating the output for easy reading
monthly_analysis['Total_Revenue_Formatted'] = monthly_analysis['Total_Revenue'].map('${:,.2f}'.format)

# 6. Displaying the monthly breakdown
print("=== Month-by-Month Order & Revenue Summary ===")
print(monthly_analysis[['Month', 'Total_Orders', 'Total_Revenue_Formatted']].to_string(index=False))


# COMMAND ----------

# 3. Creating a Year-Quarter period column 
df['Quarter'] = df['OrderDate'].dt.to_period('Q')

# 4. Group by Quarter and aggregate Order Count and Total Revenue
quarterly_analysis = df.groupby('Quarter').agg(
    Total_Orders=('OrderID', 'nunique'),  # Counts unique orders per quarter
    Total_Revenue=('amount', 'sum')       # Sums up the revenue per quarter
).reset_index()

# 5. Formating the financial output for easy reading
quarterly_analysis['Total_Revenue_Formatted'] = quarterly_analysis['Total_Revenue'].map('${:,.2f}'.format)

# 6. Displaying the quarterly breakdown
print("=== Quarter-by-Quarter Order & Revenue Summary ===")
print(quarterly_analysis[['Quarter', 'Total_Orders', 'Total_Revenue_Formatted']].to_string(index=False))

# COMMAND ----------

# DBTITLE 1,Orphan Products Check
print("\n--- Duplicate OrderIDs ---")
dupes = Orders[Orders.duplicated(subset="OrderID", keep=False)]
print("Count:", dupes.shape[0])

Products = spark.table("shop_performance.shop_performance_data.shop_products").toPandas()

print("\n--- Orphan products (ProductID not in products.csv) ---")
orphan_products = Orders[~Orders["ProductID"].isin(Products["ProductID"])]
print("Count:", orphan_products.shape[0])

# COMMAND ----------

# DBTITLE 1,Status & PaymentMethod Values
print("\n--- Quantity & Discount sanity check ---")
print(Orders[["Quantity", "Discount"]].describe())

print("\n--- Status values ---")
print(Orders["Status"].value_counts())

print("\n--- PaymentMethod values ---")
print(Orders["PaymentMethod"].value_counts())

# COMMAND ----------

# checking to see if the missing values are in the same rows
missing_values = Orders[Orders["OrderDate"].isnull() & Orders["Quantity"].isnull() & Orders["Discount"].isnull() & Orders["PaymentMethod"].isnull()]

display(f"Number of rows with all four values missing: {len(missing_values)}")
if not missing_values.empty:
    display(missing_values)

# COMMAND ----------

# DBTITLE 1,Visualizations Header
# MAGIC %md
# MAGIC # 📊 Shop Performance Visualizations & Insights
# MAGIC
# MAGIC This section presents key visualizations that answer critical business questions about revenue trends, order success rates, payment method performance, top products, and the impact of discounts on order outcomes.

# COMMAND ----------

# DBTITLE 1,Monthly Revenue Trend
import matplotlib.pyplot as plt
import pandas as pd

# --- Q: How is the business performing over time? ---
df_trend = Orders.copy()
df_trend['OrderDate'] = pd.to_datetime(df_trend['OrderDate'])
df_trend['Month'] = df_trend['OrderDate'].dt.to_period('M').astype(str)

monthly = df_trend.groupby('Month').agg(
    Total_Revenue=('amount', 'sum'),
    Order_Count=('OrderID', 'nunique')
).reset_index()

fig, ax1 = plt.subplots(figsize=(12, 5))

color1 = '#2E86AB'
ax1.bar(monthly['Month'], monthly['Total_Revenue'], color=color1, alpha=0.7, label='Revenue')
ax1.set_xlabel('Month')
ax1.set_ylabel('Revenue ($)', color=color1)
ax1.tick_params(axis='y', labelcolor=color1)
ax1.tick_params(axis='x', rotation=45)

ax2 = ax1.twinx()
color2 = '#A23B72'
ax2.plot(monthly['Month'], monthly['Order_Count'], color=color2, marker='o', linewidth=2, label='Order Count')
ax2.set_ylabel('Order Count', color=color2)
ax2.tick_params(axis='y', labelcolor=color2)

plt.title('Monthly Revenue & Order Count Trend', fontsize=14, fontweight='bold')
fig.tight_layout()
plt.show()

# --- Insights ---
total_rev = monthly['Total_Revenue'].sum()
avg_monthly_rev = monthly['Total_Revenue'].mean()
best_month = monthly.loc[monthly['Total_Revenue'].idxmax()]
worst_month = monthly.loc[monthly['Total_Revenue'].idxmin()]
print(f"Total Revenue: ${total_rev:,.2f}")
print(f"Average Monthly Revenue: ${avg_monthly_rev:,.2f}")
print(f"Best Month: {best_month['Month']} (${best_month['Total_Revenue']:,.2f}, {best_month['Order_Count']} orders)")
print(f"Worst Month: {worst_month['Month']} (${worst_month['Total_Revenue']:,.2f}, {worst_month['Order_Count']} orders)")

# COMMAND ----------

# DBTITLE 1,Order Status Distribution
# --- Q: What percentage of orders succeed vs fail? What is the revenue impact? ---
status_counts = Orders['Status'].value_counts()
status_revenue = Orders.groupby('Status')['amount'].sum().sort_values(ascending=False)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

colors_status = ['#2ECC71', '#E74C3C', '#F39C12', '#3498DB']
ax1.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%', colors=colors_status[:len(status_counts)], startangle=90)
ax1.set_title('Order Status Distribution (by Count)', fontsize=12, fontweight='bold')

bars = ax2.bar(status_revenue.index, status_revenue.values, color=colors_status[:len(status_revenue)])
ax2.set_title('Revenue by Order Status', fontsize=12, fontweight='bold')
ax2.set_ylabel('Revenue ($)')
for bar, val in zip(bars, status_revenue.values):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100, f'${val:,.0f}', ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.show()

# --- Insights ---
completion_rate = (status_counts.get('Completed', 0) / status_counts.sum()) * 100
lost_revenue = status_revenue.get('Cancelled', 0) + status_revenue.get('Returned', 0)
print(f"Completion Rate: {completion_rate:.1f}%")
print(f"Revenue Lost to Returns & Cancellations: ${lost_revenue:,.2f}")
print(f"Returned Orders: {status_counts.get('Returned', 0)} ({status_counts.get('Returned', 0)/status_counts.sum()*100:.1f}%)")
print(f"Cancelled Orders: {status_counts.get('Cancelled', 0)} ({status_counts.get('Cancelled', 0)/status_counts.sum()*100:.1f}%)")

# COMMAND ----------

# DBTITLE 1,Payment Method Analysis
# --- Q: Which payment methods drive the most revenue and highest order values? ---
payment_stats = Orders.groupby('PaymentMethod').agg(
    Total_Revenue=('amount', 'sum'),
    Order_Count=('OrderID', 'nunique'),
    Avg_Order_Value=('amount', 'mean')
).sort_values('Total_Revenue', ascending=False).reset_index()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

bars = ax1.bar(payment_stats['PaymentMethod'], payment_stats['Total_Revenue'], color='#3498DB')
ax1.set_title('Total Revenue by Payment Method', fontsize=12, fontweight='bold')
ax1.set_ylabel('Revenue ($)')
for bar, val in zip(bars, payment_stats['Total_Revenue']):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200, f'${val:,.0f}', ha='center', va='bottom', fontsize=10)

bars2 = ax2.bar(payment_stats['PaymentMethod'], payment_stats['Avg_Order_Value'], color='#9B59B6')
ax2.set_title('Average Order Value by Payment Method', fontsize=12, fontweight='bold')
ax2.set_ylabel('Avg Order Value ($)')
for bar, val in zip(bars2, payment_stats['Avg_Order_Value']):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, f'${val:,.2f}', ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.show()

# --- Insights ---
top_payment = payment_stats.iloc[0]
best_aov = payment_stats.loc[payment_stats['Avg_Order_Value'].idxmax()]
print(f"Top Payment Method: {top_payment['PaymentMethod']} (${top_payment['Total_Revenue']:,.2f} revenue, {top_payment['Order_Count']} orders)")
print(f"Highest Avg Order Value: {best_aov['PaymentMethod']} (${best_aov['Avg_Order_Value']:,.2f})")
print("\nFull breakdown:")
for _, row in payment_stats.iterrows():
    print(f"  {row['PaymentMethod']}: ${row['Total_Revenue']:,.2f} | {row['Order_Count']} orders | AOV ${row['Avg_Order_Value']:,.2f}")

# COMMAND ----------

# DBTITLE 1,Top Products by Revenue
# --- Q: What are the best-selling products by revenue? ---
orders_with_names = Orders.merge(Products[['ProductID', 'ProductName', 'Category']], on='ProductID', how='left')

top_products = orders_with_names.groupby(['ProductID', 'ProductName', 'Category']).agg(
    Total_Revenue=('amount', 'sum'),
    Order_Count=('OrderID', 'nunique'),
    Avg_Quantity=('Quantity', 'mean')
).sort_values('Total_Revenue', ascending=False).head(10).reset_index()

fig, ax = plt.subplots(figsize=(12, 6))
y_labels = [f"{row['ProductName']} ({row['Category']})" for _, row in top_products.iterrows()]
bars = ax.barh(y_labels, top_products['Total_Revenue'], color='#E67E22')
ax.set_title('Top 10 Products by Revenue', fontsize=14, fontweight='bold')
ax.set_xlabel('Revenue ($)')
ax.invert_yaxis()
for bar, val in zip(bars, top_products['Total_Revenue']):
    ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2, f'${val:,.2f}', va='center', fontsize=9)

plt.tight_layout()
plt.show()

# --- Insights ---
top10_rev = top_products['Total_Revenue'].sum()
total_all_rev = orders_with_names['amount'].sum()
print(f"Top Product: {top_products.iloc[0]['ProductName']} (${top_products.iloc[0]['Total_Revenue']:,.2f})")
print(f"Top 10 products contribute ${top10_rev:,.2f} ({top10_rev/total_all_rev*100:.1f}% of total revenue)")
print(f"Total revenue across all products: ${total_all_rev:,.2f}")

# COMMAND ----------

# DBTITLE 1,Discount Impact Analysis
# --- Q: Do higher discounts lead to more returns and cancellations? ---
Orders_disc = Orders.copy()
Orders_disc['Discount_Bin'] = pd.cut(Orders_disc['Discount'],
    bins=[-0.001, 0, 0.05, 0.15, 0.5],
    labels=['No Discount', 'Low (0-5%)', 'Medium (5-15%)', 'High (15%+)'])

discount_status = Orders_disc.groupby(['Discount_Bin', 'Status'], observed=False).size().unstack(fill_value=0)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

colors_disc = ['#2ECC71', '#E74C3C', '#F39C12', '#3498DB']
discount_status.plot(kind='bar', stacked=True, ax=ax1, color=colors_disc[:len(discount_status.columns)])
ax1.set_title('Order Status by Discount Level', fontsize=12, fontweight='bold')
ax1.set_xlabel('Discount Level')
ax1.set_ylabel('Order Count')
ax1.legend(title='Status')
ax1.tick_params(axis='x', rotation=0)

total_per_bin = discount_status.sum(axis=1)
fail_rate = ((discount_status.get('Returned', 0) + discount_status.get('Cancelled', 0)) / total_per_bin * 100)
ax2.bar(fail_rate.index.astype(str), fail_rate.values, color='#C0392B')
ax2.set_title('Return/Cancel Rate by Discount Level', fontsize=12, fontweight='bold')
ax2.set_xlabel('Discount Level')
ax2.set_ylabel('Failure Rate (%)')
for i, val in enumerate(fail_rate.values):
    ax2.text(i, val + 0.3, f'{val:.1f}%', ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.show()

# --- Insights ---
print("Return/Cancel Rate by Discount Level:")
for bin_name, rate in fail_rate.items():
    print(f"  {bin_name}: {rate:.1f}%")
highest_fail = fail_rate.idxmax()
lowest_fail = fail_rate.idxmin()
print(f"\nHighest failure rate: {highest_fail} ({fail_rate.max():.1f}%)")
print(f"Lowest failure rate: {lowest_fail} ({fail_rate.min():.1f}%)")

# COMMAND ----------

# DBTITLE 1,Key Insights Summary
# MAGIC %md
# MAGIC # 🔑 Key Insights Summary
# MAGIC
# MAGIC Based on the visualizations above:
# MAGIC
# MAGIC 1. **Revenue Trend**: The monthly revenue chart reveals the overall growth trajectory and seasonal patterns, helping identify peak and trough periods for resource planning.
# MAGIC 2. **Order Success**: The completion rate shows what percentage of orders succeed. Returns and cancellations represent direct revenue loss that can be reduced through better inventory and customer service.
# MAGIC 3. **Payment Methods**: Understanding which payment channels drive the most revenue and highest average order values helps prioritize payment infrastructure investments.
# MAGIC 4. **Top Products**: The top 10 products share of total revenue reveals product concentration risk and highlights best-sellers for promotional focus.
# MAGIC 5. **Discount Impact**: The relationship between discount levels and return/cancellation rates guides pricing strategy. If higher discounts correlate with more failures, aggressive discounting may be counterproductive.