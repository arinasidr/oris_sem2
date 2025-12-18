CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    session_start_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE subjects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    deadline DATE NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at DATE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

CREATE TABLE grades (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL,
    value INTEGER NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE subject_tags (
    subject_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    UNIQUE (subject_id, tag_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);
