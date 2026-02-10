CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT,
    email TEXT UNIQUE,
    mobile TEXT,
    country TEXT,
    password TEXT,
    otp TEXT,
    is_verified INTEGER DEFAULT 0,
    reset_token TEXT
);
