###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, ValidationError # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required # Here, too
from flask_sqlalchemy import SQLAlchemy

import requests
import json
## App setup code
app = Flask(__name__)
app.debug = True

## All app.config values
app.config['SECRET_KEY'] = 'hardtoguessstring'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://postgres:0000@localhost/wwsleeMidTerm"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)



######################################
######## HELPER FXNS (If any) ########
######################################

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internalservererror(e):
    return render_template('500.html'), 500

owmkey = "6414e7704376b3841968b4f46522a771"

##################
##### MODELS #####
##################

class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)

class Pokemon(db.Model):
    __tablename__ = "pokemon"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))
    color = db.Column(db.String(64))
    game_id = db.Column(db.Integer)
    ref_id = db.Column(db.Integer,db.ForeignKey("colors.id"))

    def __repr__(self):
        return "{} (ID: {})".format(self.color, self.id)

class Colors(db.Model):
    __tablename__ = "colors"
    id = db.Column(db.Integer,primary_key=True)
    color = db.Column(db.String(64))
    color_id = db.relationship('Pokemon',backref='Colors')
    def __repr__(self):
        return "{}".format(self.color)

class Weather(db.Model):
    __tablename__ = "weather"
    id = db.Column(db.Integer,primary_key=True)
    location = db.Column(db.String(64))
    temperature = db.Column(db.Float)
    pressure = db.Column(db.Integer)
    humidity = db.Column(db.Integer)
    def __repr__(self):
        return "{}".format(self.weather)

###################
###### FORMS ######
###################

class NameForm(FlaskForm):
    def namevalidator(self, field):
        if len(str(field.data).split()) > 1:
            raise ValidationError("Your name has a space in it. Only one word names are acceptable.")
    name = StringField("Please enter your name.  ",validators=[Required(), namevalidator])
    submit = SubmitField()

class PokemonForm(FlaskForm):
    color = StringField("Please enter a color.  ",validators=[Required()])
    submit = SubmitField()

class WeatherForm(FlaskForm):
    location = StringField("Please enter a zip code.  ",validators=[Required()])
    submit = SubmitField()

#######################
###### VIEW FXNS ######
#######################

@app.route('/', methods=['GET', 'POST'])
def home():
    form = NameForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    if request.method == "POST":
        if form.validate_on_submit():
            print("working")
            name = form.name.data
            newname = Name(name = name)
            db.session.add(newname)
            db.session.commit()
            return redirect(url_for('all_names'))
        else:
            print("NOT WORKINGGG")
            flash(form.errors)
    return render_template('index.html',form=form)

@app.route('/names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html',names=names)


@app.route('/pokemon_enter')
def pokemon_enter():
    form = PokemonForm()
    return render_template('pokemon_enter.html',form = form)

@app.route('/pokemon_error')
def pokemon_error():
    form = PokemonForm()
    return render_template('pokemon_error.html',form = form)

@app.route('/pokemon_data')
def pokemon_data():
    form = PokemonForm()
    if request.method == "GET":
        color = request.args.get("color", "nothing")
        while True:
            colorcheck = Colors.query.filter_by(color = color).first()
            if colorcheck:
                base_url = "https://pokeapi.co/api/v2/pokemon-color/"
                new_url = base_url+color.lower()
                resp = requests.get(new_url)
                text = resp.text
                results = json.loads(text)['pokemon_species']
                break
            else:
                try:
                    print(color)
                    base_url = "https://pokeapi.co/api/v2/pokemon-color/"
                    new_url = base_url+color.lower()
                    resp = requests.get(new_url)
                    text = resp.text
                    results = json.loads(text)['pokemon_species']
                    newcolor = Colors(color = color)
                    db.session.add(newcolor)
                    db.session.commit()
                    break
                except ValueError:
                    return redirect(url_for('pokemon_error'))
                    break
    return render_template('pokemon_data.html', color = color, objects = results)

@app.route('/pokemon_data/<pokemon>')
def pokemon_details(pokemon):
    base_url = "https://pokeapi.co/api/v2/pokemon-species/"
    new_url = base_url+pokemon.lower()
    resp = requests.get(new_url)
    text = resp.text
    species_results = json.loads(text)

    base_url2 = "https://pokeapi.co/api/v2/pokemon/"
    new_url2 = base_url2+pokemon.lower()
    resp2 = requests.get(new_url2)
    text2 = resp2.text
    stat_results = json.loads(text2)

    pname = species_results['name']
    pcolor = species_results['color']['name']
    pgame_id = stat_results['id']
    ref_id = Colors.query.filter_by(color = pcolor.title()).first().id

    newpokemon = Pokemon(name = pname, color = pcolor, game_id = pgame_id, ref_id = ref_id)
    db.session.add(newpokemon)
    db.session.commit()

    return render_template('pokemon_detail.html', stat_objects = stat_results, species_object = species_results, ref_id = ref_id)

@app.route('/color_history')
def color_history():
    color_log = Colors.query.all()
    return render_template('pokemon_color_history.html',colors=color_log)

@app.route('/pokemon_history')
def pokemon_history():
    pokemon_log = Pokemon.query.all()
    return render_template('pokemon_history.html',pokemons=pokemon_log)

@app.route('/weather', methods=['GET', 'POST'])
def weather():
    form = WeatherForm()
    if request.method == "POST":
        if len(form.location.data) != 0:
            print("post")
            zipcode = form.location.data
            base_url = "http://api.openweathermap.org/data/2.5/weather?"
            parameters = {}
            parameters['zip'] = zipcode + ",us"
            parameters["appid"] = owmkey
            resp = requests.get(base_url, params = parameters)
            text = resp.text
            results = json.loads(text)

            l = results['name']
            t = results['main']['temp']
            p = results['main']['pressure']
            h = results['main']['humidity']
            weather_entry = Weather(location = l, temperature=t, pressure=p, humidity=h)
            db.session.add(weather_entry)
            db.session.commit()

            return render_template('weather.html',form = form, results = results)
        else:
            print("no entry yet")
            results = None
            return render_template('weather.html',form = form, results = None)
    else:
        print("nopost")
        results = None
        return render_template('weather.html',form = form, results = None)

@app.route('/weather_history')
def weather_history():
    weather_log = Weather.query.all()
    return render_template('weather_history.html',weather=weather_log)

## Code to run the application...

if __name__ == '__main__':
    db.create_all()
    app.run(use_reloader=True,debug=True)

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
