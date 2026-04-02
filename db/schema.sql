PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS models (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS teams (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS equipment (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id   INTEGER NOT NULL REFERENCES models(id),
    serial_no  TEXT UNIQUE,
    status     TEXT NOT NULL DEFAULT 'available'
                   CHECK(status IN ('available','broken','retired')),
    team_id    INTEGER REFERENCES teams(id),
    reg_no      TEXT DEFAULT '',
    notes       TEXT DEFAULT '',
    disposed    INTEGER DEFAULT 0,
    disposed_at TEXT,
    updated_at  TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS rentals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id    INTEGER NOT NULL REFERENCES equipment(id),
    borrower_team   INTEGER NOT NULL REFERENCES teams(id),
    borrower_name   TEXT NOT NULL,
    borrowed_at     TEXT DEFAULT (datetime('now','localtime')),
    expected_return TEXT,
    returned_at     TEXT
);
