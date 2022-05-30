CREATE TABLE forbidden_word (
    id VARCHAR(36) PRIMARY KEY,
    regex TEXT NOT NULL
);

INSERT INTO forbidden_word (id, regex) VALUES 
    ('think', 't+h+i+n+k+'), 
    ('thought', 't+h+o+u+g+h+t+'), 
    ('morning', 'm+o+r+n+i+n+g+');