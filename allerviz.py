
import pdb
import sqlite3
import os
import datetime
from sqlite3.dbapi2 import version
from pathlib import Path
from secrets import token_hex
from flask import Flask, jsonify, send_from_directory, render_template, request, redirect, url_for, g, flash, Markup as flask_Markup
from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DecimalField, FileField, HiddenField, SelectMultipleField, widgets
from wtforms.validators import InputRequired, DataRequired, Length, ValidationError
from wtforms.widgets import Input, ListWidget
from werkzeug.utils import secure_filename, escape, unescape
from markupsafe import Markup
from database.test.sqldb_init import sqliteDB
from database.allervizdb import AllervizDB, base_allergens
from bson.objectid import ObjectId

from pprint import pprint


basedir = Path(__file__).absolute()

app = Flask(__name__)
app.config["SECRET_KEY"] = "Guava&CheeseEmpanadasAreTheBest"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["jpeg", "jpg", "png"]
app.config["ALLOWED_FILE_EXTENSIONS"] = ["json", "csv"]
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["IMAGE_UPLOADS"] = f"{basedir.joinpath('uploads')}"

app.config["TESTING"] = True

app.config["RECAPTCHA_PUBLIC_KEY"] = "6LcwtOQZAAAAAP2TPQkLcs7iDqztiiQWDcjvwr8R"
app.config["RECAPTCHA_PRIVATE_KEY"] = "6LcwtOQZAAAAAAoRj7o0zQTXE-qHyctU9Zy_g3wK"

class AllergyScoreInput(Input):
    input_type = "number"

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        kwargs.setdefault("type", self.input_type)
        kwargs.setdefault("step", "0.01")
        if "value" not in kwargs:
            kwargs["value"] = field._value()
        if "required" not in kwargs and "required" in getattr(field, "flags", []):
            kwargs["required"] = True
        return Markup("""
                <div class="input-group mb-3">
                    <div class="input-group-prepend">
                        <span class="input-group-text">%%</span>
                    </div>
                    <input %s>
                </div>""" % self.html_params(name=field.name, **kwargs))

class AllergyScoreField(DecimalField):
    widget = AllergyScoreInput()

class ItemForm(FlaskForm):
    restaurant      = StringField("Restaurant Name", validators=[InputRequired("Input is required!"), DataRequired("Data is required!"), Length(min=3, max=20, message="Input must be between 5 and 20 characters long")])
    food_item       = StringField("Food Name", validators=[InputRequired("Input is required!"), DataRequired("Data is required!")])
    allergy_score   = AllergyScoreField("Allergy Score")
    description     = TextAreaField("Description", validators=[InputRequired("Input is required!"), DataRequired("Data is required!"), Length(min=5, max=40, message="Input must be between 5 and 40 characters long")])
    image           = FileField("Image", validators=[FileAllowed(app.config["ALLOWED_IMAGE_EXTENSIONS"], "Images only!")])

class BelongsToOtherFieldOption:
    def __init__(self, table, belongs_to, foreign_key=None, message=None):
        if not table:
            raise AttributeError("""
            BelongsToOtherFieldOption validator needs the table parameter
            """)
        if not belongs_to:
            raise AttributeError("""
            BelongsToOtherFieldOption validator needs the belongs_to parameter
            """)

        self.table = table
        self.belongs_to = belongs_to

        if not foreign_key:
            foreign_key = belongs_to + "_id"
        if not message:
            message = "Chosen option is not valid."

        self.foreign_key = foreign_key
        self.message = message

    def __call__(self, form, field):
        c = get_db().cursor()
        try:
            c.execute("""SELECT COUNT(*) FROM {}
                         WHERE id = ? AND {} = ?""".format(
                            self.table,
                            self.foreign_key
                         ),
                         (field.data, getattr(form, self.belongs_to).data)
            )
        except Exception as e:
            raise AttributeError("""
            Passed parameters are not correct. {}
            """.format(e))
        exists = c.fetchone()[0]
        if not exists:
            raise ValidationError(self.message)

class NewItemForm(ItemForm):
    cuisine     = SelectField("Cuisine", coerce=int)
    allergen    = SelectField("Allergen", coerce=int, validators=[BelongsToOtherFieldOption(table="allergens", belongs_to="cuisine", message="allergen does not belong to that cuisine.")])
    recaptcha   = RecaptchaField()
    submit      = SubmitField("Submit")

class UploadNewItemForm(ItemForm):
    image       = FileField("CSV or JSON file", validators=[FileAllowed(app.config["ALLOWED_FILE_EXTENSIONS"], "CSV or JSON files only!")])
    recaptcha   = RecaptchaField()
    submit      = SubmitField("Submit")

class EditItemForm(ItemForm):
    submit      = SubmitField("Update item")

class DeleteItemForm(FlaskForm):
    submit      = SubmitField("Delete item")

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class FilterForm(FlaskForm):
    restaurant      = StringField("Restaurant Name", validators=[Length(max=20)])
    allergy_score   = SelectField("Allergy Score", coerce=int, choices=[(0, "---"), (1, "Max to Min"), (2, "Min to Max")])
    cuisine         = SelectField("Cuisine", coerce=str)
    allergen        = SelectField("Allergen", coerce=str)
    allergen_list_val_desc = [(x, x+" Free") for x in base_allergens]
    allergen_filter = MultiCheckboxField('Allergens', choices=allergen_list_val_desc)
    submit          = SubmitField("Filter")

class NewCommentForm(FlaskForm):
    content = TextAreaField("Comment", validators=[InputRequired("Input is required."), DataRequired("Data is required.")])
    item_id = HiddenField(validators=[DataRequired()])
    submit  = SubmitField("Submit")


SQLLITEDB_EXISTS = False
SQLDB = None
MONGODB_EXISTS = False
MONGODB = None

VERBOSE = True

@app.route("/")
def home():
    """home [summary]

    :return: [description]
    :rtype: [type]
    """

    mongodb = get_mongodb()
    form = FilterForm(request.args, meta={"csrf": False})

    cuisines = mongodb.GetRestaurantCollection().distinct("cuisine")
    cuisines.sort()
    cuisines = [(choc, choc) for choc in cuisines]
    cuisines.insert(0, (0, "---"))
    form.cuisine.choices = cuisines

    allergens = mongodb.GetRestaurantCollection().distinct("allergens")
    allergens.sort()
    allergens = [(aller, aller) for aller in allergens]
    allergens.insert(0, (0, "---"))
    form.allergen.choices = allergens


    example_items = [
        {'id': 5, 'restaurant_name': "Linguine's", 'description': 'Authenic Italian', 'allergy_score': 22.0, 'image': '', 'cuisine': 'Italian', 'allergen': 'Eggs'},
        {'id': 4, 'restaurant_name': 'Cocina 214', 'description': 'Authentic Tex Mex', 'allergy_score': 32.0, 'image': '', 'cuisine': 'Hispanic', 'allergen': 'Dairy'},
        {'id': 3, 'restaurant_name': 'Super Rico', 'description': 'Columbian to the core!', 'allergy_score': 100.0, 'image': '', 'cuisine': 'Hispanic', 'allergen': 'Eggs'},
        {'id': 2, 'restaurant_name': 'Five Guys', 'description': 'Just 5 guys and some burgers', 'allergy_score': 4.0, 'image': '', 'cuisine': 'American', 'allergen': 'Fish'},
        {'id': 1, 'restaurant_name': 'Red Robin', 'description': 'American all around', 'allergy_score': 67.0, 'image': '', 'cuisine': 'American', 'allergen': 'Tree nuts'}
    ]

    items = mongodb.GetRestaurantsInfo(all=True)

    if VERBOSE:
        print(
            "Home mongodb -> "
            f"\n\ttype: {type(items)}"
            f"\n\tlength: {len(items)}"
        )

    if VERBOSE:
        print(
            "Home -> "
            f"\n\titems: {type(items)},"
            f"\n\tlength: {len(items)}"
            # f"\n\titems: {items},"
            f"\n\tform: {type(form)}"
            f"\n\tform: {form}"
            )
    return render_template("home.html", items=items, form=form)

@app.route("/filter")
def filter_items():

    mongodb = get_mongodb()
    form = FilterForm(request.args, meta={"csrf": False})

    cuisines = mongodb.GetRestaurantCollection().distinct("cuisine")
    cuisines.sort()
    cuisines = [(choc, choc) for choc in cuisines]
    cuisines.insert(0, (0, "---"))
    form.cuisine.choices = cuisines

    allergens = mongodb.GetRestaurantCollection().distinct("allergens")
    allergens.sort()
    allergens = [(aller, aller) for aller in allergens]
    allergens.insert(0, (0, "---"))
    form.allergen.choices = allergens

    filter_options = request.args.to_dict(flat=False)
    query = dict()

    if 'restaurant' in request.args and request.args["restaurant"]:
        query["restaurant"] = {
            "$in": filter_options["restaurant"]
        }

    if 'allergy_score' in request.args and int(request.args["allergy_score"]):
        query["total_allergy_score"] = {
            "$in": filter_options["allergy_score"]
        }

    if 'cuisine' in request.args and int(request.args["cuisine"]):
        query["cuisine"] = {
            "$in": filter_options["cuisine"]
        }

    if 'allergen_filter' in request.args and request.args["allergen_filter"]:
        query["allergens"] = {
            "$nin": filter_options["allergen_filter"]
        }

    if query:
        items = list(mongodb.QueryRestaurants(query=query))
    else:
        items = mongodb.GetRestaurantsInfo(all=True)


    if VERBOSE:
        print(
            "filter -> "
            f"\n\ttype: {type(items)}"
            f"\n\tlength: {len(items)}"
        )

    return render_template("filter.html", items=items, form=form)




@app.route('/favicon.ico')
def favicon():
    """favicon [summary]

    :return: [description]
    :rtype: [type]
    """
    return send_from_directory(os.path.join(app.root_path, 'static'),
                                'images/favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route("/item/<string:item_id>")
def item(item_id):

    mongodb = get_mongodb()
    restaurant = next(mongodb.QueryRestaurants({"_id": ObjectId(item_id)}))
    restaurant_extract = ["_id","restaurant", "allergens", "cuisine", "total_allergy_score"]

    restaurant_info = dict()
    for key in restaurant_extract:
        if not isinstance(restaurant[key], ObjectId):
            restaurant_info[key] = restaurant[key]
        else:
            restaurant_info[key] = str(restaurant[key])

    print(restaurant_info)
    menu = restaurant["menu"]
    print(len(menu))

    c = get_db().cursor()
    c.execute("""SELECT
                   i.id, i.restaurant, i.description, i.allergy_score, i.image, c.name, s.name
                   FROM
                   items AS i
                   INNER JOIN cuisines AS c ON i.cuisine_id = c.id
                   INNER JOIN allergens AS s ON i.allergen_id = s.id
                   WHERE i.id = ?""",
                   (item_id,)
    )
    row = c.fetchone()

    try:
        item = {
            "id": row[0],
            "restaurant": row[1],
            "description": row[2],
            "allergy_score": row[3],
            "image": row[4],
            "cuisine": row[5],
            "allergen": row[6]
        }
    except:
        item = {}

    if restaurant:

        c.execute("""SELECT menu_item, description, allergen, allergy_score FROM menu_items
                                    WHERE item_id = ? """, (item_id,))
        # menu = c.fetchall()
        comments_from_db = c.execute("""SELECT content FROM comments
                    WHERE item_id = ? ORDER BY id DESC""", (item_id,))
        comments = []
        for row in comments_from_db:
            comment = {
                "content": row[0]
            }
            comments.append(comment)

        commentForm = NewCommentForm()
        commentForm.item_id.data = item_id

        deleteItemForm = DeleteItemForm()

        print("item() -> "
              f"\n\tcommentForm: {type(commentForm)}, "
              f"\n\tcommentForm: {commentForm}, "
              f"\n\n\titem: {type(item)}, "
              f"\n\titem: {item}, "
              f"\n\n\tcomments: {type(comments)}, "
              f"\n\tcomments: {comments}, "
              f"\n\n\tmenu: {type(menu)}, "
              f"\n\tmenu: {menu}, "
              f"\n\n\tdeleteItemForm: {type(deleteItemForm)}"
              f"\n\tdeleteItemForm: {deleteItemForm}"
              )
    return render_template("item.html", commentForm=commentForm, restaurant=restaurant_info, comments=comments, menu=menu, deleteItemForm=deleteItemForm)

@app.route("/item/new", methods=["GET", "POST"])
def new_item():
    """new_item [summary]

    :return: [description]
    :rtype: [type]
    """
    conn = get_db()
    c = conn.cursor()
    form = NewItemForm()

    c.execute("SELECT id, name FROM cuisines")
    cuisines = c.fetchall()
    # [(1, 'Food'), (2, 'Technology'), (3, 'Books')]
    form.cuisine.choices = cuisines

    c.execute("SELECT id, name FROM allergens")
    allergens = c.fetchall()
    form.allergen.choices = allergens

    if form.validate_on_submit() and form.image.validate(form, extra_validators=(FileRequired(),)):

        filename = save_image_upload(form.image)

        # Process the form data
        c.execute("""INSERT INTO items
                    (restaurant, description, allergy_score, image, cuisine_id, allergen_id)
                    VALUES(?,?,?,?,?,?)""",
                    (
                        escape(form.restaurant.data),
                        escape(form.description.data),
                        float(form.allergy_score.data),
                        filename,
                        form.cuisine.data,
                        form.allergen.data
                    )
        )
        conn.commit()
        # Redirect to some page
        flash("Item {} has been successfully submitted".format(request.form.get("restaurant")), "success")
        return redirect(url_for("home"))

    return render_template("new_item.html", form=form)


@app.route("/item/<string:item_id>/edit", methods=["GET", "POST"])
def edit_item(item_id):
    """edit_item [summary]

    :param item_id: [description]
    :type item_id: [type]
    :return: [description]
    :rtype: [type]
    """
    conn = get_db()
    c = conn.cursor()
    item_from_db = c.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = c.fetchone()
    try:
        item = {
            "id": row[0],
            "restaurant": row[1],
            "description": row[2],
            "allergy_score": row[3],
            "image": row[4]
        }
    except:
        item = {}

    if item:
        form = EditItemForm()
        if form.validate_on_submit():

            filename = item["image"]
            if form.image.data:
                filename = save_image_upload(form.image)

            c.execute("""UPDATE items SET
            restaurant = ?, description = ?, allergy_score = ?, image = ?
            WHERE id = ?""",
                (
                    escape(form.restaurant.data),
                    escape(form.description.data),
                    float(form.allergy_score.data),
                    filename,
                    item_id
                )
            )
            conn.commit()

            flash("Item {} has been successfully updated".format(form.restaurant.data), "success")
            return redirect(url_for("item", item_id=item_id))

        form.restaurant.data       = item["restaurant"]
        form.description.data = unescape(item["description"])
        form.allergy_score.data       = item["allergy_score"]


        return render_template("edit_item.html", item=item, form=form)

    return redirect(url_for("home"))

@app.route("/item/<string:item_id>/delete", methods=["POST"])
def delete_item(item_id):
    """delete_item [summary]

    :param item_id: [description]
    :type item_id: [type]
    :return: [description]
    :rtype: [type]
    """
    conn = get_db()
    c = conn.cursor()

    item_from_db = c.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = c.fetchone()
    try:
        item = {
            "id": row[0],
            "restaurant": row[1]
        }
    except:
        item = {}

    if item:
        c.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()

        flash("Item {} has been successfully deleted.".format(item["restaurant"]), "success")
    else:
        flash("This item does not exist.", "danger")

    return redirect(url_for("home"))


@app.route("/comment/new", methods=["POST"])
def new_comment():
    """new_comment [summary]

    :return: [description]
    :rtype: [type]
    """
    conn = get_db()
    c = conn.cursor()
    form = NewCommentForm()

    try:
        is_ajax = int(request.form["ajax"])
    except:
        is_ajax = 0

    if form.validate_on_submit():

        c.execute("""INSERT INTO comments (content, item_id)
                     VALUES (?,?)""",
                     (
                        escape(form.content.data),
                        form.item_id.data
                     )
        )
        conn.commit()

        if is_ajax:
            return render_template("_comment.html", content=form.content.data)

    if is_ajax:
        return "Content is required.", 400
    return redirect(url_for('item', item_id=form.item_id.data))


@app.route("/cuisine/<int:cuisine_id>")
def cuisine(cuisine_id):
    """cuisine [summary]

    :param cuisine_id: [description]
    :type cuisine_id: [type]
    :return: [description]
    :rtype: [type]
    """

    c = get_db().cursor()
    c.execute("""SELECT id, name FROM allergens
                 WHERE cuisine_id = ?""",
                 (cuisine_id,)
    )
    allergens = c.fetchall()

    return jsonify(allergens=allergens)

def get_db():
    DB_FILE = 'allerviz.db'

    db = SQLDB
    if db is None:
        db = g._database = sqliteDB(DB_FILE).get_dbcon()
    return db

def get_mongodb(collection_name=None):
    """get_mongodb
    Returns reference to the mongodb interface class for this application.

    If a collection_name is proved then

    :param collection_name: [description], defaults to None
    :type collection_name: [type], optional
    :return: [description]
    :rtype: [type]
    """
    # db = getattr(g, "_database", None)
    # if db is None:
    #     print("\n\n\n\tDatabase not found. RECREATING NOW!!!\n\n\n")
    #     path = Path(__file__).parent.joinpath("database", "data", "Grubhub-Final-short.csv").resolve()
    #     mongodb = AllervizDB(db_name='allerviz')
    #     mongodb.Load(data_path=path)
    #     db = g._database = mongodb

    # dbmongo = getattr(g, "_database", None)
    # if dbmongo is None:
    #     print(u"\u001b[1m\u001b[31m Database not found. \u001b[0m")
    #     dbmongo = g._database = "test"
    # else:
    #     print(u"\u001b[1m\u001b[32m Database Found! \u001b[0m")
    #     print()

    db  = getattr(g, "_database", None)
    if db is None:
        print(u"\u001b[1m\u001b[31m \n\n\n\tDatabase not found. RECREATING NOW!!!\n\n\n\u001b[0m")
        path = Path(__file__).parent.joinpath("database", "data", "Grubhub-Final.csv").resolve()
        mongodb = AllervizDB(db_name='allerviz')
        mongodb.Load(data_path=path, checkdb_exists=True)
        db = g._database = mongodb
    else:
        print(u"\u001b[1m\u001b[32m Database Found! \u001b[0m")

    if collection_name is None:
        return db
    else:
        return mongodb.GetCollection(collection_name)

@app.teardown_appcontext
def close_connection(exception):
    """close_connection [summary]

    :param exception: [description]
    :type exception: [type]
    """
    db = get_db()
    if db is not None:
        db.close()



