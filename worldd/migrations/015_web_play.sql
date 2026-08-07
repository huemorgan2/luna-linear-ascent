-- 005 web play: the website is a tenant of the world.
-- The secret is generated here and never leaves the database — web play
-- authenticates by session cookie (webplay.py), and auth.py refuses HMAC
-- for tenant 'web' outright, so this row cannot be replayed through /v1/*.
INSERT INTO ascent_tenants (tenant, secret)
SELECT 'web', md5(random()::text) || md5(random()::text) || md5(random()::text)
WHERE NOT EXISTS (SELECT 1 FROM ascent_tenants WHERE tenant = 'web');

-- Optional resurrection email (phase 4): nullable, unvalidated on purpose —
-- it exists so a lost password can be resurrected by hand later.
ALTER TABLE ascent_accounts ADD COLUMN IF NOT EXISTS email text;
