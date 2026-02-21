# COMMAND ----------
# 📔 NOTEBOOK: 03_gold_analysis
# 🎯 GOAL: The "Business Insights" Layer (Analysis).
# We take the clean "Silver" data and create Aggregated Reports.
# Examples: "Total Revenue by Category" or "Top 10 Customers".

from pyspark.sql.functions import sum, count, avg, round, desc

# 1. READ: Load the Clean Data
print("Reading Silver table...")
df_silver = spark.read.table("silver_sales")

# 2. ANALYSIS 1: Which Category makes the most money?
# We group by 'Category' and sum up the 'Amount'.
print("Calculating Sales by Category...")
df_gold_category = (df_silver.groupBy("category")
                    .agg(
                        sum("amount").alias("total_revenue"),
                        count("order_id").alias("total_orders"),
                        round(avg("amount"), 2).alias("avg_order_value")
                    )
                    .orderBy(desc("total_revenue")))

# 3. ANALYSIS 2: Who are our best customers?
# We find the top 10 people who spent the most.
print("Calculating Top Customers...")
df_gold_customers = (df_silver.groupBy("customer_id")
                     .agg(sum("amount").alias("lifetime_value"))
                     .orderBy(desc("lifetime_value"))
                     .limit(10))

# 4. WRITE: Save the Reports (Gold Tables)
# Dashboards will read these small, fast tables.
print("Writing Gold tables...")
df_gold_category.write.format("delta").mode("overwrite").saveAsTable("gold_sales_by_category")
df_gold_customers.write.format("delta").mode("overwrite").saveAsTable("gold_top_customers")

# 5. BONUS: Save the full Clean Dataset for the AI
# The AI Agent likes to query this table (`gold_sales_all`) to answer general questions.
print("Writing Full Gold Data for AI...")
df_silver.write.format("delta").mode("overwrite").saveAsTable("gold_sales_all")

print("✅ Gold Layer Analysis Complete.")
display(df_gold_category)
