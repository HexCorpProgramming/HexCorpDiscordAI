CREATE TABLE drone (
    id VARCHAR(36) PRIMARY KEY,
    drone_id CHAR(4) UNIQUE,
    optimized BOOL,
    glitched BOOL,
    trusted_users TEXT,
    last_activity DATETIME
);

CREATE TABLE storage (
    id VARCHAR(36) PRIMARY KEY,
    stored_by CHAR(4),
    target_id CHAR(4),
    purpose VARCHAR(255),
    roles TEXT,
    release_time DATETIME,
    FOREIGN KEY(target_id) REFERENCES drone(drone_id)
);

CREATE TABLE drone_order (
    id VARCHAR(36) PRIMARY KEY,
    drone_id CHAR(4),
    protocol VARCHAR(255),
    finish_time DATETIME,
    FOREIGN KEY(drone_id) REFERENCES drone(drone_id)
);