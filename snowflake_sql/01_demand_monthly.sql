-- =========================================================
-- Context Setup
-- =========================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE COMPUTE_WH;
USE DATABASE SUPPLY_CHAIN_DB;
USE SCHEMA RAW;

-- =========================================================
-- Monthly Demand (Planning Foundation)
-- =========================================================
-- Converts order-level sales into monthly demand per product.
-- Filters out records with missing order dates to ensure
-- valid time-based aggregation.

CREATE OR REPLACE TABLE DEMAND_MONTHLY AS
SELECT
    PRODUCT_ID,
    DATE_TRUNC('month', ORDER_DATE) AS DEMAND_MONTH,
    SUM(ORDER_QTY) AS MONTHLY_DEMAND
FROM RAW_SALES_ORDERS
WHERE ORDER_DATE IS NOT NULL
GROUP BY
    PRODUCT_ID,
    DATE_TRUNC('month', ORDER_DATE);

-- =========================================================
-- Inventory Enriched (Inventory Value Layer)
-- =========================================================
-- Adds financial context to inventory by calculating
-- inventory value from on-hand quantity and unit cost.

CREATE OR REPLACE TABLE INVENTORY_ENRICHED AS
SELECT
    PRODUCT_ID,
    PRODUCT_CATEGORY,
    ON_HAND_QTY,
    UNIT_COST,
    ON_HAND_QTY * UNIT_COST AS INVENTORY_VALUE
FROM RAW_INVENTORY;

-- =========================================================
-- Inventory Turnover (Core Inventory KPI)
-- =========================================================
-- Measures how efficiently inventory is consumed by demand.
-- Uses total demand over the period divided by average inventory.

CREATE OR REPLACE TABLE INVENTORY_TURNOVER AS
SELECT
    d.PRODUCT_ID,
    SUM(d.MONTHLY_DEMAND) AS TOTAL_DEMAND,
    AVG(i.ON_HAND_QTY) AS AVG_INVENTORY,
    SUM(d.MONTHLY_DEMAND) / NULLIF(AVG(i.ON_HAND_QTY), 0) AS INVENTORY_TURNOVER
FROM DEMAND_MONTHLY d
JOIN RAW_INVENTORY i
    ON d.PRODUCT_ID = i.PRODUCT_ID
GROUP BY
    d.PRODUCT_ID;


SELECT *
FROM DEMAND_MONTHLY
ORDER BY DEMAND_MONTH DESC
LIMIT 50;
