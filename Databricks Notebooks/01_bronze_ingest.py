# COMMAND ----------
# 📔 NOTEBOOK: 01_bronze_ingest
# 🎯 GOAL: The "Ingestion" Layer.
# We take the raw, messy CSV file from the outside world and save it into our system (Delta Lake).
# Does it clean the data? NO. (That's the next step)

from pyspark.sql.functions import current_timestamp, input_file_name
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, DateType

# 1. SETUP: Where is the file?
# We assume the file is sitting in the "FileStore" (like an S3 bucket).
source_path = "dbfs:/FileStore/tables/sales_data.csv"
bronze_table_path = "dbfs:/mnt/delta/bronze_sales"
bronze_table_name = "bronze_sales"

# 2. DEFINITION: What do the columns look like?
# We tell Spark exactly what to expect so it doesn't guess wrong.
schema = StructType([
    StructField("order_id", StringType(), True),
    StructField("date", DateType(), True),
    StructField("customer_id", IntegerType(), True),
    StructField("category", StringType(), True),
    StructField("product", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("status", StringType(), True)
])

# 3. READ: Load the CSV
print("Reading CSV data...")
df = (spark.read
      .format("csv")
      .option("header", "true")
      .schema(schema)
      .load(source_path))

# 4. ENRICH: Add "Metadata" (Extra Info)
# We add a timestamp so we know EXACTLY when this data arrived.
print("Adding ingestion metadata...")
df_bronze = df.withColumn("ingestion_timestamp", current_timestamp()) \
              .withColumn("source_file", input_file_name())

# 5. WRITE: Save as "Bronze"
# This creates a permanent table we can query later.
print(f"Writing to {bronze_table_name}...")
(df_bronze.write
 .format("delta")
 .mode("overwrite") # Overwrite = Delete old data and replace with new (Simple for demo)
 .saveAsTable(bronze_table_name))

print("✅ Bronze Layer Ingestion Complete.")
display(df_bronze.limit(5))
