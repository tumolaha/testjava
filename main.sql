CREATE TABLE IF NOT EXISTS english_vietnamese (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    english_word VARCHAR(255) NOT NULL,
    vietnamese_meaning TEXT NOT NULL,
    word_type VARCHAR(50),
    pronunciation VARCHAR(255),
    example TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vietnamese_english (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vietnamese_word VARCHAR(255) NOT NULL,
    english_meaning TEXT NOT NULL,
    word_type VARCHAR(50),
    example TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_english_word ON english_vietnamese(english_word);
CREATE INDEX idx_vietnamese_word ON vietnamese_english(vietnamese_word);