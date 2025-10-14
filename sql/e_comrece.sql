create DATABASE e_comrece;
use e_comrece;

CREATE TABLE perfumes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    image VARCHAR(200),
    description TEXT,
    price DECIMAL(10,2),
    sale_price DECIMAL(10,2),
    stock INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
