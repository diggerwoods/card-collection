-- ============================================================
-- CARD COLLECTION DATABASE SCHEMA
-- ============================================================
-- This is the SQL that creates your database structure.
-- Each section is explained so you can learn the concepts.

-- ============================================================
-- TABLE: cards
-- This is your main table. Each row = one card in your collection.
-- ============================================================
-- Key SQL concepts:
--   CREATE TABLE: defines a new table
--   SERIAL: auto-incrementing integer (each card gets a unique ID)
--   VARCHAR: text with a max length
--   TEXT: unlimited text
--   NUMERIC(10,2): decimal number with 2 decimal places (for money)
--   INTEGER: whole number
--   TIMESTAMP: date + time
--   DEFAULT: value used if you don't specify one

CREATE TABLE cards (
    id              SERIAL PRIMARY KEY,          -- unique ID, auto-assigned
    year            INTEGER NOT NULL,            -- card year (1952, 2026, etc.)
    classification  VARCHAR(50) NOT NULL,        -- sport: baseball, basketball, etc.
    series          VARCHAR(200) NOT NULL,       -- e.g. "1987 Topps"
    set_name        VARCHAR(200) NOT NULL,       -- e.g. "Base Set", "Rookie Stars"
    card_name       TEXT,                        -- full card name from Ludex
    player_name     VARCHAR(200) NOT NULL,       -- player or subject name
    team_name       VARCHAR(200),               -- team
    card_number     VARCHAR(20),                -- card # in the set (varchar because of "NNO", "U-106", etc.)
    parallel        VARCHAR(100),               -- parallel/variant name
    grader          VARCHAR(20),                -- PSA, SGC, BGS, RAW, or null
    grade_value     VARCHAR(10),                -- numeric grade (10, 9.5, etc.)
    condition       VARCHAR(50),                -- condition notes
    image_url       TEXT,                        -- URL to card image in Supabase Storage
    notes           TEXT,                        -- your personal notes
    purchased_at    DATE,                        -- when you bought it
    purchase_price  NUMERIC(10,2),              -- what you paid
    created_at      TIMESTAMP DEFAULT NOW(),    -- when you added it to the database
    updated_at      TIMESTAMP DEFAULT NOW()     -- last time you edited it
);

-- ============================================================
-- TABLE: price_history
-- Tracks estimated value over time. Each row = one price snapshot.
-- This lets you see how your collection value changes.
-- ============================================================
-- Key SQL concepts:
--   REFERENCES: creates a foreign key (links to another table)
--   ON DELETE CASCADE: if you delete a card, its price history is deleted too

CREATE TABLE price_history (
    id          SERIAL PRIMARY KEY,
    card_id     INTEGER REFERENCES cards(id) ON DELETE CASCADE,
    price       NUMERIC(10,2) NOT NULL,         -- estimated value at this point
    source      VARCHAR(50),                    -- where the price came from (ludex, ebay, manual)
    recorded_at TIMESTAMP DEFAULT NOW()         -- when this price was recorded
);

-- ============================================================
-- TABLE: sets_metadata
-- Stores known information about each set (total size, etc.)
-- Used for the set completion feature.
-- ============================================================

CREATE TABLE sets_metadata (
    id              SERIAL PRIMARY KEY,
    series          VARCHAR(200) NOT NULL,       -- e.g. "1987 Topps"
    classification  VARCHAR(50) NOT NULL,        -- sport
    total_cards     INTEGER,                     -- how many cards in the full set
    year            INTEGER,
    UNIQUE(series, classification)              -- prevent duplicate entries
);

-- ============================================================
-- TABLE: player_pc
-- Your personal collection tracker (which players you're building around)
-- ============================================================

CREATE TABLE player_pc (
    id          SERIAL PRIMARY KEY,
    player_name VARCHAR(200) NOT NULL UNIQUE,
    added_at    TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- These speed up common queries. Think of them like a book's index -
-- instead of scanning every page, the database can jump right to what it needs.
-- ============================================================

CREATE INDEX idx_cards_classification ON cards(classification);
CREATE INDEX idx_cards_year ON cards(year);
CREATE INDEX idx_cards_player ON cards(player_name);
CREATE INDEX idx_cards_series ON cards(series);
CREATE INDEX idx_cards_team ON cards(team_name);
CREATE INDEX idx_price_history_card ON price_history(card_id);
CREATE INDEX idx_price_history_date ON price_history(recorded_at);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- Supabase uses RLS to control who can read/write data.
-- For now, we'll allow public read access and authenticated writes.
-- ============================================================

ALTER TABLE cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE sets_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_pc ENABLE ROW LEVEL SECURITY;

-- Allow anyone to read (your page uses the anon key)
CREATE POLICY "Public read cards" ON cards FOR SELECT USING (true);
CREATE POLICY "Public read prices" ON price_history FOR SELECT USING (true);
CREATE POLICY "Public read sets" ON sets_metadata FOR SELECT USING (true);
CREATE POLICY "Public read pc" ON player_pc FOR SELECT USING (true);

-- Allow inserts/updates/deletes with the anon key (since this is your personal project)
CREATE POLICY "Public insert cards" ON cards FOR INSERT WITH CHECK (true);
CREATE POLICY "Public update cards" ON cards FOR UPDATE USING (true);
CREATE POLICY "Public delete cards" ON cards FOR DELETE USING (true);

CREATE POLICY "Public insert prices" ON price_history FOR INSERT WITH CHECK (true);
CREATE POLICY "Public insert sets" ON sets_metadata FOR INSERT WITH CHECK (true);
CREATE POLICY "Public update sets" ON sets_metadata FOR UPDATE USING (true);

CREATE POLICY "Public insert pc" ON player_pc FOR INSERT WITH CHECK (true);
CREATE POLICY "Public delete pc" ON player_pc FOR DELETE USING (true);
