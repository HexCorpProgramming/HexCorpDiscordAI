CREATE TABLE timer (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    drone_id CHAR(4) NOT NULL,
    mode VARCHAR(64) NOT NULL,
    end_time DATETIME NOT NULL,
    FOREIGN KEY(drone_id) REFERENCES drone(drone_id)
);