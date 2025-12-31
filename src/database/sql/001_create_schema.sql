-- ============================================================================
-- Walmart Delivery Fraud Detection - Database Schema
-- ============================================================================
-- Purpose: Create normalized schema for fraud detection analysis
-- Database: PostgreSQL 14+
-- Author: Data Engineering Team
-- Created: 2025-12-31
-- ============================================================================

-- Drop existing objects if they exist (for clean re-runs)
DROP SCHEMA IF EXISTS walmart_fraud CASCADE;

-- Create dedicated schema for fraud detection
CREATE SCHEMA walmart_fraud;

-- Set search path for this session
SET search_path TO walmart_fraud, public;

-- ============================================================================
-- REFERENCE/DIMENSION TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: regions
-- Description: Lookup table for delivery regions in Central Florida
-- ----------------------------------------------------------------------------
CREATE TABLE walmart_fraud.regions (
    region_id       SERIAL PRIMARY KEY,
    region_name     VARCHAR(50) NOT NULL UNIQUE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE walmart_fraud.regions IS 'Lookup table for Central Florida delivery regions';
COMMENT ON COLUMN walmart_fraud.regions.region_name IS 'Name of the delivery region (e.g., Winter Park, Orlando)';

-- Insert known regions
INSERT INTO walmart_fraud.regions (region_name) VALUES
    ('Altamonte Springs'),
    ('Apopka'),
    ('Clermont'),
    ('Kissimmee'),
    ('Orlando'),
    ('Sanford'),
    ('Winter Park');

-- ----------------------------------------------------------------------------
-- Table: product_categories
-- Description: Lookup table for product categories
-- ----------------------------------------------------------------------------
CREATE TABLE walmart_fraud.product_categories (
    category_id     SERIAL PRIMARY KEY,
    category_name   VARCHAR(50) NOT NULL UNIQUE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE walmart_fraud.product_categories IS 'Lookup table for product categories';

-- Insert known categories
INSERT INTO walmart_fraud.product_categories (category_name) VALUES
    ('Bakery'),
    ('Beverages'),
    ('Dairy'),
    ('Electronics'),
    ('Frozen'),
    ('Household'),
    ('Pantry'),
    ('Personal Care'),
    ('Produce'),
    ('Snacks'),
    ('Supermarket');

-- ============================================================================
-- CORE ENTITY TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: customers
-- Description: Customer master data
-- Source: customers_data.csv
-- ----------------------------------------------------------------------------
CREATE TABLE walmart_fraud.customers (
    customer_id     VARCHAR(20) PRIMARY KEY,
    customer_name   VARCHAR(100) NOT NULL,
    customer_age    SMALLINT NOT NULL CHECK (customer_age >= 0 AND customer_age <= 150),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE walmart_fraud.customers IS 'Customer master data from customers_data.csv';
COMMENT ON COLUMN walmart_fraud.customers.customer_id IS 'Unique customer identifier (format: WCID####)';
COMMENT ON COLUMN walmart_fraud.customers.customer_name IS 'Full name of the customer';
COMMENT ON COLUMN walmart_fraud.customers.customer_age IS 'Age of the customer in years';

-- Create index for name searches
CREATE INDEX idx_customers_name ON walmart_fraud.customers (customer_name);
CREATE INDEX idx_customers_age ON walmart_fraud.customers (customer_age);

-- ----------------------------------------------------------------------------
-- Table: drivers
-- Description: Delivery driver master data
-- Source: drivers_data.csv
-- ----------------------------------------------------------------------------
CREATE TABLE walmart_fraud.drivers (
    driver_id       VARCHAR(20) PRIMARY KEY,
    driver_name     VARCHAR(100) NOT NULL,
    driver_age      SMALLINT NOT NULL CHECK (driver_age >= 18 AND driver_age <= 100),
    total_trips     INTEGER NOT NULL CHECK (total_trips >= 0),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE walmart_fraud.drivers IS 'Driver master data from drivers_data.csv';
COMMENT ON COLUMN walmart_fraud.drivers.driver_id IS 'Unique driver identifier (format: WDID#####)';
COMMENT ON COLUMN walmart_fraud.drivers.driver_name IS 'Full name of the driver';
COMMENT ON COLUMN walmart_fraud.drivers.driver_age IS 'Age of the driver in years';
COMMENT ON COLUMN walmart_fraud.drivers.total_trips IS 'Total number of trips completed in 2023';

-- Create indexes for analysis
CREATE INDEX idx_drivers_name ON walmart_fraud.drivers (driver_name);
CREATE INDEX idx_drivers_age ON walmart_fraud.drivers (driver_age);
CREATE INDEX idx_drivers_trips ON walmart_fraud.drivers (total_trips);

-- ----------------------------------------------------------------------------
-- Table: products
-- Description: Product catalog
-- Source: products_data.csv (note: source has typo 'produc_id')
-- ----------------------------------------------------------------------------
CREATE TABLE walmart_fraud.products (
    product_id      VARCHAR(30) PRIMARY KEY,
    product_name    VARCHAR(200) NOT NULL,
    category_id     INTEGER NOT NULL REFERENCES walmart_fraud.product_categories(category_id),
    price           DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE walmart_fraud.products IS 'Product catalog from products_data.csv';
COMMENT ON COLUMN walmart_fraud.products.product_id IS 'Unique product identifier (format: PWPX################)';
COMMENT ON COLUMN walmart_fraud.products.product_name IS 'Name of the product';
COMMENT ON COLUMN walmart_fraud.products.category_id IS 'Foreign key to product_categories';
COMMENT ON COLUMN walmart_fraud.products.price IS 'Unit price in USD';

-- Create indexes for analysis
CREATE INDEX idx_products_category ON walmart_fraud.products (category_id);
CREATE INDEX idx_products_price ON walmart_fraud.products (price);
CREATE INDEX idx_products_name ON walmart_fraud.products (product_name);

-- ============================================================================
-- FACT/TRANSACTION TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: orders
-- Description: Main order/delivery transaction table
-- Source: orders.csv
-- ----------------------------------------------------------------------------
CREATE TABLE walmart_fraud.orders (
    order_id            UUID PRIMARY KEY,
    order_date          DATE NOT NULL,
    order_amount        DECIMAL(12, 2) NOT NULL CHECK (order_amount >= 0),
    region_id           INTEGER NOT NULL REFERENCES walmart_fraud.regions(region_id),
    items_delivered     INTEGER NOT NULL CHECK (items_delivered >= 0),
    items_missing       INTEGER NOT NULL CHECK (items_missing >= 0),
    delivery_hour       TIME NOT NULL,
    driver_id           VARCHAR(20) NOT NULL REFERENCES walmart_fraud.drivers(driver_id),
    customer_id         VARCHAR(20) NOT NULL REFERENCES walmart_fraud.customers(customer_id),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Note: No constraint on items_missing <= items_delivered
    -- Anomalous cases where missing > delivered are fraud indicators to be analyzed
);

COMMENT ON TABLE walmart_fraud.orders IS 'Order and delivery transactions from orders.csv';
COMMENT ON COLUMN walmart_fraud.orders.order_id IS 'Unique order identifier (UUID format)';
COMMENT ON COLUMN walmart_fraud.orders.order_date IS 'Date of the order/delivery';
COMMENT ON COLUMN walmart_fraud.orders.order_amount IS 'Total order amount in USD';
COMMENT ON COLUMN walmart_fraud.orders.region_id IS 'Foreign key to regions lookup table';
COMMENT ON COLUMN walmart_fraud.orders.items_delivered IS 'Number of items delivered';
COMMENT ON COLUMN walmart_fraud.orders.items_missing IS 'Number of items reported missing';
COMMENT ON COLUMN walmart_fraud.orders.delivery_hour IS 'Time of delivery';
COMMENT ON COLUMN walmart_fraud.orders.driver_id IS 'Foreign key to drivers table';
COMMENT ON COLUMN walmart_fraud.orders.customer_id IS 'Foreign key to customers table';

-- Create indexes for foreign keys and common query patterns
CREATE INDEX idx_orders_date ON walmart_fraud.orders (order_date);
CREATE INDEX idx_orders_region ON walmart_fraud.orders (region_id);
CREATE INDEX idx_orders_driver ON walmart_fraud.orders (driver_id);
CREATE INDEX idx_orders_customer ON walmart_fraud.orders (customer_id);
CREATE INDEX idx_orders_delivery_hour ON walmart_fraud.orders (delivery_hour);
CREATE INDEX idx_orders_items_missing ON walmart_fraud.orders (items_missing) WHERE items_missing > 0;

-- Composite indexes for common query patterns in fraud analysis
CREATE INDEX idx_orders_driver_date ON walmart_fraud.orders (driver_id, order_date);
CREATE INDEX idx_orders_customer_date ON walmart_fraud.orders (customer_id, order_date);
CREATE INDEX idx_orders_region_date ON walmart_fraud.orders (region_id, order_date);

-- ----------------------------------------------------------------------------
-- Table: order_missing_items
-- Description: Normalized table for missing items per order
-- Source: missing_items_data.csv (normalized from sparse 3-column structure)
-- ----------------------------------------------------------------------------
CREATE TABLE walmart_fraud.order_missing_items (
    missing_item_id     SERIAL PRIMARY KEY,
    order_id            UUID NOT NULL REFERENCES walmart_fraud.orders(order_id),
    product_id          VARCHAR(30) NOT NULL REFERENCES walmart_fraud.products(product_id),
    item_position       SMALLINT NOT NULL CHECK (item_position BETWEEN 1 AND 3),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Ensure no duplicate product in same position for an order
    CONSTRAINT uq_order_product_position UNIQUE (order_id, item_position)
);

COMMENT ON TABLE walmart_fraud.order_missing_items IS 'Normalized missing items from missing_items_data.csv';
COMMENT ON COLUMN walmart_fraud.order_missing_items.order_id IS 'Foreign key to orders table';
COMMENT ON COLUMN walmart_fraud.order_missing_items.product_id IS 'Foreign key to products table';
COMMENT ON COLUMN walmart_fraud.order_missing_items.item_position IS 'Original position (1, 2, or 3) from source data';

-- Create indexes for analysis
CREATE INDEX idx_missing_items_order ON walmart_fraud.order_missing_items (order_id);
CREATE INDEX idx_missing_items_product ON walmart_fraud.order_missing_items (product_id);

-- Composite index for product fraud analysis
CREATE INDEX idx_missing_items_product_order ON walmart_fraud.order_missing_items (product_id, order_id);

-- ============================================================================
-- STAGING TABLES (for data loading)
-- ============================================================================

-- Staging table for customers (direct CSV load)
CREATE TABLE walmart_fraud.stg_customers (
    customer_id     VARCHAR(20),
    customer_name   VARCHAR(100),
    customer_age    VARCHAR(10)
);

-- Staging table for drivers (direct CSV load)
CREATE TABLE walmart_fraud.stg_drivers (
    driver_id       VARCHAR(20),
    driver_name     VARCHAR(100),
    age             VARCHAR(10),
    trips           VARCHAR(20)
);

-- Staging table for products (direct CSV load with typo column name)
CREATE TABLE walmart_fraud.stg_products (
    produc_id       VARCHAR(30),
    product_name    VARCHAR(200),
    category        VARCHAR(50),
    price           VARCHAR(20)
);

-- Staging table for orders (direct CSV load)
CREATE TABLE walmart_fraud.stg_orders (
    date            VARCHAR(20),
    order_id        VARCHAR(50),
    order_amount    VARCHAR(20),
    region          VARCHAR(50),
    items_delivered VARCHAR(10),
    items_missing   VARCHAR(10),
    delivery_hour   VARCHAR(20),
    driver_id       VARCHAR(20),
    customer_id     VARCHAR(20)
);

-- Staging table for missing items (direct CSV load)
CREATE TABLE walmart_fraud.stg_missing_items (
    order_id        VARCHAR(50),
    product_id_1    VARCHAR(30),
    product_id_2    VARCHAR(30),
    product_id_3    VARCHAR(30)
);

-- ============================================================================
-- AUDIT/METADATA TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: etl_load_log
-- Description: Track data loading operations
-- ----------------------------------------------------------------------------
CREATE TABLE walmart_fraud.etl_load_log (
    load_id         SERIAL PRIMARY KEY,
    table_name      VARCHAR(100) NOT NULL,
    load_start      TIMESTAMP WITH TIME ZONE NOT NULL,
    load_end        TIMESTAMP WITH TIME ZONE,
    rows_loaded     INTEGER,
    status          VARCHAR(20) CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED')),
    error_message   TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE walmart_fraud.etl_load_log IS 'Audit log for ETL data loading operations';

-- ============================================================================
-- GRANT PERMISSIONS (adjust as needed for your environment)
-- ============================================================================

-- Example: Grant read access to analysts
-- GRANT USAGE ON SCHEMA walmart_fraud TO analyst_role;
-- GRANT SELECT ON ALL TABLES IN SCHEMA walmart_fraud TO analyst_role;

-- ============================================================================
-- END OF SCHEMA CREATION
-- ============================================================================
