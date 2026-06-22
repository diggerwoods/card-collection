-- ============================================================
-- SQL CHEATSHEET FOR YOUR CARD COLLECTION
-- ============================================================
-- Run these in Supabase Dashboard > SQL Editor
-- Each query is explained so you learn the syntax.

-- ============================================================
-- SELECT - Reading data (most common operation)
-- ============================================================

-- Get all cards (careful - this returns 29K rows!)
SELECT * FROM cards LIMIT 100;

-- Count your total cards
SELECT COUNT(*) FROM cards;

-- Count by sport
-- GROUP BY: groups rows together
-- ORDER BY: sorts the results
SELECT classification, COUNT(*) as total
FROM cards
GROUP BY classification
ORDER BY total DESC;

-- Total value by sport
-- SUM(): adds up all values in a column
-- COALESCE: returns first non-null value (handles cards with no price)
SELECT
    classification,
    COUNT(*) as cards,
    SUM(ph.price) as total_value,
    ROUND(AVG(ph.price), 2) as avg_value
FROM cards c
JOIN price_history ph ON ph.card_id = c.id
GROUP BY classification
ORDER BY total_value DESC;

-- Find all your Nolan Ryan cards
-- WHERE: filters rows
-- ILIKE: case-insensitive pattern match (% = wildcard)
SELECT year, series, card_number, parallel, grader, grade_value
FROM cards
WHERE player_name ILIKE '%nolan ryan%'
ORDER BY year;

-- Find your most valuable cards
-- JOIN: combines data from two tables
-- This connects cards to their latest price
SELECT
    c.player_name,
    c.year,
    c.series,
    c.card_number,
    c.grader,
    c.grade_value,
    ph.price
FROM cards c
JOIN price_history ph ON ph.card_id = c.id
WHERE ph.recorded_at = (
    SELECT MAX(recorded_at) FROM price_history WHERE card_id = c.id
)
ORDER BY ph.price DESC
LIMIT 50;

-- Search for cards (useful for quick lookups)
SELECT * FROM cards
WHERE player_name ILIKE '%trout%'
   OR team_name ILIKE '%angels%'
ORDER BY year DESC;

-- ============================================================
-- INSERT - Adding new cards
-- ============================================================

-- Add a single card
INSERT INTO cards (year, classification, series, set_name, player_name, team_name, card_number, parallel)
VALUES (2026, 'baseball', '2026 Topps', 'Base Set', 'Paul Skenes', 'Pittsburgh Pirates', '100', NULL);

-- Add a card and get back its ID (useful for then adding a price)
INSERT INTO cards (year, classification, series, set_name, player_name, team_name, card_number)
VALUES (2026, 'baseball', '2026 Topps Chrome', 'Base Set', 'Jackson Chourio', 'Milwaukee Brewers', '50')
RETURNING id;

-- Add a price for a card (use the ID from above)
INSERT INTO price_history (card_id, price, source)
VALUES (12345, 15.99, 'ebay');

-- ============================================================
-- UPDATE - Changing existing data
-- ============================================================

-- Update a card's grade after getting it back from PSA
UPDATE cards
SET grader = 'PSA', grade_value = '10', updated_at = NOW()
WHERE id = 12345;

-- Mark a card with an image URL
UPDATE cards
SET image_url = 'https://your-supabase-url.supabase.co/storage/v1/object/public/card-images/nolan-ryan-1973.jpg'
WHERE id = 12345;

-- Update all cards in a series to fix a team name
UPDATE cards
SET team_name = 'Los Angeles Angels'
WHERE team_name = 'California Angels' AND year >= 2005;

-- ============================================================
-- DELETE - Removing data
-- ============================================================

-- Delete a specific card
DELETE FROM cards WHERE id = 12345;

-- Delete duplicate cards (keep the one with the lowest ID)
-- This is an advanced query using a subquery
DELETE FROM cards
WHERE id NOT IN (
    SELECT MIN(id)
    FROM cards
    GROUP BY year, series, set_name, player_name, card_number, parallel, grader, grade_value
);

-- ============================================================
-- USEFUL QUERIES FOR YOUR COLLECTION
-- ============================================================

-- Set completion: how complete is each set?
SELECT
    c.series,
    c.classification,
    COUNT(DISTINCT c.card_number) as owned,
    sm.total_cards,
    ROUND(COUNT(DISTINCT c.card_number)::numeric / sm.total_cards * 100, 1) as pct_complete
FROM cards c
JOIN sets_metadata sm ON sm.series = c.series AND sm.classification = c.classification
WHERE c.set_name = 'Base Set'
GROUP BY c.series, c.classification, sm.total_cards
ORDER BY pct_complete DESC;

-- Cards with no price (might need updating)
SELECT player_name, year, series, card_number
FROM cards c
WHERE NOT EXISTS (SELECT 1 FROM price_history WHERE card_id = c.id)
ORDER BY year DESC
LIMIT 100;

-- Value over time (if you record prices periodically)
SELECT
    DATE(recorded_at) as date,
    SUM(price) as total_value,
    COUNT(*) as cards_priced
FROM price_history
GROUP BY DATE(recorded_at)
ORDER BY date;

-- Find duplicates
SELECT player_name, year, series, card_number, parallel, COUNT(*) as copies
FROM cards
GROUP BY player_name, year, series, card_number, parallel
HAVING COUNT(*) > 1
ORDER BY copies DESC;

-- Graded vs ungraded value comparison
SELECT
    CASE WHEN grader IS NOT NULL AND grader != '' AND grader != 'RAW'
         THEN 'Graded' ELSE 'Ungraded' END as status,
    COUNT(*) as cards,
    SUM(ph.price) as total_value,
    ROUND(AVG(ph.price), 2) as avg_value
FROM cards c
JOIN price_history ph ON ph.card_id = c.id
GROUP BY status;

-- Your collection by team (fun to see which teams you collect most)
SELECT team_name, COUNT(*) as cards
FROM cards
WHERE team_name IS NOT NULL
GROUP BY team_name
ORDER BY cards DESC
LIMIT 30;
