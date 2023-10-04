"""Models for FoodieFinds."""

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()


def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)


class User(db.Model):
    """User Model"""

    __tablename__ = "users"

    id = db.Column(db.Integer,
                   primary_key=True,
                   autoincrement=True)
    username = db.Column(db.String,
                         nullable=False, unique=True)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    @classmethod
    def signup(cls, username, email, password):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
        )

        db.session.add(user)
        return user


class Recipe(db.Model):
    """Recipe Model"""

    __tablename__ = "recipes"

    id = db.Column(db.Integer,
                   primary_key=True,
                   autoincrement=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    recipe_url = db.Column(db.Text, nullable=False)
    allergies_id = db.Column(db.Integer, db.ForeignKey('allergies.id'))
    dietary_id = db.Column(db.Integer, db.ForeignKey('dietary_preferences.id'))

    # so, the recipe in the database is from the api with the sourceUrl..
    # we would have the recipes just listed in the database and then they would
    # be tagged as allergy or dietary preference for a user?
    # recipeurl is from source url.??


class DietaryPreference(db.Model):
    """Dietary Preferences Model for User"""

    __tablename__ = "dietary_preferences"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Allergy(db.Model):
    """Allergy Model for User"""
    __tablename__ = "allergies"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class FavoriteRecipe(db.Model):
    """Favorite Recipes Model for User"""

    __tablename__ = "fav_recipes"

    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id'), primary_key=True)

    recipe_id = db.Column(db.Integer, db.ForeignKey(
        'recipes.id'), primary_key=True)
