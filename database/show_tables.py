import sqlite3
import os

db_abs_path = os.path.dirname(os.path.realpath(__file__)) + '/allerviz.db'

print("Options: (items, comments, cuisines, allergens, all)")
table = input("Show table: ")

conn = sqlite3.connect(db_abs_path)
c = conn.cursor()

def show_items():
    try:
        items = c.execute("""SELECT
                                i.id, i.restaurant_name, i.description, i.allergy_score, i.image, c.name, c.id, s.name, s.id
                             FROM
                                items AS i
                             INNER JOIN cuisines     AS c ON i.cuisine_id     = c.id
                             INNER JOIN allergens  AS s ON i.allergen_id  = s.id
        """)

        print("ITEMS")
        print("#############")
        for row in items:
            print("ID:             ", row[0]),
            print("Restaurant Name:          ", row[1]),
            print("Description:    ", row[2]),
            print("Allergy Score:          ", row[3]),
            print("Image:          ", row[4]),
            print("Cuisine:       ", row[5], "(", row[6], ")"),
            print("allergen:    ", row[7], "(", row[8], ")"),
            print("\n")
    except:
        print("Something went wrong, please run db_init.py to initialize the database.")
        conn.close()

def show_comments():
    try:
        comments = c.execute("""SELECT
                                    c.id, c.content, i.restaurant_name, i.id
                                 FROM
                                    comments AS c
                                 INNER JOIN items AS i ON c.item_id = i.id
        """)

        print("COMMENTS")
        print("#############")
        for row in comments:
            print("ID:             ", row[0]),
            print("Content:        ", row[1]),
            print("Item:           ", row[2], "(", row[3], ")")
            print("\n")
    except:
        print("Something went wrong, please run db_init.py to initialize the database.")
        conn.close()

def show_cuisines():
    try:
        cuisines = c.execute("SELECT * FROM cuisines")

        print("cuisines")
        print("#############")
        for row in cuisines:
            print("ID:             ", row[0]),
            print("Name:           ", row[1])
            print("\n")
    except:
        print("Something went wrong, please run db_init.py to initialize the database.")
        conn.close()

def show_allergens():
    try:
        allergens = c.execute("SELECT s.id, s.name, c.name, c.id FROM allergens AS s INNER JOIN cuisines AS c ON s.cuisine_id = c.id")
        print("allergens")
        print("#############")
        for row in allergens:
            print("ID:             ", row[0]),
            print("Name:           ", row[1]),
            print("Cuisine:       ", row[2], "(", row[3], ")")
            print("\n")
    except:
        print("Something went wrong, please run db_init.py to initialize the database.")
        conn.close()


if table == "items":
    show_items()
elif table == "comments":
    show_comments()
elif table == "cuisines":
    show_cuisines()
elif table == "allergens":
    show_allergens()
elif table == "all":
    show_items()
    show_comments()
    show_cuisines()
    show_allergens()
else:
    print("This option does not exist.")

conn.close()
