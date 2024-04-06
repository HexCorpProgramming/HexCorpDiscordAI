-- Sqlite does not support adding and removing foreign keys, so re-create the tables.

-- Recreate the drone table first because the id column is being renamed to discord_id.

CREATE TABLE drone2 (
    discord_id UNSIGNED INT PRIMARY KEY,
    drone_id CHAR(4) UNIQUE,
    optimized BOOL,
    glitched BOOL,
    trusted_users TEXT,
    last_activity DATETIME,
    id_prepending BOOL DEFAULT 0,
    identity_enforcement BOOL DEFAULT 0,
    can_self_configure BOOL DEFAULT 1,
    temporary_until DATETIME,
    is_battery_powered BOOL DEFAULT 0,
    battery_minutes UNSIGNED INTEGER DEFAULT 480,
    free_storage BOOL DEFAULT 0,
    associate_name TEXT);

INSERT INTO drone2 SELECT * FROM drone;
DROP TABLE drone;
ALTER TABLE drone2 RENAME TO drone;

-- Create new tables with foreign keys referencing the user's Discord ID, not drone ID.

CREATE TABLE storage2 (
    id VARCHAR(36) PRIMARY KEY,
    -- stored_by is nullable because the Hive Mxtress does not have a drone record.
    stored_by INT UNSIGNED,
    target_id INT UNSIGNED NOT NULL,
    purpose VARCHAR(255) NOT NULL,
    roles TEXT NOT NULL,
    release_time DATETIME NOT NULL,
    FOREIGN KEY (stored_by) REFERENCES drone(discord_id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES drone(discord_id) ON DELETE CASCADE
);

CREATE TABLE drone_order2 (
    id VARCHAR(36) PRIMARY KEY,
    discord_id INT UNSIGNED NOT NULL,
    protocol VARCHAR(255) NOT NULL,
    finish_time DATETIME NOT NULL,
    FOREIGN KEY (discord_id) REFERENCES drone(discord_id) ON DELETE CASCADE
);

CREATE TABLE timer2 (
    id VARCHAR(36) PRIMARY KEY NOT NULL,
    discord_id INT UNSIGNED NOT NULL,
    mode VARCHAR(64) NOT NULL,
    end_time DATETIME NOT NULL,
    FOREIGN KEY (discord_id) REFERENCES drone(discord_id) ON DELETE CASCADE
);

-- Fill the new tables with data from the old tables.

INSERT INTO storage2 SELECT storage.id, d1.discord_id, d2.discord_id, purpose, roles, release_time FROM storage
    INNER JOIN drone AS d1 ON d1.drone_id = storage.stored_by
    INNER JOIN drone AS d2 ON d2.drone_id = storage.target_id;

INSERT INTO drone_order2 SELECT drone_order.id, d.discord_id, protocol, finish_time FROM drone_order
    INNER JOIN drone AS d ON d.drone_id = drone_order.drone_id;

INSERT INTO timer2 SELECT timer.id, d.discord_id, mode, end_time FROM timer
    INNER JOIN drone AS d ON d.drone_id = timer.drone_id;

-- Drop old tables.

DROP TABLE storage;
DROP TABLE drone_order;
DROP TABLE timer;

-- Rename tables.

ALTER TABLE storage2 RENAME TO storage;
ALTER TABLE drone_order2 RENAME TO drone_order;
ALTER TABLE timer2 RENAME TO timer;
