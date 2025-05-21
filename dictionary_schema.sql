CREATE TABLE words (
    id SERIAL PRIMARY KEY,
    word VARCHAR(100) NOT NULL,
    pronunciation VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE parts_of_speech (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE word_definitions (
    id SERIAL PRIMARY KEY,
    word_id INTEGER REFERENCES words(id),
    part_of_speech_id INTEGER REFERENCES parts_of_speech(id),
    definition_en TEXT,
    definition_vi TEXT,
    context VARCHAR(100),
    source VARCHAR(100),
    UNIQUE(word_id, part_of_speech_id, definition_vi)
);

CREATE TABLE examples (
    id SERIAL PRIMARY KEY,
    word_definition_id INTEGER REFERENCES word_definitions(id),
    example_en TEXT NOT NULL,
    example_vi TEXT,
    source VARCHAR(100)
);

CREATE TABLE word_forms (
    id SERIAL PRIMARY KEY,
    word_id INTEGER REFERENCES words(id),
    form_type VARCHAR(50) NOT NULL, -- 'plural', 'past_tense', etc.
    form VARCHAR(100) NOT NULL
);

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