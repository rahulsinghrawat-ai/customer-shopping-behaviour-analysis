-- =====================================================================
-- Customer Shopping Behaviour: SQL analysis (PostgreSQL)
--
-- Run the sections in order:
--   1. Create the table
--   2. Load the cleaned CSV
--   3. Check the load
--   4. Business questions Q1 to Q10
--
-- Column names are written in plain words so they read well in
-- pgAdmin, psql and Power BI.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. Create the table
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS customer;

CREATE TABLE customer (
    customer_id             INT PRIMARY KEY,
    age                     INT,
    gender                  VARCHAR(20),
    item_purchased          VARCHAR(50),
    category                VARCHAR(50),
    purchase_amount         INT,
    location                VARCHAR(50),
    size                    VARCHAR(10),
    color                   VARCHAR(30),
    season                  VARCHAR(20),
    review_rating           NUMERIC(3,2),
    subscription_status     VARCHAR(10),
    shipping_type           VARCHAR(50),
    discount_applied        VARCHAR(10),
    previous_purchases      INT,
    payment_method          VARCHAR(30),
    frequency_of_purchases  VARCHAR(30),
    age_group               VARCHAR(20),
    purchase_frequency_days INT
);

-- ---------------------------------------------------------------------
-- 2. Load the cleaned CSV. Pick ONE of these options.
--
--    a) psql, run from the project folder (\copy reads the file on your own PC):
--       \copy customer FROM 'data/customer_shopping_cleaned.csv' WITH (FORMAT csv, HEADER true)
--
--    b) pgAdmin: right-click the customer table, then Import/Export Data,
--       choose Import, pick the file, turn on Header, and click OK.
--
--    c) Python: set DB_LOAD = True in Customer_Shopping_Behavior_Analysis.py, then run it
--       (the table above must exist first)
-- ---------------------------------------------------------------------

-- ---------------------------------------------------------------------
-- 3. Check the load. Expect 3900 rows.
-- ---------------------------------------------------------------------
SELECT COUNT(*) AS row_count, COUNT(DISTINCT customer_id) AS unique_customers
FROM customer;

SELECT * FROM customer LIMIT 5;


-- ---------------------------------------------------------------------
-- Q1. What is the total revenue from male and female customers?
-- ---------------------------------------------------------------------
SELECT
    gender,
    COUNT(*)                                                                   AS purchases,
    SUM(purchase_amount)                                                       AS revenue,
    ROUND(100.0 * SUM(purchase_amount) / SUM(SUM(purchase_amount)) OVER (), 2) AS revenue_share_pct,
    ROUND(AVG(purchase_amount), 2)                                             AS avg_purchase
FROM customer
GROUP BY gender
ORDER BY revenue DESC;


-- ---------------------------------------------------------------------
-- Q2. Which discounted purchases were above the average purchase amount?
--     (The question says "more than", so the comparison is strictly greater.)
-- ---------------------------------------------------------------------
SELECT customer_id, purchase_amount
FROM customer
WHERE discount_applied = 'Yes'
  AND purchase_amount > (SELECT AVG(purchase_amount) FROM customer)
ORDER BY purchase_amount DESC;

-- Same question as a count:
SELECT COUNT(*) AS discounted_above_average
FROM customer
WHERE discount_applied = 'Yes'
  AND purchase_amount > (SELECT AVG(purchase_amount) FROM customer);


-- ---------------------------------------------------------------------
-- Q3. Top 5 products by average review rating.
--     Products with the same average are sorted by name, so the result
--     is the same every time the query runs.
-- ---------------------------------------------------------------------
SELECT
    item_purchased,
    ROUND(AVG(review_rating), 2) AS average_rating
FROM customer
GROUP BY item_purchased
ORDER BY AVG(review_rating) DESC, item_purchased
LIMIT 5;


-- ---------------------------------------------------------------------
-- Q4. Average purchase amount: Standard vs Express shipping.
-- ---------------------------------------------------------------------
SELECT
    shipping_type,
    COUNT(*)                       AS orders,
    ROUND(AVG(purchase_amount), 2) AS avg_purchase
FROM customer
WHERE shipping_type IN ('Standard', 'Express')
GROUP BY shipping_type
ORDER BY avg_purchase DESC;


-- ---------------------------------------------------------------------
-- Q5. Do subscribers spend more? Compare subscribers and non-subscribers.
--     Average spend per order is the fair comparison. Total revenue
--     mostly reflects how many customers are in each group.
-- ---------------------------------------------------------------------
SELECT
    subscription_status,
    COUNT(*)                       AS total_customers,
    ROUND(AVG(purchase_amount), 2) AS avg_spend,
    SUM(purchase_amount)           AS total_revenue
FROM customer
GROUP BY subscription_status
ORDER BY total_revenue DESC;


-- ---------------------------------------------------------------------
-- Q6. Top 5 products with the highest share of discounted purchases.
-- ---------------------------------------------------------------------
SELECT
    item_purchased,
    ROUND(100.0 * SUM(CASE WHEN discount_applied = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2)
        AS discount_rate_pct
FROM customer
GROUP BY item_purchased
ORDER BY discount_rate_pct DESC, item_purchased
LIMIT 5;


-- ---------------------------------------------------------------------
-- Q7. Customer segments based on previous purchases.
--     New = 1 previous purchase, Returning = 2 to 10, Loyal = 11 or more.
--     (A value of 0 would also be labelled Loyal, but the data has none.)
-- ---------------------------------------------------------------------
WITH segmented AS (
    SELECT
        customer_id,
        CASE
            WHEN previous_purchases = 1              THEN 'New'
            WHEN previous_purchases BETWEEN 2 AND 10 THEN 'Returning'
            ELSE 'Loyal'
        END AS customer_segment
    FROM customer
)
SELECT
    customer_segment,
    COUNT(*)                                            AS number_of_customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_pct
FROM segmented
GROUP BY customer_segment
ORDER BY number_of_customers DESC;


-- ---------------------------------------------------------------------
-- Q8. Top 3 most purchased products in each category.
--     RANK() gives products with the same count the same position, instead
--     of breaking the tie at random as ROW_NUMBER() does.
--     Outerwear has only two products, so it returns two rows.
-- ---------------------------------------------------------------------
WITH item_counts AS (
    SELECT
        category,
        item_purchased,
        COUNT(customer_id) AS total_orders,
        RANK() OVER (PARTITION BY category ORDER BY COUNT(customer_id) DESC) AS item_rank
    FROM customer
    GROUP BY category, item_purchased
)
SELECT category, item_rank, item_purchased, total_orders
FROM item_counts
WHERE item_rank <= 3
ORDER BY category, item_rank, item_purchased;


-- ---------------------------------------------------------------------
-- Q9. Are repeat buyers (more than 5 previous purchases) more likely to subscribe?
--     Compare subscription RATES. Raw counts depend on how big each group is.
-- ---------------------------------------------------------------------
SELECT
    CASE WHEN previous_purchases > 5
         THEN 'Repeat buyer (more than 5)'
         ELSE 'Other (5 or fewer)'
    END AS buyer_type,
    COUNT(*) AS customers,
    ROUND(100.0 * AVG(CASE WHEN subscription_status = 'Yes' THEN 1 ELSE 0 END), 2)
        AS subscription_rate_pct
FROM customer
GROUP BY 1
ORDER BY 1;


-- ---------------------------------------------------------------------
-- Q10. Revenue contribution of each age group.
-- ---------------------------------------------------------------------
SELECT
    age_group,
    COUNT(*)                                                                   AS customers,
    SUM(purchase_amount)                                                       AS total_revenue,
    ROUND(100.0 * SUM(purchase_amount) / SUM(SUM(purchase_amount)) OVER (), 2) AS revenue_share_pct
FROM customer
GROUP BY age_group
ORDER BY total_revenue DESC;