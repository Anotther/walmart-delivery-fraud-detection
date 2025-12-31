-- ============================================================================
-- Walmart Delivery Fraud Detection - Data Loading Script
-- ============================================================================
-- Purpose: Load CSV data into PostgreSQL staging tables and transform to final tables
-- Database: PostgreSQL 14+
-- Author: Data Engineering Team
-- Created: 2025-12-31
--
-- Prerequisites:
--   1. Schema created via 001_create_schema.sql
--   2. CSV files located in /data/ directory (relative to database server)
--   3. PostgreSQL user has COPY permissions
--
-- Usage:
--   psql -d your_database -f 003_load_data.sql
--
-- Note: Adjust the file paths below to match your environment.
--       The paths shown assume CSVs are in /tmp/walmart_data/ on the DB server.
-- ============================================================================

SET search_path TO walmart_fraud, public;

-- ============================================================================
-- CONFIGURATION
-- ============================================================================

-- Set the base path for CSV files (adjust as needed)
-- For psql variables:
\set data_path '/tmp/walmart_data'

-- ============================================================================
-- HELPER FUNCTION: Log ETL operations
-- ============================================================================

CREATE OR REPLACE FUNCTION walmart_fraud.log_etl_start(p_table_name VARCHAR)
RETURNS INTEGER AS $$
DECLARE
    v_load_id INTEGER;
BEGIN
    INSERT INTO walmart_fraud.etl_load_log (table_name, load_start, status)
    VALUES (p_table_name, CURRENT_TIMESTAMP, 'RUNNING')
    RETURNING load_id INTO v_load_id;

    RETURN v_load_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION walmart_fraud.log_etl_end(p_load_id INTEGER, p_rows INTEGER, p_status VARCHAR, p_error TEXT DEFAULT NULL)
RETURNS VOID AS $$
BEGIN
    UPDATE walmart_fraud.etl_load_log
    SET load_end = CURRENT_TIMESTAMP,
        rows_loaded = p_rows,
        status = p_status,
        error_message = p_error
    WHERE load_id = p_load_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 1: TRUNCATE STAGING TABLES
-- ============================================================================

TRUNCATE TABLE walmart_fraud.stg_customers;
TRUNCATE TABLE walmart_fraud.stg_drivers;
TRUNCATE TABLE walmart_fraud.stg_products;
TRUNCATE TABLE walmart_fraud.stg_orders;
TRUNCATE TABLE walmart_fraud.stg_missing_items;

-- ============================================================================
-- STEP 2: LOAD CSV FILES INTO STAGING TABLES
-- ============================================================================

-- Note: Replace file paths with your actual paths
-- Option A: Using absolute paths (recommended for production)
-- Option B: Using psql \copy for client-side files

-- ----------------------------------------------------------------------------
-- Load customers_data.csv
-- ----------------------------------------------------------------------------
\echo 'Loading customers_data.csv...'

-- Using COPY (server-side, requires superuser or pg_read_server_files)
-- Uncomment and adjust path as needed:
-- COPY walmart_fraud.stg_customers FROM '/tmp/walmart_data/customers_data.csv' WITH CSV HEADER;

-- Using \copy (client-side, works for any user)
\copy walmart_fraud.stg_customers FROM '/tmp/walmart_data/customers_data.csv' WITH CSV HEADER;

-- ----------------------------------------------------------------------------
-- Load drivers_data.csv
-- ----------------------------------------------------------------------------
\echo 'Loading drivers_data.csv...'

\copy walmart_fraud.stg_drivers FROM '/tmp/walmart_data/drivers_data.csv' WITH CSV HEADER;

-- ----------------------------------------------------------------------------
-- Load products_data.csv
-- ----------------------------------------------------------------------------
\echo 'Loading products_data.csv...'

\copy walmart_fraud.stg_products FROM '/tmp/walmart_data/products_data.csv' WITH CSV HEADER;

-- ----------------------------------------------------------------------------
-- Load orders.csv
-- ----------------------------------------------------------------------------
\echo 'Loading orders.csv...'

\copy walmart_fraud.stg_orders FROM '/tmp/walmart_data/orders.csv' WITH CSV HEADER;

-- ----------------------------------------------------------------------------
-- Load missing_items_data.csv
-- ----------------------------------------------------------------------------
\echo 'Loading missing_items_data.csv...'

\copy walmart_fraud.stg_missing_items FROM '/tmp/walmart_data/missing_items_data.csv' WITH CSV HEADER;

-- ============================================================================
-- STEP 3: VERIFY STAGING DATA
-- ============================================================================

\echo 'Verifying staging data counts...'

SELECT 'stg_customers' AS table_name, COUNT(*) AS row_count FROM walmart_fraud.stg_customers
UNION ALL
SELECT 'stg_drivers', COUNT(*) FROM walmart_fraud.stg_drivers
UNION ALL
SELECT 'stg_products', COUNT(*) FROM walmart_fraud.stg_products
UNION ALL
SELECT 'stg_orders', COUNT(*) FROM walmart_fraud.stg_orders
UNION ALL
SELECT 'stg_missing_items', COUNT(*) FROM walmart_fraud.stg_missing_items;

-- ============================================================================
-- STEP 4: TRANSFORM AND LOAD INTO FINAL TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Load customers (direct mapping, minimal transformation)
-- ----------------------------------------------------------------------------
\echo 'Transforming and loading customers...'

INSERT INTO walmart_fraud.customers (customer_id, customer_name, customer_age)
SELECT
    customer_id,
    customer_name,
    customer_age::SMALLINT
FROM walmart_fraud.stg_customers
WHERE customer_id IS NOT NULL
ON CONFLICT (customer_id) DO UPDATE SET
    customer_name = EXCLUDED.customer_name,
    customer_age = EXCLUDED.customer_age,
    updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Load drivers (rename 'age' column, 'Trips' to total_trips)
-- ----------------------------------------------------------------------------
\echo 'Transforming and loading drivers...'

INSERT INTO walmart_fraud.drivers (driver_id, driver_name, driver_age, total_trips)
SELECT
    driver_id,
    driver_name,
    age::SMALLINT,
    trips::INTEGER
FROM walmart_fraud.stg_drivers
WHERE driver_id IS NOT NULL
ON CONFLICT (driver_id) DO UPDATE SET
    driver_name = EXCLUDED.driver_name,
    driver_age = EXCLUDED.driver_age,
    total_trips = EXCLUDED.total_trips,
    updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Load products (parse price, map category, fix typo column name)
-- ----------------------------------------------------------------------------
\echo 'Transforming and loading products...'

INSERT INTO walmart_fraud.products (product_id, product_name, category_id, price)
SELECT
    sp.produc_id,  -- Note: typo in source column name
    sp.product_name,
    pc.category_id,
    REPLACE(REPLACE(sp.price, '$', ''), ',', '')::DECIMAL(10, 2) AS price
FROM walmart_fraud.stg_products sp
JOIN walmart_fraud.product_categories pc ON sp.category = pc.category_name
WHERE sp.produc_id IS NOT NULL
ON CONFLICT (product_id) DO UPDATE SET
    product_name = EXCLUDED.product_name,
    category_id = EXCLUDED.category_id,
    price = EXCLUDED.price,
    updated_at = CURRENT_TIMESTAMP;

-- ----------------------------------------------------------------------------
-- Load orders (parse date, amount, time; map region)
-- ----------------------------------------------------------------------------
\echo 'Transforming and loading orders...'

INSERT INTO walmart_fraud.orders (
    order_id,
    order_date,
    order_amount,
    region_id,
    items_delivered,
    items_missing,
    delivery_hour,
    driver_id,
    customer_id
)
SELECT
    so.order_id::UUID,
    so.date::DATE,
    REPLACE(REPLACE(so.order_amount, '$', ''), ',', '')::DECIMAL(12, 2) AS order_amount,
    r.region_id,
    so.items_delivered::INTEGER,
    so.items_missing::INTEGER,
    so.delivery_hour::TIME,
    so.driver_id,
    so.customer_id
FROM walmart_fraud.stg_orders so
JOIN walmart_fraud.regions r ON so.region = r.region_name
WHERE so.order_id IS NOT NULL
ON CONFLICT (order_id) DO NOTHING;  -- Skip duplicates

-- ----------------------------------------------------------------------------
-- Load missing items (normalize sparse structure to one row per item)
-- ----------------------------------------------------------------------------
\echo 'Transforming and loading missing items (normalized)...'

-- First, clear existing data to allow re-runs
TRUNCATE TABLE walmart_fraud.order_missing_items RESTART IDENTITY;

-- Insert product_id_1 (always present if row exists)
INSERT INTO walmart_fraud.order_missing_items (order_id, product_id, item_position)
SELECT
    smi.order_id::UUID,
    smi.product_id_1,
    1
FROM walmart_fraud.stg_missing_items smi
WHERE smi.product_id_1 IS NOT NULL
  AND smi.product_id_1 != ''
  AND EXISTS (SELECT 1 FROM walmart_fraud.orders o WHERE o.order_id = smi.order_id::UUID)
  AND EXISTS (SELECT 1 FROM walmart_fraud.products p WHERE p.product_id = smi.product_id_1);

-- Insert product_id_2 (may be null/empty)
INSERT INTO walmart_fraud.order_missing_items (order_id, product_id, item_position)
SELECT
    smi.order_id::UUID,
    smi.product_id_2,
    2
FROM walmart_fraud.stg_missing_items smi
WHERE smi.product_id_2 IS NOT NULL
  AND smi.product_id_2 != ''
  AND EXISTS (SELECT 1 FROM walmart_fraud.orders o WHERE o.order_id = smi.order_id::UUID)
  AND EXISTS (SELECT 1 FROM walmart_fraud.products p WHERE p.product_id = smi.product_id_2);

-- Insert product_id_3 (may be null/empty)
INSERT INTO walmart_fraud.order_missing_items (order_id, product_id, item_position)
SELECT
    smi.order_id::UUID,
    smi.product_id_3,
    3
FROM walmart_fraud.stg_missing_items smi
WHERE smi.product_id_3 IS NOT NULL
  AND smi.product_id_3 != ''
  AND EXISTS (SELECT 1 FROM walmart_fraud.orders o WHERE o.order_id = smi.order_id::UUID)
  AND EXISTS (SELECT 1 FROM walmart_fraud.products p WHERE p.product_id = smi.product_id_3);

-- ============================================================================
-- STEP 5: VERIFY FINAL DATA
-- ============================================================================

\echo 'Verifying final data counts...'

SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM walmart_fraud.customers
UNION ALL
SELECT 'drivers', COUNT(*) FROM walmart_fraud.drivers
UNION ALL
SELECT 'products', COUNT(*) FROM walmart_fraud.products
UNION ALL
SELECT 'orders', COUNT(*) FROM walmart_fraud.orders
UNION ALL
SELECT 'order_missing_items', COUNT(*) FROM walmart_fraud.order_missing_items
UNION ALL
SELECT 'regions', COUNT(*) FROM walmart_fraud.regions
UNION ALL
SELECT 'product_categories', COUNT(*) FROM walmart_fraud.product_categories;

-- ============================================================================
-- STEP 6: DATA QUALITY CHECKS
-- ============================================================================

\echo 'Running data quality checks...'

-- Check for orphan records
SELECT 'Orders with invalid driver_id' AS check_name,
       COUNT(*) AS issues
FROM walmart_fraud.stg_orders so
LEFT JOIN walmart_fraud.drivers d ON so.driver_id = d.driver_id
WHERE d.driver_id IS NULL AND so.driver_id IS NOT NULL;

SELECT 'Orders with invalid customer_id' AS check_name,
       COUNT(*) AS issues
FROM walmart_fraud.stg_orders so
LEFT JOIN walmart_fraud.customers c ON so.customer_id = c.customer_id
WHERE c.customer_id IS NULL AND so.customer_id IS NOT NULL;

SELECT 'Missing items with invalid product_id' AS check_name,
       COUNT(*) AS issues
FROM (
    SELECT product_id_1 AS product_id FROM walmart_fraud.stg_missing_items WHERE product_id_1 IS NOT NULL AND product_id_1 != ''
    UNION ALL
    SELECT product_id_2 FROM walmart_fraud.stg_missing_items WHERE product_id_2 IS NOT NULL AND product_id_2 != ''
    UNION ALL
    SELECT product_id_3 FROM walmart_fraud.stg_missing_items WHERE product_id_3 IS NOT NULL AND product_id_3 != ''
) mi
LEFT JOIN walmart_fraud.products p ON mi.product_id = p.product_id
WHERE p.product_id IS NULL;

-- Check for data anomalies
SELECT 'Orders with more missing than delivered items' AS check_name,
       COUNT(*) AS issues
FROM walmart_fraud.orders
WHERE items_missing > items_delivered;

SELECT 'Orders with negative amounts' AS check_name,
       COUNT(*) AS issues
FROM walmart_fraud.orders
WHERE order_amount < 0;

-- ============================================================================
-- STEP 7: ANALYZE TABLES FOR QUERY OPTIMIZATION
-- ============================================================================

\echo 'Analyzing tables for query optimization...'

ANALYZE walmart_fraud.customers;
ANALYZE walmart_fraud.drivers;
ANALYZE walmart_fraud.products;
ANALYZE walmart_fraud.orders;
ANALYZE walmart_fraud.order_missing_items;
ANALYZE walmart_fraud.regions;
ANALYZE walmart_fraud.product_categories;

-- ============================================================================
-- STEP 8: SUMMARY REPORT
-- ============================================================================

\echo ''
\echo '=============================================='
\echo 'DATA LOADING COMPLETE'
\echo '=============================================='
\echo ''

SELECT
    'Total Orders' AS metric,
    COUNT(*)::TEXT AS value
FROM walmart_fraud.orders
UNION ALL
SELECT
    'Orders with Missing Items',
    COUNT(*)::TEXT
FROM walmart_fraud.orders
WHERE items_missing > 0
UNION ALL
SELECT
    'Total Items Missing',
    SUM(items_missing)::TEXT
FROM walmart_fraud.orders
UNION ALL
SELECT
    'Unique Drivers',
    COUNT(DISTINCT driver_id)::TEXT
FROM walmart_fraud.orders
UNION ALL
SELECT
    'Unique Customers',
    COUNT(DISTINCT customer_id)::TEXT
FROM walmart_fraud.orders
UNION ALL
SELECT
    'Date Range',
    MIN(order_date)::TEXT || ' to ' || MAX(order_date)::TEXT
FROM walmart_fraud.orders
UNION ALL
SELECT
    'Total Order Value',
    '$' || TO_CHAR(SUM(order_amount), 'FM999,999,999.00')
FROM walmart_fraud.orders;

\echo ''
\echo 'Data loading completed successfully!'
\echo ''

-- ============================================================================
-- END OF DATA LOADING SCRIPT
-- ============================================================================
