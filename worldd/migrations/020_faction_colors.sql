-- 010: a faction flies a color of its own — one of the 9 named 1-bit
-- inks (see plugin colors.py). Pre-plan banners keep the exact ink
-- their sigils always wore: warden-violet.
ALTER TABLE ascent_factions
  ADD COLUMN IF NOT EXISTS color text NOT NULL DEFAULT 'warden-violet';
