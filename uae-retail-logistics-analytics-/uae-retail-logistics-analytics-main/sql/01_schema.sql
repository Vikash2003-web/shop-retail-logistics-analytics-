-- ============================================================================
-- UAE Retail & Logistics Analytics — Schema Definition
-- Star-schema style: fact tables (orders, order_items, deliveries)
-- surrounded by dimension tables (customers, products, suppliers, warehouses)
-- ============================================================================

DROP TABLE IF EXISTS deliveries;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS warehouses;
DROP TABLE IF EXISTS customers;

-- Dimension: Customers
CREATE TABLE customers (
    customer_id      INTEGER PRIMARY KEY,
    customer_name    TEXT,
    email            TEXT,
    emirate          TEXT,
    city             TEXT,
    signup_date      DATE,
    customer_segment TEXT,
    age              INTEGER,
    gender           TEXT
);

-- Dimension: Suppliers
CREATE TABLE suppliers (
    supplier_id       INTEGER PRIMARY KEY,
    supplier_name     TEXT,
    country           TEXT,
    avg_lead_time_days REAL
);

-- Dimension: Products
CREATE TABLE products (
    product_id      INTEGER PRIMARY KEY,
    product_name    TEXT,
    category        TEXT,
    subcategory     TEXT,
    unit_price_aed  REAL,
    supplier_id     INTEGER REFERENCES suppliers(supplier_id)
);

-- Dimension: Warehouses (one per emirate)
CREATE TABLE warehouses (
    warehouse_id INTEGER PRIMARY KEY,
    emirate      TEXT,
    city         TEXT
);

-- Fact: Orders (order header)
CREATE TABLE orders (
    order_id       INTEGER PRIMARY KEY,
    customer_id    INTEGER REFERENCES customers(customer_id),
    order_date     DATE,
    channel        TEXT,
    payment_method TEXT,
    warehouse_id   INTEGER REFERENCES warehouses(warehouse_id)
);

-- Fact: Order Items (order line items — grain = 1 product per order)
CREATE TABLE order_items (
    order_item_id  INTEGER PRIMARY KEY,
    order_id       INTEGER REFERENCES orders(order_id),
    product_id     INTEGER REFERENCES products(product_id),
    quantity       INTEGER,
    unit_price_aed REAL,
    discount_pct   REAL,
    line_total_aed REAL
);

-- Fact: Deliveries (only for online orders)
CREATE TABLE deliveries (
    delivery_id     INTEGER PRIMARY KEY,
    order_id        INTEGER REFERENCES orders(order_id),
    warehouse_id    INTEGER REFERENCES warehouses(warehouse_id),
    courier         TEXT,
    dispatch_date   DATETIME,
    promised_date   DATETIME,
    delivery_date   DATETIME,
    delivery_status TEXT,
    on_time         INTEGER  -- boolean 0/1
);

-- Helpful indexes for analytical queries
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_items_order ON order_items(order_id);
CREATE INDEX idx_items_product ON order_items(product_id);
CREATE INDEX idx_deliveries_order ON deliveries(order_id);
