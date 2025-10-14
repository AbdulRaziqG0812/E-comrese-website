CREATE DATABASE e_comrece;
USE e_comrece;

CREATE TABLE perfumes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    image VARCHAR(200) DEFAULT 'default.jpg',
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    sale_price DECIMAL(10,2) DEFAULT 0.00,
    stock INT DEFAULT 0,
    category VARCHAR(20) DEFAULT 'Unisex', 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    city VARCHAR(100),
    country VARCHAR(100),
    postal VARCHAR(20),
    address TEXT,
    items TEXT,        
    total FLOAT,
    payment_method VARCHAR(50),
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
