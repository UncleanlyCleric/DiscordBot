-- =========================================================
-- GUILDS
-- =========================================================

CREATE TABLE IF NOT EXISTS guilds (
    guild_id   INTEGER PRIMARY KEY,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- GUILD SETTINGS (CORE CONFIG TABLE)
-- =========================================================

CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER PRIMARY KEY,

    -- MUSIC SETTINGS
    music_volume              INTEGER DEFAULT 75,
    music_autoplay            INTEGER DEFAULT 1,
    music_247                 INTEGER DEFAULT 0,
    music_idle_minutes        INTEGER DEFAULT 10,

    -- MARKOV SETTINGS
    markov_enabled           INTEGER DEFAULT 1,
    markov_chance            REAL DEFAULT 0.5,
    markov_cooldown_minutes  INTEGER DEFAULT 15,
    markov_min_words         INTEGER DEFAULT 3,
    markov_max_words         INTEGER DEFAULT 30,

    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
);

-- =========================================================
-- QUOTES SYSTEM
-- =========================================================

CREATE TABLE IF NOT EXISTS quotes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id    INTEGER NOT NULL,
    category    TEXT NOT NULL,
    quote_text  TEXT NOT NULL,
    author_id   INTEGER,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
);

CREATE INDEX IF NOT EXISTS idx_quotes_lookup
ON quotes (guild_id, category);

-- =========================================================
-- MARKOV TRAINING DATA
-- =========================================================

CREATE TABLE IF NOT EXISTS markov_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id    INTEGER NOT NULL,
    channel_id  INTEGER NOT NULL,
    message     TEXT NOT NULL,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
);

CREATE INDEX IF NOT EXISTS idx_markov_guild_channel
ON markov_messages (guild_id, channel_id);

-- =========================================================
-- MARKOV CHANNEL WHITELIST
-- =========================================================

CREATE TABLE IF NOT EXISTS markov_channels (
    guild_id   INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,

    PRIMARY KEY (guild_id, channel_id)
);

-- =========================================================
-- MUSIC STATE (PERSISTENT PLAYBACK)
-- =========================================================

CREATE TABLE IF NOT EXISTS music_state (
    guild_id          INTEGER PRIMARY KEY,

    current_track_uri TEXT,
    current_position  INTEGER DEFAULT 0,

    voice_channel_id  INTEGER,
    text_channel_id   INTEGER,

    is_playing        INTEGER DEFAULT 0,
    repeat_mode       TEXT DEFAULT 'off',
    shuffle           INTEGER DEFAULT 0,

    updated_at        TEXT DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- MUSIC QUEUE PERSISTENCE
-- =========================================================

CREATE TABLE IF NOT EXISTS music_queue (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id      INTEGER NOT NULL,
    position      INTEGER NOT NULL,

    track_title   TEXT,
    track_author  TEXT,
    track_uri     TEXT NOT NULL,
    track_source  TEXT,

    requester_id  INTEGER,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
);

CREATE INDEX IF NOT EXISTS idx_music_queue_guild
ON music_queue (guild_id);

-- =========================================================
-- PLAYLISTS
-- =========================================================

CREATE TABLE IF NOT EXISTS playlists (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id    INTEGER NOT NULL,
    name        TEXT NOT NULL,
    created_by  INTEGER,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (guild_id, name)
);

CREATE TABLE IF NOT EXISTS playlist_tracks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id  INTEGER NOT NULL,
    position     INTEGER NOT NULL,

    track_title  TEXT,
    track_author TEXT,
    track_uri    TEXT NOT NULL,

    FOREIGN KEY (playlist_id) REFERENCES playlists(id)
);

CREATE INDEX IF NOT EXISTS idx_playlist_lookup
ON playlist_tracks (playlist_id);

-- =========================================================
-- USER FAVORITES (OPTIONAL FEATURE)
-- =========================================================

CREATE TABLE IF NOT EXISTS user_favorites (
    user_id     INTEGER NOT NULL,
    track_uri   TEXT NOT NULL,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, track_uri)
);

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

CREATE TABLE IF NOT EXISTS personality_triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    pattern TEXT NOT NULL,
    priority INTEGER DEFAULT 100,
    enabled INTEGER DEFAULT 1
);