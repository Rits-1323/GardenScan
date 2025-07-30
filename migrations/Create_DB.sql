CREATE TABLE gardens(garden_id INT PRIMARY KEY AUTO_INCREMENT,

garden_name VARCHAR(255) NOT NULL,

adult_price DECIMAL(10, 2) NOT NULL,

child_price DECIMAL(10, 2) NOT NULL,

account_number CHAR(16) NOT NULL

);



CREATE TABLE tickets(ticket_id INT PRIMARY KEY AUTO_INCREMENT,

garden_id INT NOT NULL,

visitor_name VARCHAR(255) NOT NULL,

num_adults INT NOT NULL,

num_children INT NOT NULL,

total_amount DECIMAL(10, 2) NOT NULL,

phone VARCHAR(20) NOT NULL,

visit_date DATE NOT NULL,

payment_status VARCHAR(50) DEFAULT 'pending',

created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY (garden_id) REFERENCES gardens(garden_id)

);