import sqlite3
import os

db_abs_path = os.path.dirname(os.path.realpath(__file__)) + '/allerviz.db'
conn = sqlite3.connect(db_abs_path)
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS items")
c.execute("DROP TABLE IF EXISTS cuisines")
c.execute("DROP TABLE IF EXISTS allergens")
c.execute("DROP TABLE IF EXISTS comments")

c.execute("""CREATE TABLE cuisines(
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    name            TEXT
)""")

c.execute("""CREATE TABLE allergens(
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    name            TEXT,
                    allergen_id     INTEGER,
                    cuisine_id      INTEGER,
                    FOREIGN KEY(cuisine_id) REFERENCES cuisines(id)
)""")

c.execute("""CREATE TABLE items(
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    restaurant_name TEXT,
                    description     TEXT,
                    allergy_score   REAL,
                    image           TEXT,
                    cuisine_id      INTEGER,
                    allergen_id     INTEGER,
                    FOREIGN KEY(cuisine_id) REFERENCES cuisines(id),
                    FOREIGN KEY(allergen_id) REFERENCES allergens(id)
)""")

c.execute("""CREATE TABLE comments(
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    content         TEXT,
                    item_id         INTEGER,
                    FOREIGN KEY(item_id) REFERENCES items(id)
)""")

cuisines = [
    ("Italian",),
    ("Hispanic",),
    ("American",)
]
c.executemany("INSERT INTO cuisines (name) VALUES (?)", cuisines)

allergens = [
    ("Dairy",     1,  1),
    ("Eggs",      2,  2),
    ("Fish",      3,  1),
    ("Shellfish", 4,  3),
    ("Tree nuts", 5,  3),
    ("Wheat",     6,  1),
    ("Peanuts",   7,  2),
    ("Gluten",    8,  1),
    ("Soy",       9,  2),
    ("Sesame",    10, 3),
]
c.executemany("INSERT INTO allergens (name, allergen_id, cuisine_id) VALUES (?,?,?)", allergens)

items = [
    ("Red Robin", "American all around", 67.0, "", 3, 5),
    ("Five Guys", "Just 5 guys and some burgers", 4.0, "", 3, 3),
    ("Super Rico", "Columbian to the core!", 100.0, "", 2, 2),
    ("Cocina 214", "Authentic Tex Mex", 32.0, "", 2, 1),
    ("Linguine's", "Authenic Italian", 22.0, "", 1, 2)
]
c.executemany("INSERT INTO items (restaurant_name, description, allergy_score, image, cuisine_id, allergen_id) VALUES (?,?,?,?,?,?)", items)

comments = [
    ("This item is great!", 1),
    ("Whats up?", 2),
    ("Spam spam", 3)
]
c.executemany("INSERT INTO comments (content, item_id) VALUES (?,?)", comments)

conn.commit()
conn.close()

print("Database is created and initialized.")
print("You can see the tables with the show_tables.py script.")
