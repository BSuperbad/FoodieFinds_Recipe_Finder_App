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

    fav_recipes = db.relationship(
        'FavoriteRecipe', cascade="all, delete-orphan")
    allergies = db.relationship(
        "Allergy", backref="users", viewonly=True, cascade="all, delete, delete-orphan")
    diet_prefs = db.relationship(
        "DietaryPreference", backref="users", viewonly=True, cascade="all, delete, delete-orphan")

    #  secondary="user_allergies"
    #  secondary="user_diet_prefs",

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

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.
        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


class DietaryPreference(db.Model):
    """Dietary Preferences Model"""

    __tablename__ = "diet_prefs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String)


class Allergy(db.Model):
    """Allergy Model"""
    __tablename__ = "allergies"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String)


class FavoriteRecipe(db.Model):
    """Favorite Recipes Model for User"""

    __tablename__ = "fav_recipes"

    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id'), primary_key=True)
    recipe_id = db.Column(db.Integer, primary_key=True)


class UserAllergy(db.Model):
    """User-Allergy Association Table"""

    __tablename__ = "user_allergies"

    user_id = db.Column(db.Integer, db.ForeignKey(
        "users.id"), primary_key=True)
    allergy_id = db.Column(db.Integer, db.ForeignKey(
        "allergies.id"), primary_key=True)

    user = db.relationship("User", backref="user_allergies")
    allergy = db.relationship("Allergy", backref="user_allergies")


class UserDiet(db.Model):
    """User-Allergy Association Table"""

    __tablename__ = "user_diet_prefs"

    user_id = db.Column(db.Integer, db.ForeignKey(
        "users.id"), primary_key=True)
    diet_prefs_id = db.Column(db.Integer, db.ForeignKey(
        "diet_prefs.id"), primary_key=True)

    user = db.relationship("User", backref="user_diet_prefs")
    diet_pref = db.relationship("DietaryPreference", backref="user_diet_prefs")
