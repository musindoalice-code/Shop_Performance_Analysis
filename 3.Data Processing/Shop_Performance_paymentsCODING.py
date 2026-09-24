# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
#imports pandas and reads each CSV into its own table (called a DataFrame).
import pandas as pd
import numpy as np



# COMMAND ----------

 # Data Injestion
Payments=spark.table("shop_performance.shop_performance_data.shop_payments")
Payments=Payments.toPandas()
display(Payments)



# COMMAND ----------

 #shows rows and columns
print("Shape (rows, columns):", Payments.shape)



# COMMAND ----------

 #shows each column's data type and whether it has missing values
Payments.info()



# COMMAND ----------

# previews the first 5 rows
Payments.head()

Payments.describe()



# COMMAND ----------

 # .isnull().sum()- counts how many blank/missing cells are in each column, for each table.
print(Payments.isnull().sum())

# COMMAND ----------

#Count how many payments succeeded, failed, or are pending.
status_counts = Payments['PaymentStatus'].value_counts()
print(status_counts)


# COMMAND ----------

# 2. Calculate the total value (sum) for each payment status
# Compute order values by joining Payments with Orders and Products
Orders = spark.table("shop_performance.shop_performance_data.shop_orders").toPandas()
Products = spark.table("shop_performance.shop_performance_data.shop_products").toPandas()

order_values = Orders.merge(Products[['ProductID', 'UnitPrice']], on='ProductID', how='left')
order_values['amount'] = order_values['Quantity'] * order_values['UnitPrice'] * (1 - order_values['Discount'])

Payments_with_amount = Payments.merge(order_values[['OrderID', 'amount']], on='OrderID', how='inner')
status_totals = Payments_with_amount.groupby('PaymentStatus')['amount'].sum().reset_index()

# 3. Rename columns for clarity and format the currency output
status_totals.columns = ['Payment Status', 'Total Value']
status_totals['Total Value'] = status_totals['Total Value'].map('${:,.2f}'.format)

# 4. Display the analysis results
print("=== Payment Status Financial Analysis ===")
print(status_totals.to_string(index=False))