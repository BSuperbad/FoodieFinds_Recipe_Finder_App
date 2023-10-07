# pip3 install psycopg2-binary
# pip3 install flask-sqlalchemy

"""FoodieFinds: Recipe Finder App & Blog"""

import requests
from flask import Flask, request, render_template, redirect, flash, session, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, FavoriteRecipe, Allergy, DietaryPreference, UserAllergy, UserDiet
from forms import AddUserForm, LoginForm, EditForm, IngredientSearchForm
from sqlalchemy.exc import IntegrityError
from bs4 import BeautifulSoup

API_BASE_URL = "https://api.spoonacular.com/recipes"
API_KEY = "575e1a620c0049c982972c3f3dba302b"
CURR_USER_KEY = "curr_user"
html_instructions = '<ol><li>'
diets = ['Gluten Free', 'Ketogenic', 'Vegetarian', 'Lacto-Vegetarian',
         'Ovo-Vegetarian', 'Vegan', 'Pescetarian', 'Paleo', 'Primal', 'Low FODMAP', 'Whole 30']
allergies = ['Dairy', 'Egg', 'Gluten', 'Grain', 'Peanut', 'Seafood',
             'Sesame', 'Shellfish', 'Soy', 'Sulfite', 'Tree Nut', 'Wheat']


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


for diet in diets:
    dietary_preference = DietaryPreference(type=diet)
    db.session.add(dietary_preference)


for allergy in allergies:
    allergy_entry = Allergy(type=allergy)
    db.session.add(allergy_entry)
db.session.commit()


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


@app.route('/', methods=['GET'])
def fetch_and_populate():
    """Fetch data from the API if logged in user"""
    if not g.user:
        return render_template('home-anon.html')
    else:
        user_allergies = g.user.get_allergies()
        user_diet = g.user.get_diet()
        if not user_allergies:
            user_allergies = []
        if not user_diet:
            user_diet = []
        response = requests.get(
            f'{API_BASE_URL}/complexSearch',
            params={
                'intolerances': ','.join(user_allergies),
                'diet': user_diet,
                'number': 2,
                'apiKey': API_KEY,
                'sort': 'random'
            })
        data = response.json()
        recipe_data = data["results"]
        recipe_list = [{"name": recipe["title"], "id": recipe.get(
            "id", "")} for recipe in recipe_data]
        return render_template('home.html', recipe_list=recipe_list)

##################################################################################
# User Routes


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

        flash(f"Welcome, {user.username}", 'success')
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
            flash(f"Welcome back, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials. Try again.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()

    flash("You have successfully logged out.", 'success')
    return redirect("/login")


@app.route('/profile/<int:user_id>', methods=["GET"])
def view_user_profile(user_id):
    user = User.query.get_or_404(user_id)
    allergies = user.allergies
    diet_prefs = user.diet_prefs

    if not g.user:
        flash("Unable to view other users profiles", "danger")
        return redirect("/")
    return render_template('users/detail.html', user=user, allergies=allergies, diet_prefs=diet_prefs)


@app.route('/profile/<int:user_id>', methods=["POST"])
def edit_user_profile(user_id):
    user = User.query.get_or_404(user_id)
    allergies = Allergy.query.all()
    diet_prefs = DietaryPreference.query.all()

    form = EditForm(request.form, obj=user)

    if not g.user:
        flash("Unable to view other users profiles", "danger")
        return redirect("/")

    if request.method == 'POST' and form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data

        new_allergies = request.form.getlist('allergies')
        for allergy_id in new_allergies:
            if not user.has_allergy(allergy_id):
                user_allergy = UserAllergy(
                    user_id=user.id, allergy_id=int(allergy_id))  # Convert to int
                db.session.add(user_allergy)

        new_diet_prefs = request.form.getlist('diet_prefs')
        for diet_prefs_id in new_diet_prefs:
            if not user.has_diet(diet_prefs_id):
                user_diet_pref = UserDiet(
                    user_id=user.id, diet_prefs_id=int(diet_prefs_id))
                db.session.add(user_diet_pref)

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(f'/profile/{g.user.id}')
    return render_template('users/edit_profile.html', form=form, user=user, allergies=allergies, diet_prefs=diet_prefs)


@app.route('/profile/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if g.user:
        do_logout()
        db.session.delete(g.user)
        db.session.commit()
        flash(f'{g.user.username} successfully deleted', 'success')
        return redirect("/")


##################################################################################
# Recipe Routes


@app.route('/recipes/<int:recipe_id>', methods=["GET", "POST"])
def get_recipe_info(recipe_id):
    """Show recipe details and option to add to favorites."""
    if not g.user:
        flash("Login to view and favorite recipes", "danger")
        return redirect('/login')

    response = requests.get(
        f'{API_BASE_URL}/{recipe_id}/information?includeNutrition=false&apiKey={API_KEY}')

    if response.status_code == 200:
        data = response.json()
        if 'title' in data:
            title = data['title']
            if 'image' in data:
                photo_url = data['image']
            else:
                photo_url = ''
            ingredients = [ingredient['original']
                           for ingredient in data['extendedIngredients']]
            instructions_html = data['instructions']
            soup = BeautifulSoup(instructions_html, 'html.parser')
            instructions = soup.get_text()

            return render_template('recipes/detail.html', title=title, photo_url=photo_url, ingredients=ingredients, instructions=instructions, recipe_id=recipe_id)
        else:
            return "Title not found in the JSON response."
    else:
        return f"Error: {response.status_code}, {response}"


@app.route('/fav-recipes', methods=['GET'])
def list_fav_recipes_of_g_user():
    """Page of Logged In User's Favorite Recipes."""
    if not g.user:
        flash("Login to add to favorites", "danger")
        return redirect('/login')

    user = User.query.filter_by(id=g.user.id).first()
    favorite_recipes = []

    for fav_recipe in user.fav_recipes:

        recipe_id = fav_recipe.recipe_id
        response = requests.get(
            f'{API_BASE_URL}/{recipe_id}/information?includeNutrition=false&apiKey={API_KEY}')

        recipe_data = response.json()
        recipe_name = recipe_data.get('title', 'N/A')

        recipe_info = {'recipe_id': recipe_id, 'recipe_name': recipe_name}
        favorite_recipes.append(recipe_info)

        # favorite_recipes.append(recipe_id)
    return render_template('recipes/fav-recipes.html', favorite_recipes=favorite_recipes)


@app.route('/fav-recipes/<int:recipe_id>', methods=['POST'])
def add_fav_recipe(recipe_id):
    """Have currently-logged-in-user add a recipe to their list of favorites/ and database."""
    if not g.user:
        flash("Login to add to favorites", "danger")
        return redirect('/login')

    response = requests.get(
        f'{API_BASE_URL}/{recipe_id}/information?includeNutrition=false&apiKey={API_KEY}')

    if response.status_code == 200:
        data = response.json()

        recipe_name = data.get('title')
        recipe_id = data.get('id')

        new_fav_recipe = FavoriteRecipe(
            user_id=g.user.id,
            recipe_id=recipe_id
        )

        db.session.add(new_fav_recipe)
        db.session.commit()

        flash(f"{recipe_name} added to favorites!", "success")
        return redirect(f'/recipes/{recipe_id}')
    else:
        flash("Error adding the recipe to favorites", "danger")


@app.route('/search', methods=['GET', 'POST'])
def search_ingredient():
    if not g.user:
        flash("Sign up or Log in to search recipes", "danger")
        return redirect('/')
    form = IngredientSearchForm()
    if request.method == 'POST':
        ingredients = request.form.get('ingredients')
        user_allergies = g.user.get_allergies()
        user_diet = g.user.get_diet()
        if not user_allergies:
            user_allergies = []
        if not user_diet:
            user_diet = []
        response = requests.get(
            f'{API_BASE_URL}/complexSearch',
            params={
                'intolerances': ','.join(user_allergies),
                'diet': user_diet,
                'number': 2,
                'apiKey': API_KEY,
                'query': ingredients,
                'sort': 'random'
            })
        if response.status_code == 200:
            data = response.json()
            recipe_data = data["results"]
            recipes = [{"name": recipe["title"], "id": recipe.get(
                "id", "")} for recipe in recipe_data]
            return render_template('recipes/search.html', recipes=recipes, form=form)
    return render_template('recipes/search.html', form=form)


@app.route('/fav-recipes/<int:recipe_id>/delete', methods=["POST"])
def unfavorite_recipe(recipe_id):
    """Remove a recipe from favorites for g.user"""
    if not g.user:
        flash("You must be logged in.", "danger")
        return redirect("/login")

    fav_recipe = FavoriteRecipe.query.filter_by(
        user_id=g.user.id, recipe_id=recipe_id).first()
    db.session.delete(fav_recipe)
    db.session.commit()
    flash("Recipe removed from favorites!", "success")
    return redirect("/fav-recipes")
