# Customer Shopping Behaviour Analysis

A small end-to-end analytics project built on 3,900 retail purchase records. It covers data cleaning in Python, ten business questions answered with SQL, a Power BI dashboard, and a written project report.

## Key findings

- **Revenue is driven by volume, not order size.** Men make 68% of purchases and 67.7% of revenue ($157,890 of $233,081), but the average purchase is almost the same for men ($59.54) and women ($60.25).
- **Average order value sits at about $60** across categories, age groups and shipping types.
- **Discounts are common but do not lift order size.** 43% of purchases used a discount, and discounted orders average $59.28 compared with $60.13 at full price.
- **Subscribers do not spend more per order.** Subscribers average $59.49 and non-subscribers $59.87.
- **Repeat buyers are more likely to subscribe.** Customers with more than five previous purchases subscribe at 27.6%, compared with 22.4% for everyone else.

The full write-up, with charts and recommendations, is in [`reports/Customer_Behavior_Project_Report.pdf`](reports/Customer_Behavior_Project_Report.pdf).

## Project structure

```
Customer_Behavior_GitHub/
├── Customer_Shopping_Behavior_Analysis.py   Cleaning script (Python)
├── customer_behavior_queries.sql            Table, load step and queries Q1 to Q10
├── data/
│   ├── customer_shopping_behavior.csv       Raw data
│   └── customer_shopping_cleaned.csv        Cleaned data (created by the script)
├── dashboard/
│   └── Customer_Behavior_Dashboard.pbix     Power BI dashboard
├── reports/
│   ├── make_report.py                       Builds the PDF report and its charts
│   ├── Customer_Behavior_Project_Report.pdf
│   └── figures/
├── tests/
│   └── test_pipeline.py                     Checks the cleaned output
├── CODE_REVIEW.md                           Problems found before upload and how they were fixed
├── requirements.txt
└── .gitignore
```

## Tools

- Python 3.9 or newer, with pandas, matplotlib and reportlab
- PostgreSQL for the SQL analysis (optional for the Python part)
- Power BI Desktop for the dashboard file
- Git and GitHub for version control

## How to run

1. Clone the repository and open a terminal in the project folder.
2. Install the packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Clean the data. This writes `data/customer_shopping_cleaned.csv`. The script finds the raw CSV in the project folder or in `data/`:
   ```bash
   python Customer_Shopping_Behavior_Analysis.py
   ```
4. **SQL (PostgreSQL).** Run the `CREATE TABLE` part of `customer_behavior_queries.sql`, then load the cleaned CSV. In psql, run this from the project folder:
   ```sql
   \copy customer FROM 'data/customer_shopping_cleaned.csv' WITH (FORMAT csv, HEADER true)
   ```
   You can also use pgAdmin's Import tool. To load from Python instead, set your password in the terminal, then set `DB_LOAD = True` in the script and run it again:
   ```bash
   export PG_PASSWORD=your_password        # Windows: set PG_PASSWORD=your_password
   ```
   Never commit a password to the repository.
5. **Dashboard.** Open `dashboard/Customer_Behavior_Dashboard.pbix` in Power BI Desktop. If it cannot find the data, go to *Transform data → Data source settings* and point it at `data/customer_shopping_cleaned.csv`.
6. **Report.** Rebuild the PDF and charts:
   ```bash
   python reports/make_report.py
   ```
7. **Checks.** Run the tests. They run the cleaning script and check its output:
   ```bash
   python tests/test_pipeline.py
   ```

## Notes on the data

- Each `customer_id` appears once, so "repeat buyer" means a count of earlier purchases, not an observed order history.
- Purchase amounts are spread almost evenly between $20 and $100. That is unusual for real retail data, so the results are best treated as analysis practice until they are checked against real records.
- `age_group` uses quartiles of age, so the "Senior" group covers ages 58 to 70. These are analysis groups, not official age bands.
- The file has no order dates, so trends over time cannot be measured.

## Data source

[Add where the dataset came from, with a link.]

## Author

[Your name]

## Licence

No licence is set yet. Add a `LICENSE` file before others reuse the code. MIT is a common, permissive choice.
