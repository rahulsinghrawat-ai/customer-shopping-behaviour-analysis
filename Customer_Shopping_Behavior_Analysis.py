"""
Customer Shopping Behaviour Analysis: data cleaning script

What this script does
    Loads the raw shopping dataset (3,900 purchase records, 18 columns),
    cleans and checks it, saves the cleaned version for the SQL queries and
    the Power BI dashboard, and optionally loads it into PostgreSQL.

Input
    customer_shopping_behavior.csv, in the project folder or in a data folder

Output
    customer_shopping_cleaned.csv, saved in the same folder as the raw file
    (3,900 rows, 19 columns, no missing values)

Run it
    python Customer_Shopping_Behavior_Analysis.py

Requirements
    pandas. SQLAlchemy and psycopg2 are needed only when DB_LOAD is True.

Results on the included data
    - 37 missing Review Rating values filled with the category median
    - promo_code_used dropped, because it is identical to discount_applied
    - 1,028 Young Adult, 986 Middle-aged, 944 Senior, 942 Adult customers

Changes from the original version
    1. Step 1 finds the raw CSV in the project folder or in a data folder, so it works from any folder.
    2. The CSV is read with utf-8-sig, which handles the hidden marker Excel adds.
    3. Step 4 falls back to the overall median if a whole category has no ratings.
    4. Step 6 drops duplicates="drop", which conflicted with the four labels.
    5. Step 7 stops with an error on unknown frequencies instead of printing a warning.
    6. Step 9 stops the script if the data breaks a basic rule.
    7. Step 10 (missing from the original) saves customer_shopping_cleaned.csv.
    8. Step 11 reads the password from PG_PASSWORD instead of the file, and runs only when DB_LOAD is True.
"""

import os
import sys
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

# Paths are built from this file's location, so the script works from any folder.
BASE_DIR = Path(__file__).resolve().parent


def find_raw_file(file_name):
    """Return the path to the raw CSV. Looks in the project folder first, then in a data folder."""
    for folder in (BASE_DIR, BASE_DIR / "data"):
        candidate = folder / file_name
        if candidate.exists():
            return candidate
    sys.exit(f"Could not find {file_name} in {BASE_DIR} or in {BASE_DIR / 'data'}.")


RAW_FILE = find_raw_file("customer_shopping_behavior.csv")

# The cleaned file is saved next to the raw file, so the SQL and Power BI paths stay the same.
CLEANED_FILE = RAW_FILE.parent / "customer_shopping_cleaned.csv"

# Keep this False until your PostgreSQL setup is ready.
# The password is never stored here. It is read from the PG_PASSWORD environment variable.
DB_LOAD = False


# --------------------------------------------------
# STEP 1: Load the dataset
# --------------------------------------------------

# RAW_FILE was found automatically, so the script works from any folder.
# utf-8-sig removes the hidden marker that Excel adds at the start of the file.

df = pd.read_csv(RAW_FILE, encoding="utf-8-sig")

print("\nFirst five records:")
print(df.head())


# --------------------------------------------------
# STEP 2: Understand the dataset
# --------------------------------------------------

# info() tells us about columns, data types and missing values.
print("\nDataset information:")
df.info()

# describe() gives statistical information about the data.
print("\nStatistical summary:")
print(df.describe(include="all"))


# --------------------------------------------------
# STEP 3: Check missing values
# --------------------------------------------------

print("\nMissing values before cleaning:")
print(df.isnull().sum())


# --------------------------------------------------
# STEP 4: Handle missing values
# --------------------------------------------------

# Review Rating contains missing values.
# I fill them using the median rating of the same product category.
# This keeps the replacement relevant to each category.
# If a whole category is missing, I use the overall median instead.

df["Review Rating"] = (
    df.groupby("Category")["Review Rating"]
    .transform(lambda x: x.fillna(x.median()))
)
df["Review Rating"] = df["Review Rating"].fillna(df["Review Rating"].median())

print("\nMissing values after cleaning:")
print(df.isnull().sum())


# --------------------------------------------------
# STEP 5: Standardize column names
# --------------------------------------------------

# I convert column names into lowercase snake_case.
# This makes the column names easier to use in Python and SQL.

df.columns = df.columns.str.strip().str.lower()
df.columns = df.columns.str.replace(" ", "_")

# Remove the currency detail from this column name.
df = df.rename(
    columns={"purchase_amount_(usd)": "purchase_amount"}
)

print("\nUpdated column names:")
print(df.columns.tolist())


# --------------------------------------------------
# STEP 6: Create age groups
# --------------------------------------------------

# I divide customers into four age groups using quartiles.
# qcut creates groups with approximately equal numbers of records.
# These are analytical segments, not official age classifications.
# Because they are quartiles, "Senior" covers the oldest quarter of customers (ages 58 to 70).
# I convert the groups to plain text so they save cleanly to CSV and the database.

labels = ["Young Adult", "Adult", "Middle-aged", "Senior"]

df["age_group"] = pd.qcut(
    df["age"],
    q=4,
    labels=labels
).astype(str)

print("\nAge group distribution:")
print(df["age_group"].value_counts())


# --------------------------------------------------
# STEP 7: Convert purchase frequency into days
# --------------------------------------------------

# I convert purchase frequency into approximate number of days.
# This can help with customer purchase-frequency analysis.

frequency_mapping = {
    "Fortnightly": 14,
    "Weekly": 7,
    "Monthly": 30,
    "Quarterly": 90,
    "Bi-Weekly": 14,
    "Annually": 365,
    "Every 3 Months": 90
}

df["purchase_frequency_days"] = (
    df["frequency_of_purchases"].map(frequency_mapping)
)

# Stop the script if any frequency value was not mapped.
# A silent blank here would cause wrong results later.
unmapped_values = df.loc[
    df["purchase_frequency_days"].isna(),
    "frequency_of_purchases"
].unique()

if len(unmapped_values) > 0:
    raise ValueError(f"Unmapped purchase frequencies: {list(unmapped_values)}")

df["purchase_frequency_days"] = df["purchase_frequency_days"].astype(int)
print("\nAll purchase frequencies were mapped successfully.")


# --------------------------------------------------
# STEP 8: Check discount and promo code columns
# --------------------------------------------------

# I compare both columns to see whether they contain
# exactly the same information in this dataset.

columns_match = (
    df["discount_applied"] == df["promo_code_used"]
).all()

print("\nDo discount and promo code columns match?")
print(columns_match)

# If both columns are identical, I remove the duplicate column.
if columns_match:
    df = df.drop("promo_code_used", axis=1)
    print("Promo code column removed because it duplicates discount data.")
else:
    print("Both columns retained because their values differ.")


# --------------------------------------------------
# STEP 9: Validate the cleaned dataset
# --------------------------------------------------

print("\nFinal dataset shape:")
print(df.shape)

print("\nDuplicate customer IDs:")
print(df["customer_id"].duplicated().sum())

print("\nRemaining missing values:")
print(df.isnull().sum())

print("\nAge range:")
print(df["age"].min(), "to", df["age"].max())

print("\nPurchase amount range:")
print(df["purchase_amount"].min(), "to", df["purchase_amount"].max())

# Stop the script if the data breaks a basic rule.
problems = []
if df.isnull().sum().sum() > 0:
    problems.append("missing values remain")
if df["customer_id"].duplicated().any():
    problems.append("customer IDs are not unique")
if not df["review_rating"].between(1, 5).all():
    problems.append("review ratings are outside 1 to 5")
if (df["purchase_amount"] <= 0).any():
    problems.append("purchase amounts of zero or less")
if problems:
    raise ValueError("Validation failed: " + "; ".join(problems))

print("\nValidation passed.")


# --------------------------------------------------
# STEP 10: Save the cleaned dataset
# --------------------------------------------------

# The SQL queries and the Power BI dashboard both read this file.
df.to_csv(CLEANED_FILE, index=False)
print(f"\nCleaned data saved to: {CLEANED_FILE}")


# --------------------------------------------------
# STEP 11: Optional PostgreSQL upload
# --------------------------------------------------

# Keep DB_LOAD set to False until your PostgreSQL setup is ready.
# Set the password in your terminal before running the script:
#   Windows:       set PG_PASSWORD=your_password
#   macOS / Linux: export PG_PASSWORD=your_password
# The table must already exist. Create it with the first part of customer_behavior_queries.sql.

if DB_LOAD:
    password = os.getenv("PG_PASSWORD")
    if not password:
        sys.exit("PG_PASSWORD is not set. Set it in your terminal and run the script again.")

    # Imported here, so the script still runs when DB_LOAD is False.
    from urllib.parse import quote_plus

    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import ProgrammingError

    username = os.getenv("PG_USER", "postgres")
    host = os.getenv("PG_HOST", "localhost")
    port = os.getenv("PG_PORT", "5432")
    database = os.getenv("PG_DB", "Customer_Behavior")

    table_name = "customer"

    engine = create_engine(
        f"postgresql+psycopg2://{username}:{quote_plus(password)}@{host}:{port}/{database}"
    )

    try:
        # Emptying the table first keeps its column types and primary key.
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name}"))

        # Upload the DataFrame into PostgreSQL.
        df.to_sql(
            table_name,
            engine,
            if_exists="append",
            index=False,
            chunksize=1000,
            method="multi"
        )
        print(
            f"Data successfully loaded into PostgreSQL table '{table_name}' "
            f"in database '{database}'."
        )
    except ProgrammingError as err:
        sys.exit(
            "Could not load the data. Create the table first by running the "
            f"CREATE TABLE part of customer_behavior_queries.sql.\n{err}"
        )
    finally:
        engine.dispose()
else:
    print("\nPostgreSQL upload skipped (DB_LOAD is False).")