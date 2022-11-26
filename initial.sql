DROP TABLE IF EXISTS "Concerts";
CREATE TABLE "Concerts" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL
);
DROP TABLE IF EXISTS "Tickets";
CREATE TABLE "Tickets" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    concert_id INTEGER NOT NULL,
    place INTEGER not null,
    line INTEGER not null,
    FOREIGN KEY(concert_id) REFERENCES Concerts(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
        MATCH SIMPLE
);