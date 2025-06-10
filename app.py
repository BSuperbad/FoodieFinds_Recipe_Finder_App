# pip3 install psycopg2-binary
# pip3 install flask-sqlalchemy

"""FoodieFinds: Recipe Finder App & Blog"""
import os
import requests
from flask import Flask, request, render_template, redirect, flash, session, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, FavoriteRecipe, Allergy, DietaryPreference, UserAllergy, UserDiet, UserRecipe
from forms import AddUserForm, LoginForm, EditForm, IngredientSearchForm, AddRecipeForm
from sqlalchemy.exc import IntegrityError
from bs4 import BeautifulSoup
from secret import API_KEY

API_BASE_URL = "https://api.spoonacular.com/recipes"
API_KEY = API_KEY
CURR_USER_KEY = "curr_user"
html_instructions = '<ol><li>'
diets = ['Gluten Free', 'Ketogenic', 'Vegetarian', 'Lacto-Vegetarian',
         'Ovo-Vegetarian', 'Vegan', 'Pescetarian', 'Paleo', 'Primal', 'Low FODMAP', 'Whole 30']
allergies = ['Dairy', 'Egg', 'Gluten', 'Grain', 'Peanut', 'Seafood',
             'Sesame', 'Shellfish', 'Soy', 'Sulfite', 'Tree Nut', 'Wheat']


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL','postgresql:///foodiefinds'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.app_context().push()

app.config['SECRET_KEY'] = 'secret'
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
debug = DebugToolbarExtension(app)

connect_db(app)
db.create_all()


# Seed diets and allergies only if empty
if not DietaryPreference.query.first():
    for diet in diets:
        db.session.add(DietaryPreference(type=diet))
if not Allergy.query.first():
    for allergy in allergies:
        db.session.add(Allergy(type=allergy))

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
                'number': 10,
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


@app.route('/profile/<int:user_id>/edit', methods=["GET", "POST"])
def edit_user_profile(user_id):
    user = User.query.get_or_404(user_id)
    allergies = Allergy.query.all()
    diet_prefs = DietaryPreference.query.all()

    form = EditForm(request.form, obj=user)

    if not g.user:
        flash("Unable to view other users' profiles", "danger")
        return redirect("/")

    if request.method == 'POST' and form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data

        allergy_id = int(request.form.get('allergies')) if request.form.get(
            'allergies') != 'None' else None
        diet_prefs_id = int(request.form.get('diet_prefs')) if request.form.get(
            'diet_prefs') != 'None' else None

        if user.has_allergy(allergy_id):
            flash("Allergy already noted.", "warning")
            return redirect(f'/profile/{g.user.id}/edit')
        elif user.has_diet(diet_prefs_id):
            flash("Dietary Preference already noted.", "warning")
            return redirect(f'/profile/{g.user.id}/edit')
        else:
            user.allergies_id = allergy_id
            user.diet_prefs_id = diet_prefs_id

        new_allergies = request.form.getlist('allergies')
        if 'None' not in new_allergies:
            for allergy_id in new_allergies:
                if not user.has_allergy(int(allergy_id)):
                    user_allergy = UserAllergy(
                        user_id=user.id, allergy_id=int(allergy_id))
                    db.session.add(user_allergy)

        new_diet_prefs = request.form.getlist('diet_prefs')
        if 'None' not in new_diet_prefs:
            for diet_prefs_id in new_diet_prefs:
                if not user.has_diet(int(diet_prefs_id)):
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
                'diet': ','.join(user_diet),
                'number': 10,
                'apiKey': API_KEY,
                'query': ingredients,
                'sort': 'random'
            })
        if response.status_code == 200:
            data = response.json()
            recipe_data = data["results"]
            recipes = [{"name": recipe["title"], "id": recipe.get(
                "id", "")} for recipe in recipe_data]
            if not recipes:  # Check if recipes list is empty
                flash(
                    "No recipes found based on your allergies/ dietary preferences.", "warning")
            else:
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

##################################################################################
# Removing Tags Routes


@app.route('/remove-allergy/<int:user_allergy_id>', methods=['POST'])
def remove_allergy(user_allergy_id):
    """Remove an allergy for g.user"""
    if not g.user:
        flash("You must be logged in.", "danger")
        return redirect("/login")

    user_allergy = UserAllergy.query.get_or_404((g.user.id, user_allergy_id))

    db.session.delete(user_allergy)
    db.session.commit()
    flash(f"Allergy removed from {g.user.username} profile.", "success")
    return redirect(f"/profile/{g.user.id}")


@app.route('/remove-diet/<int:user_diet_pref_id>', methods=['POST'])
def remove_diet(user_diet_pref_id):
    """Remove a dietary preference for g.user"""
    if not g.user:
        flash("You must be logged in.", "danger")
        return redirect("/login")

    user_diet = UserDiet.query.get_or_404((g.user.id, user_diet_pref_id))

    db.session.delete(user_diet)
    db.session.commit()
    flash(
        f"Dietary Preference removed from {g.user.username} profile.", "success")
    return redirect(f"/profile/{g.user.id}")

##################################################################################
# Stretch goal/ Add own recipe route


@app.route('/user-recipes', methods=['GET'])
def list_added_recipes_of_g_user():
    """Page of Logged In User's Added Recipes."""
    if not g.user:
        flash("Login to add recipes of your own", "danger")
        return redirect('/login')

    user_recipes = UserRecipe.query.filter_by(user_id=g.user.id).all()
    return render_template('add-recipes/user-recipes.html', user_recipes=user_recipes)


@app.route('/add-recipe', methods=['GET', 'POST'])
def add_recipe():
    """Shows the form to add a recipe and adds to the db"""

    """Handle add recipe.

    User creates/ adds own recipes and add to DB. Redirect to user's favorite recipes.

    If form not valid, present form.
    """
    if not g.user:
        flash("You must be logged in.", "danger")
        return redirect("/login")

    form = AddRecipeForm()

    if form.validate_on_submit():
        recipe = UserRecipe(
            title=form.title.data,
            photo_url=form.photo_url.data,
            ingredients=form.ingredients.data,
            instructions=form.instructions.data,
            user_id=g.user.id
        )
        db.session.add(recipe)
        db.session.commit()
        flash(f"{recipe.title} recipe added.", "success")
        return redirect(f'/user-recipes/{recipe.id}')

    return render_template('add-recipes/add.html', form=form)


@app.route('/user-recipes/<int:recipe_id>', methods=["GET"])
def get_user_recipe_info(recipe_id):
    """Show user-added recipe details."""
    if not g.user:
        flash("Login to view and add recipes", "danger")
        return redirect('/login')

    user_recipe = UserRecipe.query.get_or_404(recipe_id)

    return render_template('add-recipes/show.html', user_recipe=user_recipe)


@app.route('/delete/<int:recipe_id>', methods=["POST"])
def delete_recipe(recipe_id):
    """Delete user recipe."""

    if not g.user:
        flash("You must be logged in.", "danger")
        return redirect("/login")

    recipe = UserRecipe.query.get_or_404(recipe_id)
    db.session.delete(recipe)
    db.session.commit()
    flash(
        f"{recipe.title} has been deleted.", "success")
    return redirect(f"/user-recipes")
