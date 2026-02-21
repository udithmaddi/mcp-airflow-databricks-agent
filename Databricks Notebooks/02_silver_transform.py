# COMMAND ----------
# 📔 NOTEBOOK: 02_silver_transform
# 🎯 GOAL: The "Cleanup" Layer.
# We take the raw "Bronze" data and fix it.
# We remove bad orders (Cancelled/Returned) and make sure numbers are positive.

from pyspark.sql.functions import col, current_timestamp

# 1. READ: Load the Raw Data
print("Reading Bronze table...")
df_bronze = spark.read.table("bronze_sales")

# 2. TRANSFORM: Apply Business Rules
# Rule A: Keep only "COMPLETED" or "PENDING" orders. Eliminate the rest.
# Rule B: Ensure money is positive (No negative sales).
print("Applying transformations...")

df_silver = df_bronze.filter(
    (col("status").isin(["COMPLETED", "PENDING"])) & 
    (col("amount") > 0)
)

# 3. CLEAN: Drop useless columns
# We don't need to know the original filename anymore.
df_silver = df_silver.drop("source_file")

# 4. ENRICH: Add Timestamp
# Mark when we finished cleaning this data.
df_silver = df_silver.withColumn("processing_timestamp", current_timestamp())

# 5. WRITE: Save as "Silver"
# This is our CLEAN dataset, ready for analysis.
silver_table_name = "silver_sales"
print(f"Writing to {silver_table_name}...")

(df_silver.write
 .format("delta")
 .mode("overwrite")
 .saveAsTable(silver_table_name))

print("✅ Silver Layer Transformation Complete.")
print(f"Rows kept: {df_silver.count()}") # Show how many survived the filter
display(df_silver.limit(5))
