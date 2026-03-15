DROP TABLE IF EXISTS order_products CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP NULL
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    amount NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP NULL
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    price NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP NULL
);

CREATE TABLE order_products (
    order_id INT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (order_id, product_id)
);

CREATE INDEX idx_customers_created_at ON customers(created_at);
CREATE INDEX idx_customers_deleted_at ON customers(deleted_at);

CREATE INDEX idx_orders_updated_at ON orders(updated_at);
CREATE INDEX idx_orders_deleted_at ON orders(deleted_at);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);

CREATE INDEX idx_products_updated_at ON products(updated_at);
CREATE INDEX idx_products_deleted_at ON products(deleted_at);

CREATE INDEX idx_order_products_order_id ON order_products(order_id);
CREATE INDEX idx_order_products_product_id ON order_products(product_id);

INSERT INTO customers (name, email) VALUES
('Ivan Petrov', 'ivan@example.com'),
('Maria Sidorova', 'maria@example.com');

INSERT INTO products (name, category, price) VALUES
('Laptop', 'Electronics', 75000.00),
('Mouse', 'Accessories', 1500.00),
('Monitor', 'Electronics', 35000.00),
('Keyboard', 'Accessories', 5000.00);

INSERT INTO orders (customer_id, status, amount) VALUES
(1, 'completed', 76500.00),
(1, 'pending', 5000.00),
(2, 'shipped', 35000.00);

INSERT INTO order_products (order_id, product_id, quantity) VALUES
(1, 1, 1),
(1, 2, 1),
(2, 4, 1),
(3, 3, 1);