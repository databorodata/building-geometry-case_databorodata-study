CREATE TABLE IF NOT EXISTS sites (
    id uuid PRIMARY KEY,
    name text NOT NULL,
    polygon jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS options (
    id uuid PRIMARY KEY,
    site_id uuid NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    parent_id uuid REFERENCES options(id) ON DELETE CASCADE,
    source_id uuid REFERENCES options(id) ON DELETE SET NULL,
    kind text NOT NULL DEFAULT 'save',
    name text,
    params jsonb NOT NULL,
    result jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE options ADD COLUMN IF NOT EXISTS kind text NOT NULL DEFAULT 'save';

ALTER TABLE options ADD COLUMN IF NOT EXISTS source_id uuid REFERENCES options(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_options_site_created ON options (site_id, created_at);

CREATE INDEX IF NOT EXISTS idx_options_parent ON options (parent_id);
