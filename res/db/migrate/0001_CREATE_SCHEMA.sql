-- only for test purpose; remove when actually used
CREATE TABLE drone (
    id int,
    drone_id char(4),
    optimized bool,
    glitched bool,
    trusted_users text,
    last_activity datetime
);