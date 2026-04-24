from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField, DateTimeField, SelectField
from wtforms.validators import DataRequired, Length

# Formulaire d'inscription
class RegistrationForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=4, max=150)])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('S\'inscrire')

# Formulaire de connexion
class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')

# Formulaire pour ajouter/modifier un concert
class ConcertForm(FlaskForm):
    nom = StringField('Nom du concert', validators=[DataRequired()])
    date_concert = DateTimeField('Date et Heure (AAAA-MM-JJ HH:MM:SS)', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()])
    lieu = StringField('Lieu', validators=[DataRequired()])
    type_musique = StringField('Genre musical', validators=[DataRequired()])
    places_totales = IntegerField('Nombre de places totales', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Enregistrer le concert')

# Formulaire pour ajouter/modifier une actualité
class ActualiteForm(FlaskForm):
    titre = StringField('Titre de l\'article', validators=[DataRequired()])
    contenu = TextAreaField('Contenu de l\'article', validators=[DataRequired()])
    categorie_id = SelectField('Catégorie', coerce=int) 
    submit = SubmitField('Publier l\'actualité')

# Formulaire pour les commentaires
class CommentaireForm(FlaskForm):
    contenu = TextAreaField('Mon commentaire', validators=[DataRequired()])
    submit = SubmitField('Envoyer')