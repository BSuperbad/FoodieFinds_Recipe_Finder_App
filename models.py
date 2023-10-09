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
    user_recipes = db.relationship(
        'UserRecipe', backref="user", cascade='all, delete-orphan')
    allergies = db.relationship(
        "UserAllergy", back_populates="user",
        overlaps="users", cascade="all, delete-orphan")
    diet_prefs = db.relationship(
        "UserDiet", back_populates="user",
        overlaps="users", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    def get_allergies(self):
        """Retrieve the allergies for this user."""
        allergies = [ua.allergy.type for ua in self.allergies]
        return allergies

    def has_allergy(self, allergy_id):
        """
        Check if the user has a specific allergy.
        :param allergy_id: The ID of the allergy to check.
        :return: True if the user has the allergy, False otherwise.
        """
        for user_allergy in self.allergies:
            if user_allergy.allergy_id == allergy_id:
                return True
        return False

    def get_diet(self):
        """Retrieve the dietary preferences for this user."""
        diets = [ud.diet_pref.type for ud in self.diet_prefs]
        return diets

    def has_diet(self, diet_id):
        """
        Check if the user has a specific allergy.
        :param allergy_id: The ID of the allergy to check.
        :return: True if the user has the allergy, False otherwise.
        """
        for user_diet_pref in self.diet_prefs:
            if user_diet_pref.diet_prefs_id == diet_id:
                return True
        return False

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
    type = db.Column(db.Text)


class Allergy(db.Model):
    """Allergy Model"""
    __tablename__ = "allergies"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.Text)


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

    user = db.relationship("User", back_populates="allergies",
                           overlaps="user_allergies")
    allergy = db.relationship("Allergy", backref="user_allergies")


class UserDiet(db.Model):
    """User-Allergy Association Table"""

    __tablename__ = "user_diet_prefs"

    user_id = db.Column(db.Integer, db.ForeignKey(
        "users.id"), primary_key=True)
    diet_prefs_id = db.Column(db.Integer, db.ForeignKey(
        "diet_prefs.id"), primary_key=True)

    user = db.relationship("User", back_populates="diet_prefs",  # Back-reference to User.diet_prefs
                           overlaps="user_diet_prefs")
    diet_pref = db.relationship(
        "DietaryPreference", backref="user_diet_prefs")


class UserRecipe(db.Model):
    """User-added Recipe Table"""

    __tablename__ = "user_recipes"

    id = db.Column(db.Integer,
                   primary_key=True,
                   autoincrement=True)
    title = db.Column(db.Text, nullable=False)
    photo_url = db.Column(db.Text, nullable=True)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
