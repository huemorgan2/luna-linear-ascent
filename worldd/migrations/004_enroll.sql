-- 004: self-service enrollment. A Luna install enrolls once with a random
-- install_id and gets back its tenant + secret; re-enrolling with the same
-- install_id is idempotent (returns the same credentials).
ALTER TABLE ascent_tenants ADD COLUMN IF NOT EXISTS install_id TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_tenants_install
    ON ascent_tenants (install_id) WHERE install_id IS NOT NULL;
