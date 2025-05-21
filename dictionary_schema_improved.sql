-- Cập nhật cấu trúc cơ sở dữ liệu để thêm trường nguồn gốc

CREATE TABLE words (
    id SERIAL PRIMARY KEY,
    word VARCHAR(100) NOT NULL,
    pronunciation VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_word ON words(word);

CREATE TABLE parts_of_speech (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE UNIQUE INDEX idx_pos_name ON parts_of_speech(name);

CREATE TABLE word_definitions (
    id SERIAL PRIMARY KEY,
    word_id INTEGER REFERENCES words(id),
    part_of_speech_id INTEGER REFERENCES parts_of_speech(id),
    definition_en TEXT,
    definition_vi TEXT,
    context VARCHAR(100),
    source VARCHAR(100),  -- Nguồn gốc định nghĩa
    source_url VARCHAR(255),  -- URL nguồn nếu có
    confidence SMALLINT DEFAULT 100,  -- Độ tin cậy (0-100)
    UNIQUE(word_id, part_of_speech_id, definition_vi)
);

CREATE INDEX idx_word_def_word_id ON word_definitions(word_id);

CREATE TABLE examples (
    id SERIAL PRIMARY KEY,
    word_definition_id INTEGER REFERENCES word_definitions(id),
    example_en TEXT NOT NULL,
    example_vi TEXT,
    source VARCHAR(100),
    source_url VARCHAR(255)
);

CREATE INDEX idx_examples_def_id ON examples(word_definition_id);

CREATE TABLE word_forms (
    id SERIAL PRIMARY KEY,
    word_id INTEGER REFERENCES words(id),
    form_type VARCHAR(50) NOT NULL, -- 'plural', 'past_tense', etc.
    form VARCHAR(100) NOT NULL
);

CREATE INDEX idx_word_forms_word_id ON word_forms(word_id);

CREATE TABLE synonyms (
    id SERIAL PRIMARY KEY,
    word_definition_id INTEGER REFERENCES word_definitions(id),
    synonym_word_id INTEGER REFERENCES words(id)
);

CREATE TABLE antonyms (
    id SERIAL PRIMARY KEY,
    word_definition_id INTEGER REFERENCES word_definitions(id),
    antonym_word_id INTEGER REFERENCES words(id)
);

CREATE TABLE phrases (
    id SERIAL PRIMARY KEY,
    phrase VARCHAR(255) NOT NULL,
    meaning TEXT,
    language VARCHAR(10) DEFAULT 'en'
);

CREATE TABLE word_phrases (
    word_id INTEGER REFERENCES words(id),
    phrase_id INTEGER REFERENCES phrases(id),
    PRIMARY KEY (word_id, phrase_id)
);

-- Bảng mới để lưu trữ nguồn dữ liệu từ điển
CREATE TABLE dictionary_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    url VARCHAR(255),
    enabled BOOLEAN DEFAULT TRUE,
    priority SMALLINT DEFAULT 50,  -- Mức độ ưu tiên (cao hơn = ưu tiên hơn)
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Thêm các nguồn dữ liệu mặc định
INSERT INTO dictionary_sources (name, description, priority) VALUES 
('StarDict-AV', 'StarDict English-Vietnamese Dictionary', 90),
('OpenDict-EV', 'Open Dictionary English-Vietnamese', 80),
('EVDict', 'EVDict English-Vietnamese Dictionary', 70),
('FreeDict-EnVi', 'FreeDict English-Vietnamese Dictionary', 60),
('Wiktionary-VI', 'Vietnamese Wiktionary', 50),
('Local-AV', 'Local English-Vietnamese Dictionary', 40),
('Oxford', 'Oxford Dictionary', 30),
('WordNet', 'Princeton WordNet', 20),
('Wiktionary-EN', 'English Wiktionary', 10);

-- Bảng mới để lưu trữ thông tin người dùng
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    email VARCHAR(100) UNIQUE,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Bảng đóng góp/chỉnh sửa từ người dùng
CREATE TABLE user_contributions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    word_id INTEGER REFERENCES words(id),
    type VARCHAR(50) NOT NULL, -- 'definition', 'example', 'pronunciation', etc.
    old_value TEXT,
    new_value TEXT,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by INTEGER REFERENCES users(id)
);