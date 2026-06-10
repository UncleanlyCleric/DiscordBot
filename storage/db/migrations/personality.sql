CREATE TABLE IF NOT EXISTS personality_abstracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS personality_abstract_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    abstract_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    FOREIGN KEY (abstract_id)
        REFERENCES personality_abstracts(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_personality_abstracts_name
ON personality_abstracts(name);

CREATE INDEX IF NOT EXISTS idx_personality_items_abstract
ON personality_abstract_items(abstract_id);