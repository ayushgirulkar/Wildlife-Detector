CREATE DATABASE wildlife_db;

USE wildlife_db;

CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100),
    password VARCHAR(100)
);

CREATE TABLE alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    label VARCHAR(100),
    location VARCHAR(100),
    latitude DOUBLE,
    longitude DOUBLE,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default admin
INSERT INTO admin (username, password) VALUES ('admin', 'admin123');
