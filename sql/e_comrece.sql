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
