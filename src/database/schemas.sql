-- Walmart Fraud Detection Database Schema
-- PostgreSQL DDL for all tables

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS missing_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS drivers CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS products CASCADE;

-- Customers table
CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    customer_age INTEGER CHECK (customer_age > 0)
);

CREATE INDEX idx_customers_age ON customers(customer_age);

-- Drivers table
CREATE TABLE drivers (
    driver_id VARCHAR(20) PRIMARY KEY,
    driver_name VARCHAR(100) NOT NULL,
    age INTEGER CHECK (age >= 18),
    trips INTEGER DEFAULT 0 CHECK (trips >= 0)
);

CREATE INDEX idx_drivers_age ON drivers(age);
CREATE INDEX idx_drivers_trips ON drivers(trips);

-- Products table
CREATE TABLE products (
    product_id VARCHAR(30) PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2) CHECK (price >= 0)
);

CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_price ON products(price);

-- Orders table (fact table)
CREATE TABLE orders (
    order_id VARCHAR(50) PRIMARY KEY,
    order_date DATE NOT NULL,
    order_amount DECIMAL(10, 2) CHECK (order_amount >= 0),
    region VARCHAR(50) NOT NULL,
    items_delivered INTEGER DEFAULT 0 CHECK (items_delivered >= 0),
    items_missing INTEGER DEFAULT 0 CHECK (items_missing >= 0),
    delivery_hour TIME,
    driver_id VARCHAR(20) REFERENCES drivers(driver_id),
    customer_id VARCHAR(20) REFERENCES customers(customer_id)
);

CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_region ON orders(region);
CREATE INDEX idx_orders_driver ON orders(driver_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_items_missing ON orders(items_missing);

-- Missing items table (links orders to products)
CREATE TABLE missing_items (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) REFERENCES orders(order_id),
    product_id_1 VARCHAR(30) REFERENCES products(product_id),
    product_id_2 VARCHAR(30) REFERENCES products(product_id),
    product_id_3 VARCHAR(30) REFERENCES products(product_id)
);

CREATE INDEX idx_missing_items_order ON missing_items(order_id);
CREATE INDEX idx_missing_items_product1 ON missing_items(product_id_1);

-- Analytical views

-- Driver fraud rate view
CREATE OR REPLACE VIEW vw_driver_fraud_stats AS
SELECT
    d.driver_id,
    d.driver_name,
    d.age,
    d.trips,
    COUNT(o.order_id) AS total_orders,
    SUM(o.items_missing) AS total_items_missing,
    SUM(o.items_delivered) AS total_items_delivered,
    ROUND(
        CASE
            WHEN SUM(o.items_delivered + o.items_missing) > 0
            THEN (SUM(o.items_missing)::DECIMAL / SUM(o.items_delivered + o.items_missing)) * 100
            ELSE 0
        END, 2
    ) AS missing_rate_pct,
    COUNT(CASE WHEN o.items_missing > 0 THEN 1 END) AS orders_with_missing
FROM drivers d
LEFT JOIN orders o ON d.driver_id = o.driver_id
GROUP BY d.driver_id, d.driver_name, d.age, d.trips;

-- Customer fraud rate view
CREATE OR REPLACE VIEW vw_customer_fraud_stats AS
SELECT
    c.customer_id,
    c.customer_name,
    c.customer_age,
    COUNT(o.order_id) AS total_orders,
    SUM(o.items_missing) AS total_items_missing,
    SUM(o.order_amount) AS total_spent,
    ROUND(
        CASE
            WHEN SUM(o.items_delivered + o.items_missing) > 0
            THEN (SUM(o.items_missing)::DECIMAL / SUM(o.items_delivered + o.items_missing)) * 100
            ELSE 0
        END, 2
    ) AS missing_rate_pct,
    COUNT(CASE WHEN o.items_missing > 0 THEN 1 END) AS orders_with_missing
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name, c.customer_age;

-- Regional analysis view
CREATE OR REPLACE VIEW vw_regional_stats AS
SELECT
    region,
    COUNT(order_id) AS total_orders,
    SUM(items_missing) AS total_items_missing,
    SUM(items_delivered) AS total_items_delivered,
    SUM(order_amount) AS total_revenue,
    ROUND(AVG(order_amount), 2) AS avg_order_amount,
    ROUND(
        CASE
            WHEN SUM(items_delivered + items_missing) > 0
            THEN (SUM(items_missing)::DECIMAL / SUM(items_delivered + items_missing)) * 100
            ELSE 0
        END, 2
    ) AS missing_rate_pct
FROM orders
GROUP BY region;

-- Monthly trend view
CREATE OR REPLACE VIEW vw_monthly_trends AS
SELECT
    DATE_TRUNC('month', order_date) AS month,
    COUNT(order_id) AS total_orders,
    SUM(items_missing) AS total_items_missing,
    SUM(order_amount) AS total_revenue,
    ROUND(
        CASE
            WHEN SUM(items_delivered + items_missing) > 0
            THEN (SUM(items_missing)::DECIMAL / SUM(items_delivered + items_missing)) * 100
            ELSE 0
        END, 2
    ) AS missing_rate_pct
FROM orders
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month;

-- Hourly pattern view
CREATE OR REPLACE VIEW vw_hourly_patterns AS
SELECT
    EXTRACT(HOUR FROM delivery_hour) AS hour_of_day,
    COUNT(order_id) AS total_orders,
    SUM(items_missing) AS total_items_missing,
    ROUND(
        CASE
            WHEN SUM(items_delivered + items_missing) > 0
            THEN (SUM(items_missing)::DECIMAL / SUM(items_delivered + items_missing)) * 100
            ELSE 0
        END, 2
    ) AS missing_rate_pct
FROM orders
WHERE delivery_hour IS NOT NULL
GROUP BY EXTRACT(HOUR FROM delivery_hour)
ORDER BY hour_of_day;
