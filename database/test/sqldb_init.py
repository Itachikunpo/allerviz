""" [summary]
"""
import sqlite3
from pathlib2 import Path


def init_entries():
    """[summary]

    Returns:
        [type]: [description]
    """
    allergens = [("Dairy",     1,  1),
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

    cuisines = [("Italian",),
                ("Hispanic",),
                ("American",)
                ]

    items = [
        ("Red Robin", "American all around", 67.0, "", 3, 5),
        ("Five Guys", "Just 5 guys and some burgers", 4.0, "", 3, 3),
        ("Super Rico", "Columbian to the core!", 100.0, "", 2, 2),
        ("Cocina 214", "Authentic Tex Mex", 32.0, "", 2, 1),
        ("Linguine's", "Authenic Italian", 22.0, "", 1, 2)
    ]

    menu_items = [
        (1, "Red Robin", "Just Krispy", "The Original Spicy Tuna Krispy Rice (2 pc)King Salmon & Yuzu Krispy Rice (2 pc)", "", 90.0),
        (1, "Red Robin", "Chicken Sandwich", "Chicken, Whole wheat bread, tomato, lettuce, cheese", "cheese", 60.0),
        (2, "Five Guys", "Beef Burger", "lettuce, cheese, fries, tomato, , pickles, onion and choice of sauce", "", 100.0),
        (3, "Super Rico", "Deluxe Quesadilla", "Jack cheese, tomatoes, onions, guacamole and sour cream.", "", 100.0),
        (4, "Cocina 214", "Capucino", "coffee, milk, sugar", "milk", 49.0),
        (5, "Linguine's", "Seafood Linguini", "tomato sauce, shrimp, pasta", "shrimp", 60.0)
    ]

    comments = [("This item is great!", 1),
                ("Whats up?", 2),
                ("Spam spam", 3)
                ]

    return (allergens, items, menu_items, cuisines, comments)


class sqliteDB():
    """sqliteDB [summary]
    """
    def __init__(self, db_filename="project.db"):
        """__init__ [summary]

        :param db_filename: [description], defaults to "project.db"
        :type db_filename: str, optional
        """
        db_path = Path(db_filename)
        self.dbcon = sqlite3.connect(db_path.absolute())
        self.dbcursor = self.dbcon.cursor()

        self.drop_tables()
        self.create_tables()
        allergens, items, menu_items, cuisines, comments = init_entries()
        self.insert_db(allergens, items, menu_items, cuisines, comments)

    def get_dbcon(self):
        """get_dbcon [summary]

        :return: [description]
        :rtype: [type]
        """
        return self.dbcon

    def get_dbcursor(self):
        """get_dbcursor [summary]

        :return: [description]
        :rtype: [type]
        """
        return self.dbcursor

    def drop_tables(self):
        """drop_tables Drop all the tables from the database
        """
        try:
            self.dbcursor.execute("DROP TABLE IF EXISTS items")
            self.dbcursor.execute("DROP TABLE IF EXISTS cuisines")
            self.dbcursor.execute("DROP TABLE IF EXISTS allergens")
            self.dbcursor.execute("DROP TABLE IF EXISTS comments")
            self.dbcursor.execute("DROP TABLE IF EXISTS menu_items")
            self.dbcon.commit()
        except AttributeError:
            raise AttributeError("Database connection invalid. Check that its not NoneType.")


    def restart_tables(self):
        """restart_tables [summary]
        """
        self.drop_tables()
        self.create_tables()
        self.insert_db(init_entries())

    def create_tables(self):
        """create_tables [summary]
        """

        self.dbcursor.execute("""CREATE TABLE cuisines(
                        id              INTEGER PRIMARY KEY AUTOINCREMENT,
                        name            TEXT
        )""")

        self.dbcursor.execute("""CREATE TABLE allergens(
                            id              INTEGER PRIMARY KEY AUTOINCREMENT,
                            name            TEXT,
                            allergen_id     INTEGER,
                            cuisine_id      INTEGER,
                            FOREIGN KEY(cuisine_id) REFERENCES cuisines(id)
        )""")

        self.dbcursor.execute("""CREATE TABLE items(
                            id              INTEGER PRIMARY KEY AUTOINCREMENT,
                            restaurant      TEXT,
                            description     TEXT,
                            allergy_score   REAL,
                            image           TEXT,
                            cuisine_id      INTEGER,
                            allergen_id     INTEGER,
                            FOREIGN KEY(cuisine_id) REFERENCES cuisines(id),
                            FOREIGN KEY(allergen_id) REFERENCES allergens(id)
        )""")

        self.dbcursor.execute("""CREATE TABLE menu_items(
                            id              INTEGER PRIMARY KEY AUTOINCREMENT,
                            item_id         INTEGER,
                            restaurant      TEXT,
                            menu_item       TEXT,
                            description     TEXT,
                            allergen        TEXT,
                            allergy_score   REAL,
                            FOREIGN KEY(item_id) REFERENCES items(id)
        )""")

        self.dbcursor.execute("""CREATE TABLE comments(
                            id              INTEGER PRIMARY KEY AUTOINCREMENT,
                            content         TEXT,
                            item_id         INTEGER,
                            FOREIGN KEY(item_id) REFERENCES items(id)
        )""")
        self.dbcon.commit()

    def insert_db(self, allergens=None, items=None, menu_items=None, cuisines=None, comments=None):
        """insert_db Insert into the database some entries
        """
        if allergens is not None:
            self.dbcursor.executemany("INSERT INTO cuisines (name) VALUES (?)", cuisines)
        if items is not None:
            self.dbcursor.executemany("INSERT INTO allergens (name, allergen_id, cuisine_id) VALUES (?,?,?)", allergens)
        if menu_items is not None:
            self.dbcursor.executemany("INSERT INTO menu_items (item_id, restaurant, menu_item, description, allergen, allergy_score) VALUES (?,?,?,?,?,?)", menu_items)
        if cuisines is not None:
            self.dbcursor.executemany("INSERT INTO items (restaurant, description, allergy_score, image, cuisine_id, allergen_id) VALUES (?,?,?,?,?,?)", items)
        if comments is not None:
            self.dbcursor.executemany("INSERT INTO comments (content, item_id) VALUES (?,?)", comments)
        self.dbcon.commit()

    def close_dbcon(self):
        """close_dbcon [summary]
        """
        self.dbcon.close()


if __name__ == "__main__":
    DB_FILE = 'allerviz.db'

    print("Starting sqlite3 database.")
    allervizDB = sqliteDB(DB_FILE)
    print("Database intialized.")


