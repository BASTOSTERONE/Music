from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from forms import RegistrationForm, LoginForm, ConcertForm, ActualiteForm, CommentaireForm
import requests
from datetime import timedelta

# --- 1. CONFIGURATION ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'tous-pour-la-musique'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:admin@localhost/musique_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- 2. MODÈLES (BASE DE DONNÉES) ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Categorie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    actualites = db.relationship('Actualite', backref='categorie', lazy=True)

class Actualite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date_publication = db.Column(db.DateTime, default=datetime.utcnow)
    categorie_id = db.Column(db.Integer, db.ForeignKey('categorie.id'), nullable=False)

class Concert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    date_concert = db.Column(db.DateTime, nullable=False)
    lieu = db.Column(db.String(150), nullable=False)
    type_musique = db.Column(db.String(50))
    places_totales = db.Column(db.Integer, nullable=False)
    places_dispos = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    avis_redacteur = db.Column(db.Text)
    est_passe = db.Column(db.Boolean, default=False)
    reservations = db.relationship('Reservation', backref='concert', lazy=True)
    commentaires = db.relationship('Commentaire', backref='concert', lazy=True)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nb_places = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    concert_id = db.Column(db.Integer, db.ForeignKey('concert.id'), nullable=False)

class Commentaire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contenu = db.Column(db.Text, nullable=False)
    date_post = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    concert_id = db.Column(db.Integer, db.ForeignKey('concert.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('commentaires', lazy=True))

# --- 3. ROUTES ---

@app.route('/')
def index():
    concerts = Concert.query.filter_by(est_passe=False).order_by(Concert.date_concert.asc()).limit(5).all()
    actualites = Actualite.query.order_by(Actualite.date_publication.desc()).limit(5).all()
    return render_template('index.html', concerts=concerts, actualites=actualites)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user_exists = User.query.filter_by(username=form.username.data).first()
        if user_exists:
            flash("Ce nom d'utilisateur est déjà pris.", "danger")
        else:
            hashed_password = generate_password_hash(form.password.data)
            new_user = User(username=form.username.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash("Compte créé avec succès ! Vous pouvez vous connecter.", "success")
            return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Connexion réussie !", "success")
            return redirect(url_for('index'))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/init_data')
def init_data():
    if Categorie.query.first():
        flash("Les données existent déjà !", "warning")
        return redirect(url_for('index'))

    admin_existe = User.query.filter_by(username='Admin').first()
    if not admin_existe:
        mdp_hash = generate_password_hash('admin')
        compte_admin = User(username='Admin', password=mdp_hash, is_admin=True)
        db.session.add(compte_admin)

    cat_jazz = Categorie(nom="Jazz")
    cat_rock = Categorie(nom="Rock")
    cat_electro = Categorie(nom="Electro")
    db.session.add_all([cat_jazz, cat_rock, cat_electro])
    db.session.commit()

    actu1 = Actualite(titre="Le 01/07/2024 : Musilac", contenu="Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.", categorie_id=cat_rock.id)
    actu2 = Actualite(titre="Festival Jazz à Vienne : Le programme complet", contenu="Découvrez les têtes d'affiche de cette nouvelle édition...", categorie_id=cat_jazz.id)
    db.session.add_all([actu1, actu2])

    from datetime import datetime
    c1 = Concert(nom="Arctic Monkeys", date_concert=datetime(2026, 4, 28, 20, 0), lieu="Lyon", type_musique="Rock", places_totales=5000, places_dispos=4000, description="La tournée européenne passe par la région !", est_passe=False)
    c2 = Concert(nom="Daft Punk Tribute", date_concert=datetime(2026, 8, 15, 23, 0), lieu="Annecy", type_musique="Electro", places_totales=1500, places_dispos=1500, description="Une nuit inoubliable.", est_passe=False)
    # Correction de l'année 202 ici :
    c3 = Concert(nom="Marcus Miller", date_concert=datetime(2026, 5, 7, 20, 30), lieu="Chambéry", type_musique="Jazz", places_totales=800, places_dispos=0, description="Concert exceptionnel du maître de la basse.", est_passe=True)
    db.session.add_all([c1, c2, c3])

    db.session.commit()
    flash("Données de test et compte Admin générés avec succès ! 🎸", "success")
    return redirect(url_for('index'))
# --- ROUTE DES CONCERTS ---
@app.route('/concerts')
def concerts():
    query = Concert.query.filter_by(est_passe=False)
    
    filtre_type = request.args.get('type')
    filtre_lieu = request.args.get('lieu')
    
    if filtre_type:
        query = query.filter_by(type_musique=filtre_type)
    if filtre_lieu:
        query = query.filter_by(lieu=filtre_lieu)
        
    liste_concerts = query.order_by(Concert.date_concert.asc()).all()
    
    lieux_uniques = [l[0] for l in db.session.query(Concert.lieu).distinct().all()]
    types_uniques = [t[0] for t in db.session.query(Concert.type_musique).distinct().all()]
    
    return render_template('concerts.html', 
                           concerts=liste_concerts, 
                           lieux=lieux_uniques, 
                           types=types_uniques)

# --- ROUTE POUR RÉSERVER DES PLACES ---

@app.route('/reserver/<int:id_concert>', methods=['POST'])
@login_required
def reserver(id_concert):
    concert = Concert.query.get_or_404(id_concert)

    nb_places = int(request.form.get('nb_places', 1))

    if nb_places <= 0:
        flash("Veuillez demander au moins 1 place.", "danger")
    elif concert.places_dispos >= nb_places:
        nouvelle_resa = Reservation(nb_places=nb_places, user_id=current_user.id, concert_id=concert.id)

        concert.places_dispos -= nb_places
        
        db.session.add(nouvelle_resa)
        db.session.commit()
        
        flash(f"Succès ! {nb_places} place(s) réservée(s) pour {concert.nom}.", "success")
    else:
        flash("Désolé, il n'y a pas assez de places disponibles pour ce concert.", "danger")
        
    return redirect(url_for('concerts'))


# --- ROUTE DU PROFIL UTILISATEUR ---

@app.route('/profil')
@login_required
def profil():
    mes_reservations = Reservation.query.join(Concert).filter(Reservation.user_id == current_user.id).order_by(Concert.date_concert.asc()).all()
    
    return render_template('profil.html', reservations=mes_reservations)

# --- ROUTE ADMINISTRATION ---

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash("Accès refusé. Vous n'avez pas les droits d'administration.", "danger")
        return redirect(url_for('index'))
        
    tous_les_concerts = Concert.query.order_by(Concert.date_concert.desc()).all()
    toutes_les_actus = Actualite.query.order_by(Actualite.date_publication.desc()).all()
    toutes_les_categories = Categorie.query.all()
    
    return render_template('admin.html', concerts=tous_les_concerts, actualites=toutes_les_actus, categories=toutes_les_categories)

# --- AJOUTER UN CONCERT ---
@app.route('/admin/concert/add', methods=['GET', 'POST'])
@login_required
def admin_add_concert():
    if not current_user.is_admin: return redirect(url_for('index'))
    
    form = ConcertForm()
    if form.validate_on_submit():
        nouveau_c = Concert(
            nom=form.nom.data, 
            date_concert=form.date_concert.data,
            lieu=form.lieu.data,
            type_musique=form.type_musique.data,
            places_totales=form.places_totales.data,
            places_dispos=form.places_totales.data,
            description=form.description.data
        )
        db.session.add(nouveau_c)
        db.session.commit()
        flash("Concert ajouté !", "success")
        return redirect(url_for('admin'))
    return render_template('admin_form.html', form=form, title="Ajouter un Concert")

# --- AJOUTER UNE ACTUALITÉ ---
@app.route('/admin/actualite/add', methods=['GET', 'POST'])
@login_required
def admin_add_actualite():
    if not current_user.is_admin: return redirect(url_for('index'))
    
    form = ActualiteForm()
    form.categorie_id.choices = [(c.id, c.nom) for c in Categorie.query.all()]
    
    if form.validate_on_submit():
        nouvelle_a = Actualite(
            titre=form.titre.data,
            contenu=form.contenu.data,
            categorie_id=form.categorie_id.data
        )
        db.session.add(nouvelle_a)
        db.session.commit()
        flash("Actualité publiée !", "success")
        return redirect(url_for('admin'))
    return render_template('admin_form.html', form=form, title="Rédiger une Actualité")

# --- SUPPRIMER (CONCERT OU ACTU) ---
@app.route('/admin/delete/<string:type>/<int:id>')
@login_required
def admin_delete(type, id):
    if not current_user.is_admin: return redirect(url_for('index'))
    
    if type == 'concert':
        obj = Concert.query.get(id)
    else:
        obj = Actualite.query.get(id)
        
    if obj:
        db.session.delete(obj)
        db.session.commit()
        flash("Suppression réussie.", "success")
    return redirect(url_for('admin'))

# --- MODIFIER UN CONCERT ---
@app.route('/admin/concert/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_concert(id):
    if not current_user.is_admin: return redirect(url_for('index'))

    concert = Concert.query.get_or_404(id)

    form = ConcertForm(obj=concert)
    
    if form.validate_on_submit():
        concert.nom = form.nom.data
        concert.date_concert = form.date_concert.data
        concert.lieu = form.lieu.data
        concert.type_musique = form.type_musique.data
        concert.places_totales = form.places_totales.data
        concert.description = form.description.data
        concert.avis_redacteur = form.avis_redacteur.data
        
        db.session.commit()
        flash("Le concert a bien été modifié !", "success")
        return redirect(url_for('admin'))
        
    return render_template('admin_form.html', form=form, title="Modifier un Concert")

# --- MODIFIER UNE ACTUALITÉ ---
@app.route('/admin/actualite/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_actualite(id):
    if not current_user.is_admin: return redirect(url_for('index'))
    
    actu = Actualite.query.get_or_404(id)
    form = ActualiteForm(obj=actu)
    form.categorie_id.choices = [(c.id, c.nom) for c in Categorie.query.all()]
    
    if form.validate_on_submit():
        actu.titre = form.titre.data
        actu.contenu = form.contenu.data
        actu.categorie_id = form.categorie_id.data
        
        db.session.commit()
        flash("L'actualité a bien été modifiée !", "success")
        return redirect(url_for('admin'))
        
    return render_template('admin_form.html', form=form, title="Modifier une Actualité")


# --- PAGE DÉTAIL D'UN CONCERT ET COMMENTAIRES ---

@app.route('/concert/<int:id>', methods=['GET', 'POST'])
def concert_detail(id):
    concert = Concert.query.get_or_404(id)
    form = CommentaireForm()
    
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Vous devez être connecté pour commenter.", "danger")
            return redirect(url_for('login'))
            
        nouveau_com = Commentaire(contenu=form.contenu.data, user_id=current_user.id, concert_id=concert.id)
        db.session.add(nouveau_com)
        db.session.commit()
        flash("Votre commentaire a bien été posté !", "success")
        return redirect(url_for('concert_detail', id=concert.id))
        
    commentaires = Commentaire.query.filter_by(concert_id=concert.id).order_by(Commentaire.date_post.desc()).all()
    
    # --- LOGIQUE MÉTÉO ---
    meteo = None
    maintenant = datetime.utcnow()
    if not concert.est_passe and concert.date_concert > maintenant:
        jours_restants = (concert.date_concert - maintenant).days
        if jours_restants <= 15:
            meteo = get_meteo(concert.lieu, concert.date_concert)
            
    return render_template('concert_detail.html', concert=concert, form=form, commentaires=commentaires, meteo=meteo)

def get_meteo(ville, date_concert):
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={ville}&count=1&language=fr"
        geo_rep = requests.get(geo_url).json()
        
        if not geo_rep.get('results'): 
            return None
            
        lat = geo_rep['results'][0]['latitude']
        lon = geo_rep['results'][0]['longitude']

        meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=Europe/Paris&forecast_days=16"
        meteo_rep = requests.get(meteo_url).json()

        date_str = date_concert.strftime('%Y-%m-%d')
        if date_str in meteo_rep['daily']['time']:
            idx = meteo_rep['daily']['time'].index(date_str)
            t_max = meteo_rep['daily']['temperature_2m_max'][idx]
            t_min = meteo_rep['daily']['temperature_2m_min'][idx]
            code = meteo_rep['daily']['weathercode'][idx]

            if code < 3: etat = "☀️ Ensoleillé"
            elif code < 50: etat = "☁️ Nuageux"
            elif code < 70: etat = "🌧️ Pluvieux"
            else: etat = "⛈️ Orage / Neige"
                
            return {"max": t_max, "min": t_min, "etat": etat}
    except:
        return None
    return None

@app.route('/actualites')
@app.route('/actualites/<int:id_cat>')
def actualites(id_cat=None):
    if id_cat:
        categorie = Categorie.query.get_or_404(id_cat)
        liste_actus = Actualite.query.filter_by(categorie_id=id_cat).order_by(Actualite.date_publication.desc()).all()
        titre_page = f"Actualités {categorie.nom}"
    else:
        liste_actus = Actualite.query.order_by(Actualite.date_publication.desc()).all()
        titre_page = "Toutes les Actualités"
        
    return render_template('actualites.html', actus=liste_actus, titre=titre_page)

# --- 4. LANCEMENT ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')