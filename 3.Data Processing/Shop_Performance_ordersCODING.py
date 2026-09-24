# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
#imports pandas and reads each CSV into its own table (called a DataFrame).
# import pandas as pd
# import numpy as np

# Data Injestion
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

#inspect the duplicate OrderIDs : shows the actual duplicate rows side by side, sorted by OrderID, so we see  different data under the same ID
dupes = Orders[Orders.duplicated(subset="OrderID", keep=False)].sort_values("OrderID")
dupes.head(20)

# COMMAND ----------

import pandas as pd

# Compute order amounts by joining with Products for UnitPrice
Products = spark.table("shop_performance.shop_performance_data.shop_products").toPandas()
Orders = Orders.merge(Products[['ProductID', 'UnitPrice']], on='ProductID', how='left')
Orders['amount'] = Orders['Quantity'] * Orders['UnitPrice'] * (1 - Orders['Discount'])

# Your existing code setup
duplicate_orders = Orders[Orders.duplicated(subset="OrderID", keep=False)]
print("Number of duplicate OrderID rows:", duplicate_orders.shape[0])

# --- NEW CODE TO CHECK VALUE AMOUNTS ---

# Option A: Total value of ALL rows that have duplicate IDs 
# (Good for seeing the total volume of transactions flagged with issues)
total_flagged_value = duplicate_orders['amount'].sum() 
print(f"Total value of all flagged duplicate rows: ${total_flagged_value:,.2f}")

# Option B: Value of just the EXCESS/REDUNDANT rows 
# (Good for seeing how much money would be lost or double-counted if these are pure system errors)
excess_dupes = Orders[Orders.duplicated(subset="OrderID", keep='first')]
total_excess_value = excess_dupes['amount'].sum()
print(f"Total value of excess/double-counted rows: ${total_excess_value:,.2f}")

# --- Proceed with your existing inspection ---
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
# Replace 'OrderID' and 'amount' with your actual column names
monthly_analysis = df.groupby('Month').agg(
    Total_Orders=('OrderID', 'nunique'),  # Counts unique orders per month
    Total_Revenue=('amount', 'sum')       # Sums up the revenue per month
).reset_index()

# 5. Format the output for easy reading
monthly_analysis['Total_Revenue_Formatted'] = monthly_analysis['Total_Revenue'].map('${:,.2f}'.format)

# 6. Display the monthly breakdown
print("=== Month-by-Month Order & Revenue Summary ===")
print(monthly_analysis[['Month', 'Total_Orders', 'Total_Revenue_Formatted']].to_string(index=False))


# COMMAND ----------

# 3. Create a Year-Quarter period column (e.g., 2026Q1)
df['Quarter'] = df['OrderDate'].dt.to_period('Q')

# 4. Group by Quarter and aggregate Order Count and Total Revenue
# Replace 'OrderID' and 'amount' with your actual column names
quarterly_analysis = df.groupby('Quarter').agg(
    Total_Orders=('OrderID', 'nunique'),  # Counts unique orders per quarter
    Total_Revenue=('amount', 'sum')       # Sums up the revenue per quarter
).reset_index()

# 5. Format the financial output for easy reading
quarterly_analysis['Total_Revenue_Formatted'] = quarterly_analysis['Total_Revenue'].map('${:,.2f}'.format)

# 6. Display the quarterly breakdown
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