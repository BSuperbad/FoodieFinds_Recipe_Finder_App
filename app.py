# pip3 install psycopg2-binary
# pip3 install flask-sqlalchemy

"""FoodieFinds: Recipe Finder App & Blog"""

import requests
from flask import Flask, request, render_template, redirect, flash, session, g
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Recipe, FavoriteRecipe, Allergy, DietaryPreference
from forms import AddUserForm, LoginForm
from sqlalchemy.exc import IntegrityError
from bs4 import BeautifulSoup

API_BASE_URL = "https://api.spoonacular.com"
API_KEY = "8a438439ac624168a50ed796a202591a"
CURR_USER_KEY = "curr_user"
html_instructions = '<ol><li>'


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///foodiefinds'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.app_context().push()

app.config['SECRET_KEY'] = 'secret'
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
debug = DebugToolbarExtension(app)

connect_db(app)
db.create_all()


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


# @app.route('/')
# def home():
#     """Shows a list of 10 recipes on the homepage from Spoonacular API"""
#     recipes = Recipe.query.limit(5).all()
#     return render_template("home.html", recipes=recipes)


@app.route('/', methods=['GET'])
def fetch_and_populate():
    # Fetch data from the API (replace with your API URL)
    response = requests.get(
        f'{API_BASE_URL}/recipes/random?apiKey={API_KEY}&limitLicense=true&number=10')
    data = response.json()
    recipe_data = data["recipes"]
    recipe_list = [{"name": recipe["title"], "url": recipe.get(
        "sourceUrl", "")} for recipe in recipe_data]
    return render_template('home.html', recipe_list=recipe_list, data=data)


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    form = AddUserForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
            )
            db.session.commit()

        except IntegrityError as e:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()

    flash("You have successfully logged out.", 'success')
    return redirect("/login")


##################################################################################
# Fav Recipe Routes


@app.route('/fav-recipes', methods=['GET'])
def list_fav_recipes_of_g_user():
    """Page of Logged In User's Favorite Recipes."""

    if g.user:
        fav_recipes = (FavoriteRecipe.query.all())

    return render_template('fav-recipes.html', fav_recipes=fav_recipes)


@app.route('/recipes/<int:recipe_id>')
def get_recipe_info(recipe_id):
    response = requests.get(
        f'https://api.spoonacular.com/recipes/{recipe_id}/information?includeNutrition=false&apiKey={API_KEY}')

    if response.status_code == 200:
        data = response.json()
        if 'title' in data:
            title = data['title']
            photo_url = data['image']
            ingredients = [ingredient['original']
                           for ingredient in data['extendedIngredients']]
            instructions_html = data['instructions']
            soup = BeautifulSoup(instructions_html, 'html.parser')
            instructions = soup.get_text()

            return render_template('recipes/detail.html', title=title, photo_url=photo_url, ingredients=ingredients, instructions=instructions, data=data)
        else:
            return "Title not found in the JSON response."
    else:
        return f"Error: {response.status_code}, {response}"
