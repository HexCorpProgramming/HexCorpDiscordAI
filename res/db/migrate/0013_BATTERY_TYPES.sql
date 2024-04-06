-- Create a table to hold possible drone battery configurations.
CREATE TABLE battery_types (
    id INTEGER PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    capacity INT NOT NULL,
    recharge_rate INT NOT NULL
);

-- Insert the standard battery types.
INSERT INTO battery_types VALUES
    (1, "Low", 240, 30),
    (2, "Medium", 480, 120),
    (3, "High", 720, 360);

-- Recreate the drone table with the new column and foreign key constraint.
CREATE TABLE drone2 (
    discord_id UNSIGNED INT PRIMARY KEY,
    drone_id CHAR(4) NOT NULL UNIQUE,
    optimized BOOL NOT NULL DEFAULT 0,
    glitched BOOL NOT NULL DEFAULT 0,
    trusted_users TEXT NOT NULL DEFAULT "",
    last_activity DATETIME,
    id_prepending BOOL NOT NULL DEFAULT 0,
    identity_enforcement BOOL NOT NULL DEFAULT 0,
    can_self_configure BOOL NOT NULL DEFAULT 1,
    temporary_until DATETIME,
    is_battery_powered BOOL NOT NULL DEFAULT 0,
    battery_type_id INT NOT NULL DEFAULT 2,
    battery_minutes UNSIGNED INTEGER NOT NULL DEFAULT 480,
    free_storage BOOL NOT NULL DEFAULT 0,
    associate_name TEXT NOT NULL DEFAULT "",
    FOREIGN KEY (battery_type_id) REFERENCES battery_types(id)
);

-- Patch up any NULL entries.
UPDATE drone SET associate_name = drone_id WHERE associate_name IS NULL;

-- Copy the drone records into the new table.
INSERT INTO drone2
    SELECT
        discord_id,
        drone_id,
        optimized,
        glitched,
        trusted_users,
        last_activity,
        id_prepending,
        identity_enforcement,
        can_self_configure,
        temporary_until,
        is_battery_powered,
        2,
        battery_minutes,
        free_storage,
        associate_name
    FROM drone;

-- Delete the old drones table and rename the new one.
DROP TABLE drone;
ALTER TABLE drone2 RENAME TO drone;
