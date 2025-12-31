-- ============================================================================
-- Walmart Delivery Fraud Detection - Analytical Views
-- ============================================================================
-- Purpose: Create views for fraud detection analysis and reporting
-- Database: PostgreSQL 14+
-- Author: Data Engineering Team
-- Created: 2025-12-31
-- ============================================================================

SET search_path TO walmart_fraud, public;

-- ============================================================================
-- BASE DENORMALIZED VIEWS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- View: v_orders_full
-- Description: Denormalized order view with all dimensional data
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW walmart_fraud.v_orders_full AS
SELECT
    o.order_id,
    o.order_date,
    EXTRACT(YEAR FROM o.order_date) AS order_year,
    EXTRACT(MONTH FROM o.order_date) AS order_month,
    EXTRACT(DOW FROM o.order_date) AS day_of_week,
    TO_CHAR(o.order_date, 'Day') AS day_name,
    o.order_amount,
    r.region_name,
    o.items_delivered,
    o.items_missing,
    o.delivery_hour,
    EXTRACT(HOUR FROM o.delivery_hour) AS delivery_hour_int,
    CASE
        WHEN EXTRACT(HOUR FROM o.delivery_hour) BETWEEN 6 AND 11 THEN 'Morning'
        WHEN EXTRACT(HOUR FROM o.delivery_hour) BETWEEN 12 AND 17 THEN 'Afternoon'
        WHEN EXTRACT(HOUR FROM o.delivery_hour) BETWEEN 18 AND 21 THEN 'Evening'
        ELSE 'Night'
    END AS delivery_period,
    d.driver_id,
    d.driver_name,
    d.driver_age,
    d.total_trips AS driver_total_trips,
    c.customer_id,
    c.customer_name,
    c.customer_age,
    -- Calculated fields for fraud analysis
    CASE WHEN o.items_missing > 0 THEN TRUE ELSE FALSE END AS has_missing_items,
    ROUND(o.items_missing::DECIMAL / NULLIF(o.items_delivered, 0) * 100, 2) AS missing_rate_pct,
    ROUND(o.order_amount / NULLIF(o.items_delivered, 0), 2) AS avg_item_value
FROM walmart_fraud.orders o
JOIN walmart_fraud.regions r ON o.region_id = r.region_id
JOIN walmart_fraud.drivers d ON o.driver_id = d.driver_id
JOIN walmart_fraud.customers c ON o.customer_id = c.customer_id;

COMMENT ON VIEW walmart_fraud.v_orders_full IS 'Denormalized order view with all dimensions and calculated fields';

-- ----------------------------------------------------------------------------
-- View: v_missing_items_full
-- Description: Denormalized missing items with product and order details
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW walmart_fraud.v_missing_items_full AS
SELECT
    mi.missing_item_id,
    mi.order_id,
    mi.item_position,
    p.product_id,
    p.product_name,
    pc.category_name AS product_category,
    p.price AS product_price,
    o.order_date,
    o.order_amount,
    r.region_name,
    d.driver_id,
    d.driver_name,
    c.customer_id,
    c.customer_name
FROM walmart_fraud.order_missing_items mi
JOIN walmart_fraud.products p ON mi.product_id = p.product_id
JOIN walmart_fraud.product_categories pc ON p.category_id = pc.category_id
JOIN walmart_fraud.orders o ON mi.order_id = o.order_id
JOIN walmart_fraud.regions r ON o.region_id = r.region_id
JOIN walmart_fraud.drivers d ON o.driver_id = d.driver_id
JOIN walmart_fraud.customers c ON o.customer_id = c.customer_id;

COMMENT ON VIEW walmart_fraud.v_missing_items_full IS 'Denormalized missing items with full product and order context';

-- ============================================================================
-- DRIVER ANALYSIS VIEWS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- View: v_driver_fraud_metrics
-- Description: Per-driver fraud risk metrics
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW walmart_fraud.v_driver_fraud_metrics AS
WITH driver_orders AS (
    SELECT
        d.driver_id,
        d.driver_name,
        d.driver_age,
        d.total_trips,
        COUNT(o.order_id) AS orders_count,
        COUNT(CASE WHEN o.items_missing > 0 THEN 1 END) AS orders_with_missing,
        SUM(o.items_delivered) AS total_items_delivered,
        SUM(o.items_missing) AS total_items_missing,
        SUM(o.order_amount) AS total_order_value,
        AVG(o.order_amount) AS avg_order_value
    FROM walmart_fraud.drivers d
    LEFT JOIN walmart_fraud.orders o ON d.driver_id = o.driver_id
    GROUP BY d.driver_id, d.driver_name, d.driver_age, d.total_trips
),
missing_value AS (
    SELECT
        o.driver_id,
        SUM(p.price) AS total_missing_value
    FROM walmart_fraud.orders o
    JOIN walmart_fraud.order_missing_items mi ON o.order_id = mi.order_id
    JOIN walmart_fraud.products p ON mi.product_id = p.product_id
    GROUP BY o.driver_id
)
SELECT
    drv.driver_id,
    drv.driver_name,
    drv.driver_age,
    drv.total_trips,
    drv.orders_count,
    drv.orders_with_missing,
    drv.total_items_delivered,
    drv.total_items_missing,
    ROUND(drv.total_order_value, 2) AS total_order_value,
    ROUND(drv.avg_order_value, 2) AS avg_order_value,
    COALESCE(mv.total_missing_value, 0) AS total_missing_value,
    -- Fraud risk indicators
    ROUND(drv.orders_with_missing::DECIMAL / NULLIF(drv.orders_count, 0) * 100, 2) AS missing_order_rate_pct,
    ROUND(drv.total_items_missing::DECIMAL / NULLIF(drv.total_items_delivered, 0) * 100, 2) AS missing_item_rate_pct,
    ROUND(COALESCE(mv.total_missing_value, 0) / NULLIF(drv.total_order_value, 0) * 100, 2) AS missing_value_rate_pct,
    -- Risk score (higher = more suspicious)
    ROUND(
        (drv.orders_with_missing::DECIMAL / NULLIF(drv.orders_count, 0) * 40) +
        (drv.total_items_missing::DECIMAL / NULLIF(drv.total_items_delivered, 0) * 30) +
        (COALESCE(mv.total_missing_value, 0) / NULLIF(drv.total_order_value, 0) * 30),
        2
    ) AS fraud_risk_score
FROM driver_orders drv
LEFT JOIN missing_value mv ON drv.driver_id = mv.driver_id
ORDER BY fraud_risk_score DESC NULLS LAST;

COMMENT ON VIEW walmart_fraud.v_driver_fraud_metrics IS 'Per-driver fraud risk metrics with composite risk score';

-- ----------------------------------------------------------------------------
-- View: v_driver_daily_performance
-- Description: Daily performance metrics per driver for trend analysis
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW walmart_fraud.v_driver_daily_performance AS
SELECT
    d.driver_id,
    d.driver_name,
    o.order_date,
    COUNT(o.order_id) AS daily_orders,
    SUM(o.items_delivered) AS daily_items_delivered,
    SUM(o.items_missing) AS daily_items_missing,
    SUM(o.order_amount) AS daily_order_value,
    ROUND(SUM(o.items_missing)::DECIMAL / NULLIF(SUM(o.items_delivered), 0) * 100, 2) AS daily_missing_rate_pct
FROM walmart_fraud.drivers d
JOIN walmart_fraud.orders o ON d.driver_id = o.driver_id
GROUP BY d.driver_id, d.driver_name, o.order_date
ORDER BY d.driver_id, o.order_date;

COMMENT ON VIEW walmart_fraud.v_driver_daily_performance IS 'Daily performance metrics per driver for trend analysis';

-- ============================================================================
-- CUSTOMER ANALYSIS VIEWS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- View: v_customer_fraud_metrics
-- Description: Per-customer fraud risk metrics
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW walmart_fraud.v_customer_fraud_metrics AS
WITH customer_orders AS (
    SELECT
        c.customer_id,
        c.customer_name,
        c.customer_age,
        COUNT(o.order_id) AS orders_count,
        COUNT(CASE WHEN o.items_missing > 0 THEN 1 END) AS orders_with_missing,
        SUM(o.items_delivered) AS total_items_delivered,
        SUM(o.items_missing) AS total_items_missing,
        SUM(o.order_amount) AS total_order_value,
        AVG(o.order_amount) AS avg_order_value,
        MIN(o.order_date) AS first_order_date,
        MAX(o.order_date) AS last_order_date
    FROM walmart_fraud.customers c
    LEFT JOIN walmart_fraud.orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, c.customer_name, c.customer_age
),
missing_value AS (
    SELECT
        o.customer_id,
        SUM(p.price) AS total_missing_value,
        COUNT(DISTINCT p.product_id) AS unique_missing_products
    FROM walmart_fraud.orders o
    JOIN walmart_fraud.order_missing_items mi ON o.order_id = mi.order_id
    JOIN walmart_fraud.products p ON mi.product_id = p.product_id
    GROUP BY o.customer_id
)
SELECT
    co.customer_id,
    co.customer_name,
    co.customer_age,
    co.orders_count,
    co.orders_with_missing,
    co.total_items_delivered,
    co.total_items_missing,
    ROUND(co.total_order_value, 2) AS total_order_value,
    ROUND(co.avg_order_value, 2) AS avg_order_value,
    co.first_order_date,
    co.last_order_date,
    COALESCE(mv.total_missing_value, 0) AS total_missing_value,
    COALESCE(mv.unique_missing_products, 0) AS unique_missing_products,
    -- Fraud risk indicators
    ROUND(co.orders_with_missing::DECIMAL / NULLIF(co.orders_count, 0) * 100, 2) AS missing_order_rate_pct,
    ROUND(co.total_items_missing::DECIMAL / NULLIF(co.total_items_delivered, 0) * 100, 2) AS missing_item_rate_pct,
    ROUND(COALESCE(mv.total_missing_value, 0) / NULLIF(co.total_order_value, 0) * 100, 2) AS missing_value_rate_pct,
    -- Risk score (higher = more suspicious)
    ROUND(
        (co.orders_with_missing::DECIMAL / NULLIF(co.orders_count, 0) * 40) +
        (co.total_items_missing::DECIMAL / NULLIF(co.total_items_delivered, 0) * 30) +
        (COALESCE(mv.total_missing_value, 0) / NULLIF(co.total_order_value, 0) * 30),
        2
    ) AS fraud_risk_score
FROM customer_orders co
LEFT JOIN missing_value mv ON co.customer_id = mv.customer_id
ORDER BY fraud_risk_score DESC NULLS LAST;

COMMENT ON VIEW walmart_fraud.v_customer_fraud_metrics IS 'Per-customer fraud risk metrics with composite risk score';

-- ============================================================================
-- REGIONAL ANALYSIS VIEWS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- View: v_region_fraud_metrics
-- Description: Per-region fraud risk metrics
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW walmart_fraud.v_region_fraud_metrics AS
WITH region_orders AS (
    SELECT
        r.region_id,
        r.region_name,
        COUNT(o.order_id) AS orders_count,
        COUNT(CASE WHEN o.items_missing > 0 THEN 1 END) AS orders_with_missing,
        SUM(o.items_delivered) AS total_items_delivered,
        SUM(o.items_missing) AS total_items_missing,
        SUM(o.order_amount) AS total_order_value,
        COUNT(DISTINCT o.driver_id) AS unique_drivers,
        COUNT(DISTINCT o.customer_id) AS unique_customers
    FROM walmart_fraud.regions r
    LEFT JOIN walmart_fraud.orders o ON r.region_id = o.region_id
    GROUP BY r.region_id, r.region_name
),
missing_value AS (
    SELECT
        o.region_id,
        SUM(p.price) AS total_missing_value
    FROM walmart_fraud.orders o
    JOIN walmart_fraud.order_missing_items mi ON o.order_id = mi.order_id
    JOIN walmart_fraud.products p ON mi.product_id = p.product_id
    GROUP BY o.region_id
)
SELECT
    ro.region_id,
    ro.region_name,
    ro.orders_count,
    ro.orders_with_missing,
    ro.total_items_delivered,
    ro.total_items_missing,
    ROUND(ro.total_order_value, 2) AS total_order_value,
    ro.unique_drivers,
    ro.unique_customers,
    COALESCE(mv.total_missing_value, 0) AS total_missing_value,
    -- Fraud risk indicators
    ROUND(ro.orders_with_missing::DECIMAL / NULLIF(ro.orders_count, 0) * 100, 2) AS missing_order_rate_pct,
    ROUND(ro.total_items_missing::DECIMAL / NULLIF(ro.total_items_delivered, 0) * 100, 2) AS missing_item_rate_pct,
    ROUND(COALESCE(mv.total_missing_value, 0) / NULLIF(ro.total_order_value, 0) * 100, 2) AS missing_value_rate_pct,
    -- Orders per driver (efficiency)
    ROUND(ro.orders_count::DECIMAL / NULLIF(ro.unique_drivers, 0), 2) AS orders_per_driver
FROM region_orders ro
LEFT JOIN missing_value mv ON ro.region_id = mv.region_id
ORDER BY missing_item_rate_pct DESC NULLS LAST;

COMMENT ON VIEW walmart_fraud.v_region_fraud_metrics IS 'Per-region fraud risk metrics';

-- ============================================================================
-- TEMPORAL ANALYSIS VIEWS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- View: v_monthly_fraud_trends
-- Description: Monthly fraud trends for time-series analysis
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW walmart_fraud.v_monthly_fraud_trends AS
WITH monthly_orders AS (
    SELECT
        DATE_TRUNC('month', order_date)::DATE AS month_start,
        COUNT(order_id) AS orders_count,
        COUNT(CASE WHEN items_missing > 0 THEN 1 END) AS orders_with_missing,
        SUM(items_delivered) AS total_items_delivered,
        SUM(items_missing) AS total_items_missing,
        SUM(order_amount) AS total_order_value
    FROM walmart_fraud.orders
    GROUP BY DATE_TRUNC('month', order_date)
),
monthly_missing_value AS (
    SELECT
        DATE_TRUNC('month', o.order_date)::DATE AS month_start,
        SUM(p.price) AS total_missing_value
    FROM walmart_fraud.orders o
    JOIN walmart_fraud.order_missing_items mi ON o.order_id = mi.order_id
    JOIN walmart_fraud.products p ON mi.product_id = p.product_id
    GROUP BY DATE_TRUNC('month', o.order_date)
)
SELECT
    mo.month_start,
    TO_CHAR(mo.month_start, 'Month YYYY') AS month_name,
    mo.orders_count,
    mo.orders_with_missing,
    mo.total_items_delivered,
    mo.total_items_missing,
    ROUND(mo.total_order_value, 2) AS total_order_value,
    COALESCE(mmv.total_missing_value, 0) AS total_missing_value,
    ROUND(mo.orders_with_missing::DECIMAL / NULLIF(mo.orders_count, 0) * 100, 2) AS missing_order_rate_pct,
    ROUND(mo.total_items_missing::DECIMAL / NULLIF(mo.total_items_delivered, 0) * 100, 2) AS missing_item_rate_pct,
    -- Month-over-month change
    LAG(mo.total_items_missing) OVER (ORDER BY mo.month_start) AS prev_month_missing,
    mo.total_items_missing - LAG(mo.total_items_missing) OVER (ORDER BY mo.month_start) AS mom_missing_change
FROM monthly_orders mo
LEFT JOIN monthly_missing_value mmv ON mo.month_start = mmv.month_start
ORDER BY mo.month_start;

COMMENT ON VIEW walmart_fraud.v_monthly_fraud_trends IS 'Monthly fraud trends for time-series analysis';

-- ----------------------------------------------------------------------------
-- View: v_hourly_fraud_patterns
-- Description: Fraud patterns by hour of day
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW walmart_fraud.v_hourly_fraud_patterns AS
SELECT
    EXTRACT(HOUR FROM delivery_hour)::INTEGER AS delivery_hour_int,
    CASE
        WHEN EXTRACT(HOUR FROM delivery_hour) BETWEEN 6 AND 11 THEN 'Morning (6-11)'
        WHEN EXTRACT(HOUR FROM delivery_hour) BETWEEN 12 AND 17 THEN 'Afternoon (12-17)'
        WHEN EXTRACT(HOUR FROM delivery_hour) BETWEEN 18 AND 21 THEN 'Evening (18-21)'
        ELSE 'Night (22-5)'
    END AS delivery_period,
    COUNT(order_id) AS orders_count,
    COUNT(CASE WHEN items_missing > 0 THEN 1 END) AS orders_with_missing,
    SUM(items_delivered) AS total_items_delivered,
    SUM(items_missing) AS total_items_missing,
    ROUND(SUM(order_amount), 2) AS total_order_value,
    ROUND(SUM(items_missing)::DECIMAL / NULLIF(SUM(items_delivered), 0) * 100, 2) AS missing_item_rate_pct
FROM walmart_fraud.orders
GROUP BY
    EXTRACT(HOUR FROM delivery_hour),
    CASE
        WHEN EXTRACT(HOUR FROM delivery_hour) BETWEEN 6 AND 11 THEN 'Morning (6-11)'
        WHEN EXTRACT(HOUR FROM delivery_hour) BETWEEN 12 AND 17 THEN 'Afternoon (12-17)'
        WHEN EXTRACT(HOUR FROM delivery_hour) BETWEEN 18 AND 21 THEN 'Evening (18-21)'
        ELSE 'Night (22-5)'
    END
ORDER BY delivery_hour_int;

COMMENT ON VIEW walmart_fraud.v_hourly_fraud_patterns IS 'Fraud patterns by hour of day';

-- ----------------------------------------------------------------------------
-- View: v_day_of_week_fraud_patterns
-- Description: Fraud patterns by day of week
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW walmart_fraud.v_day_of_week_fraud_patterns AS
SELECT
    EXTRACT(DOW FROM order_date)::INTEGER AS day_of_week,
    TO_CHAR(order_date, 'Day') AS day_name,
    COUNT(order_id) AS orders_count,
    COUNT(CASE WHEN items_missing > 0 THEN 1 END) AS orders_with_missing,
    SUM(items_delivered) AS total_items_delivered,
    SUM(items_missing) AS total_items_missing,
    ROUND(SUM(order_amount), 2) AS total_order_value,
    ROUND(SUM(items_missing)::DECIMAL / NULLIF(SUM(items_delivered), 0) * 100, 2) AS missing_item_rate_pct
FROM walmart_fraud.orders
GROUP BY
    EXTRACT(DOW FROM order_date),
    TO_CHAR(order_date, 'Day')
ORDER BY day_of_week;

COMMENT ON VIEW walmart_fraud.v_day_of_week_fraud_patterns IS 'Fraud patterns by day of week';

-- ============================================================================
-- PRODUCT ANALYSIS VIEWS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- View: v_product_fraud_metrics
-- Description: Per-product fraud metrics (most frequently missing products)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW walmart_fraud.v_product_fraud_metrics AS
SELECT
    p.product_id,
    p.product_name,
    pc.category_name,
    p.price,
    COUNT(mi.missing_item_id) AS times_missing,
    COUNT(DISTINCT mi.order_id) AS orders_affected,
    ROUND(COUNT(mi.missing_item_id) * p.price, 2) AS total_missing_value,
    -- Rank within category
    RANK() OVER (PARTITION BY pc.category_name ORDER BY COUNT(mi.missing_item_id) DESC) AS rank_in_category
FROM walmart_fraud.products p
JOIN walmart_fraud.product_categories pc ON p.category_id = pc.category_id
LEFT JOIN walmart_fraud.order_missing_items mi ON p.product_id = mi.product_id
GROUP BY p.product_id, p.product_name, pc.category_name, p.price
ORDER BY times_missing DESC;

COMMENT ON VIEW walmart_fraud.v_product_fraud_metrics IS 'Per-product fraud metrics showing most frequently missing products';

-- ----------------------------------------------------------------------------
-- View: v_category_fraud_metrics
-- Description: Per-category fraud metrics
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW walmart_fraud.v_category_fraud_metrics AS
SELECT
    pc.category_id,
    pc.category_name,
    COUNT(DISTINCT p.product_id) AS products_in_category,
    COUNT(mi.missing_item_id) AS total_items_missing,
    COUNT(DISTINCT mi.order_id) AS orders_affected,
    ROUND(SUM(p.price), 2) AS total_missing_value,
    ROUND(AVG(p.price), 2) AS avg_missing_item_price
FROM walmart_fraud.product_categories pc
LEFT JOIN walmart_fraud.products p ON pc.category_id = p.category_id
LEFT JOIN walmart_fraud.order_missing_items mi ON p.product_id = mi.product_id
GROUP BY pc.category_id, pc.category_name
ORDER BY total_items_missing DESC;

COMMENT ON VIEW walmart_fraud.v_category_fraud_metrics IS 'Per-category fraud metrics';

-- ============================================================================
-- HIGH-RISK DETECTION VIEWS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- View: v_high_risk_drivers
-- Description: Drivers with anomalously high missing item rates
-- Uses statistical thresholds (mean + 2 std dev)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW walmart_fraud.v_high_risk_drivers AS
WITH driver_stats AS (
    SELECT
        driver_id,
        driver_name,
        orders_count,
        total_items_missing,
        missing_item_rate_pct,
        fraud_risk_score
    FROM walmart_fraud.v_driver_fraud_metrics
    WHERE orders_count >= 5  -- Minimum orders threshold
),
thresholds AS (
    SELECT
        AVG(missing_item_rate_pct) AS mean_rate,
        STDDEV(missing_item_rate_pct) AS stddev_rate,
        AVG(fraud_risk_score) AS mean_score,
        STDDEV(fraud_risk_score) AS stddev_score
    FROM driver_stats
)
SELECT
    ds.*,
    t.mean_rate AS population_mean_rate,
    t.stddev_rate AS population_stddev_rate,
    ROUND((ds.missing_item_rate_pct - t.mean_rate) / NULLIF(t.stddev_rate, 0), 2) AS z_score,
    CASE
        WHEN ds.missing_item_rate_pct > t.mean_rate + 2 * t.stddev_rate THEN 'HIGH'
        WHEN ds.missing_item_rate_pct > t.mean_rate + t.stddev_rate THEN 'MEDIUM'
        ELSE 'LOW'
    END AS risk_level
FROM driver_stats ds
CROSS JOIN thresholds t
WHERE ds.missing_item_rate_pct > t.mean_rate + t.stddev_rate
ORDER BY ds.fraud_risk_score DESC;

COMMENT ON VIEW walmart_fraud.v_high_risk_drivers IS 'Drivers flagged as high-risk based on statistical thresholds';

-- ----------------------------------------------------------------------------
-- View: v_high_risk_customers
-- Description: Customers with anomalously high missing item rates
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW walmart_fraud.v_high_risk_customers AS
WITH customer_stats AS (
    SELECT
        customer_id,
        customer_name,
        orders_count,
        total_items_missing,
        missing_item_rate_pct,
        fraud_risk_score
    FROM walmart_fraud.v_customer_fraud_metrics
    WHERE orders_count >= 3  -- Minimum orders threshold
),
thresholds AS (
    SELECT
        AVG(missing_item_rate_pct) AS mean_rate,
        STDDEV(missing_item_rate_pct) AS stddev_rate
    FROM customer_stats
)
SELECT
    cs.*,
    t.mean_rate AS population_mean_rate,
    t.stddev_rate AS population_stddev_rate,
    ROUND((cs.missing_item_rate_pct - t.mean_rate) / NULLIF(t.stddev_rate, 0), 2) AS z_score,
    CASE
        WHEN cs.missing_item_rate_pct > t.mean_rate + 2 * t.stddev_rate THEN 'HIGH'
        WHEN cs.missing_item_rate_pct > t.mean_rate + t.stddev_rate THEN 'MEDIUM'
        ELSE 'LOW'
    END AS risk_level
FROM customer_stats cs
CROSS JOIN thresholds t
WHERE cs.missing_item_rate_pct > t.mean_rate + t.stddev_rate
ORDER BY cs.fraud_risk_score DESC;

COMMENT ON VIEW walmart_fraud.v_high_risk_customers IS 'Customers flagged as high-risk based on statistical thresholds';

-- ----------------------------------------------------------------------------
-- View: v_driver_customer_pairs
-- Description: Driver-customer pair analysis to detect collusion
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW walmart_fraud.v_driver_customer_pairs AS
SELECT
    o.driver_id,
    d.driver_name,
    o.customer_id,
    c.customer_name,
    COUNT(o.order_id) AS shared_orders,
    COUNT(CASE WHEN o.items_missing > 0 THEN 1 END) AS orders_with_missing,
    SUM(o.items_missing) AS total_items_missing,
    ROUND(SUM(o.order_amount), 2) AS total_order_value,
    ROUND(COUNT(CASE WHEN o.items_missing > 0 THEN 1 END)::DECIMAL / NULLIF(COUNT(o.order_id), 0) * 100, 2) AS missing_order_rate_pct
FROM walmart_fraud.orders o
JOIN walmart_fraud.drivers d ON o.driver_id = d.driver_id
JOIN walmart_fraud.customers c ON o.customer_id = c.customer_id
GROUP BY o.driver_id, d.driver_name, o.customer_id, c.customer_name
HAVING COUNT(o.order_id) >= 2  -- At least 2 shared orders
ORDER BY missing_order_rate_pct DESC, shared_orders DESC;

COMMENT ON VIEW walmart_fraud.v_driver_customer_pairs IS 'Driver-customer pair analysis to detect potential collusion';

-- ============================================================================
-- SUMMARY/DASHBOARD VIEWS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- View: v_fraud_summary_dashboard
-- Description: High-level summary metrics for dashboard
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW walmart_fraud.v_fraud_summary_dashboard AS
WITH order_summary AS (
    SELECT
        COUNT(*) AS total_orders,
        COUNT(CASE WHEN items_missing > 0 THEN 1 END) AS orders_with_missing,
        SUM(items_delivered) AS total_items_delivered,
        SUM(items_missing) AS total_items_missing,
        SUM(order_amount) AS total_order_value
    FROM walmart_fraud.orders
),
missing_value AS (
    SELECT SUM(p.price) AS total_missing_value
    FROM walmart_fraud.order_missing_items mi
    JOIN walmart_fraud.products p ON mi.product_id = p.product_id
),
entity_counts AS (
    SELECT
        (SELECT COUNT(*) FROM walmart_fraud.drivers) AS total_drivers,
        (SELECT COUNT(*) FROM walmart_fraud.customers) AS total_customers,
        (SELECT COUNT(*) FROM walmart_fraud.products) AS total_products,
        (SELECT COUNT(*) FROM walmart_fraud.regions) AS total_regions
)
SELECT
    os.total_orders,
    os.orders_with_missing,
    os.total_items_delivered,
    os.total_items_missing,
    ROUND(os.total_order_value, 2) AS total_order_value,
    COALESCE(mv.total_missing_value, 0) AS total_missing_value,
    ROUND(os.orders_with_missing::DECIMAL / NULLIF(os.total_orders, 0) * 100, 2) AS overall_missing_order_rate_pct,
    ROUND(os.total_items_missing::DECIMAL / NULLIF(os.total_items_delivered, 0) * 100, 2) AS overall_missing_item_rate_pct,
    ROUND(COALESCE(mv.total_missing_value, 0) / NULLIF(os.total_order_value, 0) * 100, 2) AS overall_missing_value_rate_pct,
    ec.total_drivers,
    ec.total_customers,
    ec.total_products,
    ec.total_regions
FROM order_summary os
CROSS JOIN missing_value mv
CROSS JOIN entity_counts ec;

COMMENT ON VIEW walmart_fraud.v_fraud_summary_dashboard IS 'High-level summary metrics for fraud detection dashboard';

-- ============================================================================
-- END OF VIEW CREATION
-- ============================================================================
