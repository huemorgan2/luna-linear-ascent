-- 010-gmail-door: sign up with Gmail; keep password login for old accounts.
--
-- auth_provider records how an account was made ('password' | 'google').
-- google_sub is Google's stable subject id — never the email (emails
-- change, sub does not). Its PRESENCE is what "Gmail-connected" means:
-- the portrait gate and the OAuth login lookup both key off it.
-- A Gmail account has no password, so pw_hash becomes nullable.
--
-- Data-preserving: existing rows keep auth_provider='password',
-- google_sub NULL (i.e. not yet Gmail-connected), pw_hash untouched.
ALTER TABLE ascent_accounts
    ADD COLUMN IF NOT EXISTS auth_provider text NOT NULL DEFAULT 'password';

ALTER TABLE ascent_accounts
    ADD COLUMN IF NOT EXISTS google_sub text;

ALTER TABLE ascent_accounts
    ALTER COLUMN pw_hash DROP NOT NULL;

-- one Google identity, one account (nulls don't collide)
CREATE UNIQUE INDEX IF NOT EXISTS ascent_accounts_google_sub
    ON ascent_accounts (google_sub) WHERE google_sub IS NOT NULL;
