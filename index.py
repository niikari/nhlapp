
from flask import Flask, render_template, redirect, flash, session, abort, request
from flask_sqlalchemy import SQLAlchemy

from flask_wtf import FlaskForm
from wtforms.ext.sqlalchemy.orm import model_form

from wtforms import StringField, PasswordField, validators, IntegerField
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime

app = Flask(__name__)
app.secret_key = "ib)aht~eiJu%h=oopoing7de0ca9eingieLaeth"
#app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql:///niileswsgi'
db = SQLAlchemy(app)

# käyttäjät
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    passwordHash = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False, default='user')

    def setPassword(self, password):
        self.passwordHash = generate_password_hash(password) 

    def checkPassword(self, password):
        return check_password_hash(self.passwordHash, password)

    def __repr__(self):
        return self.username

class UserForm(FlaskForm):
    username = StringField("Käyttäjänimi", validators=[validators.InputRequired("Käyttäjänimi on pakollinen")])
    password = PasswordField("Salasana", validators = [validators.InputRequired("Salasana on pakko valita")])

class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Integer, nullable=False)
    players = db.Column(db.Integer, nullable=False) # eli kuinka monta pelaajaa turnauksessa
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('users', lazy=True))
    
#TournamentForm = model_form(Tournament, base_class=FlaskForm, db_session = db.session)

class TournamentForm(FlaskForm):
    name = StringField("Turnauksen nimi", validators=[validators.InputRequired("Nimi on pakollinen")])
    players = IntegerField("Monta pelaajaa?", validators=[validators.InputRequired("Pelaajia on pakko olla")])

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    tournament = db.relationship('Tournament', backref=db.backref('tournaments', lazy=True))

    def __repr__(self):
        return self.name

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    winner = db.Column(db.Integer)
    points = db.Column(db.Integer)
    player1 = db.Column(db.Integer)
    player2 = db.Column(db.Integer)
    score = db.Column(db.String, default='0 - 0')
    

@app.before_first_request
def initDb():
    db.create_all()
    user = User()
    user.username = 'admin'
    user.setPassword('admin')
    user.role = 'admin'
    db.session.add(user)

    user2 = User()
    user2.username = 'tomi'
    user2.setPassword('tomi')
    db.session.add(user2)

    tournament = Tournament(name="Hegistä", user=user, players=3)
    db.session.add(tournament)

    player = Player(name="pelaaja1", tournament = tournament)
    db.session.add(player)

    player2 = Player(name="pelaaja2", tournament=tournament)
    db.session.add(player2)
    
    db.session.commit()

# käyttäjiä varten polkuja ja tietojen lisäämistä
@app.route("/users/register", methods=["GET", "POST"])
def userRegister():
    form = UserForm()
    user = User()

    if form.validate_on_submit():
        user.username = form.username.data

        if User.query.filter_by(username=user.username).first():
            flash("Käyttäjätunnus on varattu, valitse toinen.")
            return redirect("/users/register")

        user.setPassword(form.password.data)
        db.session.add(user)
        db.session.commit()
        session["uid"] = user.id
        flash("Terveuloa mukaan, eiköhän aleta luomaan turnauksia!")        
        return redirect("/")
    
    return render_template("register.html", form = form, button = "Rekisteröidy")

@app.route("/users/login", methods=["GET", "POST"])
def userLogin():
    user = User()
    form = UserForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        password = form.password.data

        if not user:
            flash("Käyttänimi tai salasana väärin, yritä uudelleen tai rekisteröidy")
            return redirect("/users/login")
        if not user.checkPassword(password):
            flash("Käyttänimi tai salasana väärin, yritä uudelleen tai rekisteröidy")
            return redirect("/users/login")    
        else:
            flash("Tervetuloa pelaamaan änäriä helposti")
            session["uid"] = user.id
            return redirect("/")    
        
    
    return render_template("login.html", form = form, button = "Kirjaudu")

@app.route("/users/logout")
def userLogout():
    session["uid"] = None
    flash("Kirjauduit ulos, pelaillaan taas")
    return redirect("/")

def currentUser():
    try:
        uid = int(session["uid"])
    except:
        return None

    return User.query.get(uid)

def loginRequired():
    if not currentUser():
        abort(403)

app.jinja_env.globals["currentUser"] = currentUser

# turnauksia varten polkuja

@app.route("/tournament/add", methods=["GET", "POST"])
def tournament():
    loginRequired()
    form = TournamentForm()
    tournament = Tournament()
    
    if form.validate_on_submit():
        tournament.name = form.name.data
        tournament.players = form.players.data
        tournament.user = currentUser()
        db.session.add(tournament)
        db.session.commit()
        flash("Turnaus luotu")
        ad = f"/tournament/edit/{tournament.id}"
        return redirect(ad)    
    
    return render_template("new.html", form = form, button = "Luo uusi")

def usersTournaments():
    tournaments = []
    if currentUser():
        user = currentUser()
        for tournament in Tournament.query.all():
            if tournament.user_id == user.id:
                tournaments.append(tournament)

    return tournaments

def getPlayers(id):
    players = []
    for player in Player.query.all():
        if player.tournament_id == id:
            players.append(player)

    return players

#def getGames(id):
#    games = []
#
#    for game in Game.query.all():
#        if game.tournament_id == id:
#            games.append(game)
#
#    return games

@app.route("/tournament/edit/<int:id>", methods=["GET", "POST"])
def editTournament(id):
    loginRequired()
    tournament = Tournament.query.get_or_404(id)
    players = tournament.players

    if request.form:
        for i in request.form:
            player = Player(name = request.form.get(i), tournament = tournament)
            db.session.add(player)

        db.session.commit()
        flash("Pelaajat lisätty onnistuneesti.")
        ad = f"/tournament/game/{tournament.id}"
        return redirect(ad)
            
    return render_template("edit.html", players=players, button="Vahvista", tournament = tournament.name)

@app.route("/tournament/game/<int:id>")
def tournamentGames(id):
    loginRequired()
    players = getPlayers(id)
    tournament = Tournament.query.get_or_404(id)
    games = []
    
    for player in players:
        games.append(player)
    
    # alla testiä varten
    
    #for player in players:
    #    game = Game(player1 = player.name)                                
    
    return render_template("game.html", tournament = tournament.name, games = games, id = id)

@app.route("/tournament/delete/<int:id>")
def deleteTournament(id):
    tournament = Tournament.query.get_or_404(id)

    players = getPlayers(id)
    for player in players:
        db.session.delete(player)
    
    db.session.delete(tournament)
    db.session.commit()
    flash("Turnaus poistettu onnistuneesti, uutta pötkä pesään")
    return redirect("/")

@app.route("/")
def index():
    tournaments = usersTournaments()    
    return render_template("index.html", tournaments = tournaments)

## Tänne alas errorit
@app.errorhandler(403)
def error403(e):
    flash("Kirjaudu sisään tai rekisteröidy ennen aloittamista")
    return redirect("/users/login")

@app.errorhandler(404)
def error404(e):
    flash("Hupsista, jokin meni pieleen eikä sivua löytynyt...")
    return redirect("/")

if __name__ == "__main__":
    app.run()















