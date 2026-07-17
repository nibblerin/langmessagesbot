-- Пользователи бота
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 0,      
    interval_minutes INTEGER NOT NULL DEFAULT 60, 
    last_sent_at INTEGER NOT NULL DEFAULT 0    
);

-- Немецкие слова
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,   
    plural TEXT,                 -- может быть NULL, если мн.ч. нет/не нужно
    translation TEXT NOT NULL    -- перевод на русский
);

-- Текущее "слово дня"
-- Обновляется не чаще, чем раз в MIN_INTERVAL, чтобы экономить запросы к LLM
CREATE TABLE IF NOT EXISTS current_word (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    word_id INTEGER NOT NULL,
    word TEXT NOT NULL,
    plural TEXT,
    translation TEXT NOT NULL,
    sentence_de TEXT NOT NULL,
    sentence_ru TEXT NOT NULL,
    generated_at INTEGER NOT NULL,
    FOREIGN KEY(word_id) REFERENCES words(id)
);

-- Отправленные сообщения со словом - нужны, чтобы чистить старые и не засорять чат
CREATE TABLE IF NOT EXISTS sent_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    sent_at INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);