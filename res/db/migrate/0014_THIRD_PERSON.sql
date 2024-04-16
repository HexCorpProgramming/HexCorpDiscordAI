-- Recreate the drone table with the new column "third_person_enforcement".
CREATE TABLE drone2 (
    discord_id UNSIGNED INT PRIMARY KEY,
    drone_id CHAR(4) NOT NULL UNIQUE,
    optimized BOOL NOT NULL DEFAULT 0,
    glitched BOOL NOT NULL DEFAULT 0,
    trusted_users TEXT NOT NULL DEFAULT "",
    last_activity DATETIME,
    id_prepending BOOL NOT NULL DEFAULT 0,
    identity_enforcement BOOL NOT NULL DEFAULT 0,
    third_person_enforcement BOOL NOT NULL DEFAULT 0,
    can_self_configure BOOL NOT NULL DEFAULT 1,
    temporary_until DATETIME,
    is_battery_powered BOOL NOT NULL DEFAULT 0,
    battery_type_id INT NOT NULL DEFAULT 2,
    battery_minutes UNSIGNED INTEGER NOT NULL DEFAULT 480,
    free_storage BOOL NOT NULL DEFAULT 0,
    associate_name TEXT NOT NULL DEFAULT "",
    FOREIGN KEY (battery_type_id) REFERENCES battery_types(id)
);


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
        0,
        can_self_configure,
        temporary_until,
        is_battery_powered,
        battery_type_id,
        battery_minutes,
        free_storage,
        associate_name
    FROM drone;

-- Delete the old drones table and rename the new one.
DROP TABLE drone;
ALTER TABLE drone2 RENAME TO drone;
