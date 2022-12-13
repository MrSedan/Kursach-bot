PRAGMA encoding = "UTF-8";
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
INSERT INTO Concerts (id, name, date, time) VALUES (1, 'Вагнер', '14.09.2023', '14:00');
INSERT INTO Concerts (id, name, date, time) VALUES (2, 'Моцарт', '13.02.2023', '9:00');
INSERT INTO Concerts (id, name, date, time) VALUES (3, 'Тест', '10.04.2023', '12:00');
