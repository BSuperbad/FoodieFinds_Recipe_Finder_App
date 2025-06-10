from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Email, Length, Optional, URL
from wtforms.widgets import ListWidget, CheckboxInput
from models import Allergy, DietaryPreference


class AddUserForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])


class EditForm(FlaskForm):
    """Edit g.user preferences"""
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])

    allergies = SelectMultipleField(
        'Allergies',
        coerce=int,  # Cast IDs to integers
        widget=ListWidget(prefix_label=False),  # Render as a list
        option_widget=CheckboxInput(),  # Render options as checkboxes
    )
    
    diet_prefs = SelectMultipleField(
        'Dietary Preferences',
        coerce=int,  # Cast IDs to integers
        widget=ListWidget(prefix_label=False),  # Render as a list
        option_widget=CheckboxInput(),  # Render options as checkboxes
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate the allergy choices from the database
        self.allergies.choices = [(None, 'Add Allergy')] + [(allergy.id, allergy.type)
                                                            for allergy in Allergy.query.all()]

        # Populate the diet preferences choices from the database
        self.diet_prefs.choices = [(None, 'Add Dietary Preference')] + [(diet.id, diet.type)
                                                                        for diet in DietaryPreference.query.all()]


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])


class IngredientSearchForm(FlaskForm):
    ingredients = StringField('Ingredients', validators=[DataRequired()])


class AddRecipeForm(FlaskForm):
    """Form for adding users."""

    title = StringField('Title', validators=[DataRequired()])
    photo_url = StringField('Recipe Photo', default=None,
                            validators=[Optional(), URL()])
    ingredients = TextAreaField('Ingredients', validators=[DataRequired()])
    instructions = TextAreaField('Instructions', validators=[DataRequired()])
