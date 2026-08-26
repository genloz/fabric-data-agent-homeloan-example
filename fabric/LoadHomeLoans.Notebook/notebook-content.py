# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "78deb54a-9f5c-4859-828e-d0ea0fc7c2a5",
# META       "default_lakehouse_name": "HomeLoansLakehouse",
# META       "default_lakehouse_workspace_id": "",
# META       "known_lakehouses": [
# META         {
# META           "id": "78deb54a-9f5c-4859-828e-d0ea0fc7c2a5"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

source_csv_url = "https://raw.githubusercontent.com/genloz/fabric-data-agent-homeloan-example/refs/heads/main/data/home_loans.csv"
table_name = "home_loans"
write_mode = "overwrite"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import json
from urllib.parse import urlparse

import notebookutils
import requests
from pyspark.sql import functions as F
from pyspark.sql.types import (
    BooleanType,
    DateType,
    DecimalType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

parsed_url = urlparse(source_csv_url)
if parsed_url.scheme != "https" or parsed_url.hostname != "raw.githubusercontent.com":
    raise ValueError(
        "source_csv_url must be an HTTPS raw.githubusercontent.com URL for this demo."
    )
if not table_name.replace("_", "").isalnum():
    raise ValueError("table_name may only contain letters, numbers, and underscores.")
if write_mode not in {"overwrite", "append"}:
    raise ValueError("write_mode must be overwrite or append.")

response = requests.get(source_csv_url, timeout=60)
response.raise_for_status()

# Use the default attached lakehouse (HomeLoansLakehouse) via relative paths
raw_file_path = "Files/home_loans/home_loans.csv"
table_path = f"Tables/dbo/{table_name}"

notebookutils.fs.put(raw_file_path, response.text, overwrite=True)

schema = StructType(
    [
        StructField("loan_id", StringType(), False),
        StructField("application_date", DateType(), False),
        StructField("settlement_date", DateType(), True),
        StructField("state", StringType(), False),
        StructField("postcode_region", StringType(), False),
        StructField("property_type", StringType(), False),
        StructField("occupancy_type", StringType(), False),
        StructField("loan_purpose", StringType(), False),
        StructField("first_home_buyer", BooleanType(), False),
        StructField("channel", StringType(), False),
        StructField("loan_amount", DecimalType(18, 2), False),
        StructField("property_value", DecimalType(18, 2), False),
        StructField("deposit_amount", DecimalType(18, 2), False),
        StructField("lvr_pct", DecimalType(6, 2), False),
        StructField("interest_rate_pct", DecimalType(6, 3), False),
        StructField("term_years", IntegerType(), False),
        StructField("repayment_type", StringType(), False),
        StructField("monthly_repayment", DecimalType(18, 2), False),
        StructField("application_status", StringType(), False),
        StructField("days_to_decision", IntegerType(), False),
        StructField("credit_score_band", StringType(), False),
        StructField("debt_to_income_ratio", DecimalType(6, 2), False),
        StructField("arrears_days", IntegerType(), False),
        StructField("hardship_flag", BooleanType(), False),
        StructField("annual_household_income", DecimalType(18, 2), False),
        StructField("current_balance", DecimalType(18, 2), False),
    ]
)

loans = (
    spark.read.option("header", True)
    .option("dateFormat", "yyyy-MM-dd")
    .schema(schema)
    .csv(raw_file_path)
    .withColumn("application_month", F.trunc("application_date", "month"))
    .withColumn("settlement_month", F.trunc("settlement_date", "month"))
    .withColumn("is_high_lvr", F.col("lvr_pct") >= F.lit(80))
    .withColumn("is_in_arrears", F.col("arrears_days") > F.lit(0))
    .withColumn(
        "delinquency_band",
        F.when(F.col("arrears_days") == 0, F.lit("Current"))
        .when(F.col("arrears_days") < 30, F.lit("1-29 days"))
        .when(F.col("arrears_days") < 60, F.lit("30-59 days"))
        .otherwise(F.lit("60+ days")),
    )
)

row_count = loans.count()
distinct_loan_count = loans.select("loan_id").distinct().count()
invalid_count = loans.filter(
    (F.col("loan_amount") <= 0)
    | (F.col("property_value") <= 0)
    | (F.col("lvr_pct") <= 0)
    | (F.col("lvr_pct") > 100)
    | (~F.col("state").isin("NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"))
    | (
        ~F.col("application_status").isin(
            "Active", "Approved", "Declined", "Withdrawn"
        )
    )
).count()

if row_count == 0:
    raise RuntimeError("The source CSV contains no rows.")
if distinct_loan_count != row_count:
    raise RuntimeError("loan_id must be unique.")
if invalid_count:
    raise RuntimeError(f"Data quality checks failed for {invalid_count} rows.")

loans.write.format("delta").mode(write_mode).option(
    "overwriteSchema", write_mode == "overwrite"
).save(table_path)

active = loans.filter(F.col("application_status") == "Active")
summary = active.agg(
    F.count("*").alias("active_loans"),
    F.round(F.sum("current_balance"), 2).alias("current_portfolio_balance"),
    F.round(F.avg("lvr_pct"), 2).alias("average_lvr_pct"),
).first()

result = {
    "table": table_name,
    "rows_loaded": row_count,
    "active_loans": summary["active_loans"],
    "current_portfolio_balance": str(summary["current_portfolio_balance"]),
    "average_lvr_pct": str(summary["average_lvr_pct"]),
}
print(json.dumps(result, indent=2))
notebookutils.notebook.exit(json.dumps(result))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
