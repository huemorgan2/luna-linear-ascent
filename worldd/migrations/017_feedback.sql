-- 051 the postbox: player feedback threads, admin replies, unread badges.
-- Screenshots live in the database as bytea — no object store to run.

CREATE TABLE IF NOT EXISTS ascent_feedback (
    id            bigserial PRIMARY KEY,
    tenant        text NOT NULL,
    player        text NOT NULL,
    author        text NOT NULL,             -- character name at filing time
    subject       text NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now(),
    last_msg_at   timestamptz NOT NULL DEFAULT now(),
    last_sender   text NOT NULL DEFAULT 'player',   -- 'player' | 'admin'
    player_unread int NOT NULL DEFAULT 0,
    admin_unread  int NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_feedback_owner
    ON ascent_feedback (tenant, player, last_msg_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_fresh
    ON ascent_feedback (last_msg_at DESC);

CREATE TABLE IF NOT EXISTS ascent_feedback_messages (
    id          bigserial PRIMARY KEY,
    feedback_id bigint NOT NULL
                REFERENCES ascent_feedback (id) ON DELETE CASCADE,
    sender      text NOT NULL,               -- 'player' | 'admin'
    author      text NOT NULL,               -- character name of the writer
    body        text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feedback_messages
    ON ascent_feedback_messages (feedback_id, id);

CREATE TABLE IF NOT EXISTS ascent_feedback_attachments (
    id         bigserial PRIMARY KEY,
    message_id bigint NOT NULL
               REFERENCES ascent_feedback_messages (id) ON DELETE CASCADE,
    mime       text NOT NULL,
    bytes      bytea NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_feedback_attachments
    ON ascent_feedback_attachments (message_id);
