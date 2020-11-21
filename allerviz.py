from flask import Flask, jsonify, send_from_directory, render_template, request, redirect, url_for, g, flash, Markup as flask_Markup
from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DecimalField, FileField, HiddenField
from wtforms.validators import InputRequired, DataRequired, Length, ValidationError
from wtforms.widgets import Input
from werkzeug.utils import secure_filename, escape, unescape
from markupsafe import Markup
import pdb
import sqlite3
import os
import datetime
from secrets import token_hex

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = "secretkey"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["jpeg", "jpg", "png"]
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["IMAGE_UPLOADS"] = os.path.join(basedir, "uploads")

app.config["TESTING"] = True

app.config["RECAPTCHA_PUBLIC_KEY"] = "6LftyNMUAAAAANHsGBeDjOxqGbIE1sdahNHU2GYv"
app.config["RECAPTCHA_PRIVATE_KEY"] = "6LftyNMUAAAAAJ1ZGq-NHzvf_4YU8VOeaXmg3-fe"

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
        return Markup("""<div class="input-group mb-3">
                    <div class="input-group-prepend">
                        <span class="input-group-text">$</span>
                    </div>
                    <input %s>
        </div>""" % self.html_params(name=field.name, **kwargs))

class AllergyScoreField(DecimalField):
    widget = AllergyScoreInput()

class ItemForm(FlaskForm):
    restaurant_name       = StringField("Restaurant Name", validators=[InputRequired("Input is required!"), DataRequired("Data is required!"), Length(min=5, max=20, message="Input must be between 5 and 20 characters long")])
    allergy_score       = AllergyScoreField("Allergy Score")
    description = TextAreaField("Description", validators=[InputRequired("Input is required!"), DataRequired("Data is required!"), Length(min=5, max=40, message="Input must be between 5 and 40 characters long")])
    image       = FileField("Image", validators=[FileAllowed(app.config["ALLOWED_IMAGE_EXTENSIONS"], "Images only!")])

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
    allergen    = SelectField("allergen", coerce=int, validators=[BelongsToOtherFieldOption(table="allergens", belongs_to="cuisine", message="allergen does not belong to that cuisine.")])
    recaptcha   = RecaptchaField()
    submit      = SubmitField("Submit")

class EditItemForm(ItemForm):
    submit      = SubmitField("Update item")

class DeleteItemForm(FlaskForm):
    submit      = SubmitField("Delete item")

class FilterForm(FlaskForm):
    restaurant_name = StringField("Restaurant Name", validators=[Length(max=20)])
    allergy_score   = SelectField("Allergy Score", coerce=int, choices=[(0, "---"), (1, "Max to Min"), (2, "Min to Max")])
    cuisine         = SelectField("Cuisine", coerce=int)
    allergen        = SelectField("allergen", coerce=int)
    submit          = SubmitField("Filter")

class NewCommentForm(FlaskForm):
    content = TextAreaField("Comment", validators=[InputRequired("Input is required."), DataRequired("Data is required.")])
    item_id = HiddenField(validators=[DataRequired()])
    submit  = SubmitField("Submit")


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'images/favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/cuisine/<int:cuisine_id>")
def cuisine(cuisine_id):
    c = get_db().cursor()
    c.execute("""SELECT id, name FROM allergens
                 WHERE cuisine_id = ?""",
                 (cuisine_id,)
    )
    allergens = c.fetchall()

    return jsonify(allergens=allergens)

@app.route("/item/<int:item_id>/edit", methods=["GET", "POST"])
def edit_item(item_id):
    conn = get_db()
    c = conn.cursor()
    item_from_db = c.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = c.fetchone()
    try:
        item = {
            "id": row[0],
            "restaurant_name": row[1],
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
            restaurant_name = ?, description = ?, allergy_score = ?, image = ?
            WHERE id = ?""",
                (
                    escape(form.restaurant_name.data),
                    escape(form.description.data),
                    float(form.allergy_score.data),
                    filename,
                    item_id
                )
            )
            conn.commit()

            flash("Item {} has been successfully updated".format(form.restaurant_name.data), "success")
            return redirect(url_for("item", item_id=item_id))

        form.restaurant_name.data       = item["restaurant_name"]
        form.description.data = unescape(item["description"])
        form.allergy_score.data       = item["allergy_score"]


        return render_template("edit_item.html", item=item, form=form)

    return redirect(url_for("home"))

@app.route("/item/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id):
    conn = get_db()
    c = conn.cursor()

    item_from_db = c.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = c.fetchone()
    try:
        item = {
            "id": row[0],
            "restaurant_name": row[1]
        }
    except:
        item = {}

    if item:
        c.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()

        flash("Item {} has been successfully deleted.".format(item["restaurant_name"]), "success")
    else:
        flash("This item does not exist.", "danger")

    return redirect(url_for("home"))

@app.route("/item/<int:item_id>")
def item(item_id):
    c = get_db().cursor()
    c.execute("""SELECT
                   i.id, i.restaurant_name, i.description, i.allergy_score, i.image, c.name, s.name
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
            "restaurant_name": row[1],
            "description": row[2],
            "allergy_score": row[3],
            "image": row[4],
            "cuisine": row[5],
            "allergen": row[6]
        }
    except:
        item = {}

    if item:

        c.execute("""SELECT menu_item_name, description, allergen, allergy_score FROM menu_items
                                    WHERE item_id = ? """, (item_id,))
        menu = c.fetchall()

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

        return render_template("item.html", commentForm=commentForm, item=item, comments=comments, menu=menu, deleteItemForm=deleteItemForm)
    return redirect(url_for("home"))

@app.route("/comment/new", methods=["POST"])
def new_comment():
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

@app.route("/")
def home():
    conn = get_db()
    c = conn.cursor()

    form = FilterForm(request.args, meta={"csrf": False})

    c.execute("SELECT id, name FROM cuisines")
    cuisines = c.fetchall()
    cuisines.insert(0, (0, "---"))
    form.cuisine.choices = cuisines

    c.execute("SELECT id, name FROM allergens")
    allergens = c.fetchall()
    allergens.insert(0, (0, "---"))
    form.allergen.choices = allergens

    query = """SELECT
                    i.id, i.restaurant_name, i.description, i.allergy_score, i.image, c.name, s.name
                    FROM
                    items AS i
                    INNER JOIN cuisines AS c ON i.cuisine_id = c.id
                    INNER JOIN allergens AS s ON i.allergen_id = s.id
    """

    try:
        is_ajax = int(request.args["ajax"])
    except:
        is_ajax = 0

    if form.validate():

        filter_queries = []
        parameters = []

        if form.restaurant_name.data.strip():
            filter_queries.append("i.restaurant_name LIKE ?")
            parameters.append("%" + escape(form.restaurant_name.data) + "%")

        if form.cuisine.data:
            filter_queries.append("i.cuisine_id = ?")
            parameters.append(form.cuisine.data)

        if form.allergen.data:
            filter_queries.append("i.allergen_id = ?")
            parameters.append(form.allergen.data)

        if filter_queries:
            query += " WHERE "
            query += " AND ".join(filter_queries)

        if form.allergy_score.data:
            if form.allergy_score.data == 1:
                query += " ORDER BY i.allergy_score DESC"
            else:
                query += " ORDER BY i.allergy_score"
        else:
            query += " ORDER BY i.id DESC"

        items_from_db = c.execute(query, tuple(parameters))
    else:
        items_from_db = c.execute(query + "ORDER BY i.id DESC")

    items = []
    for row in items_from_db:
        item = {
            "id": row[0],
            "restaurant_name": row[1],
            "description": row[2],
            "allergy_score": row[3],
            "image": row[4],
            "cuisine": row[5],
            "allergen": row[6]
        }
        items.append(item)

    if is_ajax:
        return render_template("_items.html", items=items)
    return render_template("home.html", items=items, form=form)

@app.route("/uploads/<filename>")
def uploads(filename):
    return send_from_directory(app.config["IMAGE_UPLOADS"], filename)

@app.route("/item/new", methods=["GET", "POST"])
def new_item():
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
                    (restaurant_name, description, allergy_score, image, cuisine_id, allergen_id)
                    VALUES(?,?,?,?,?,?)""",
                    (
                        escape(form.restaurant_name.data),
                        escape(form.description.data),
                        float(form.allergy_score.data),
                        filename,
                        form.cuisine.data,
                        form.allergen.data
                    )
        )
        conn.commit()
        # Redirect to some page
        flash("Item {} has been successfully submitted".format(request.form.get("restaurant_name")), "success")
        return redirect(url_for("home"))

    return render_template("new_item.html", form=form)

def save_image_upload(image):
    format = "%Y%m%dT%H%M%S"
    now = datetime.datetime.utcnow().strftime(format)
    random_string = token_hex(2)
    filename = random_string + "_" + now + "_" + image.data.filename
    filename = secure_filename(filename)
    image.data.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
    return filename

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("db/allerviz.db")
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()
