from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, validators

MOVIE_DB_API_KEY = "c38110ce324d46ee83272ed81e474004"
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

##CREATE DB
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


##CREATE TABLE
#our new class, Movie() INHERITS all attrib. and functions of the db.Model class,
#plus the attributes we create.
class Movie(db.Model):
    #id: sets the attrib. name
    #Mapped[] creates metadata to hint at the data type most likely
    #mapped_column is a function of db.Model which our Movie() Class inherited
    #Integer is a class provided by SQLAlchemy's types module
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()

#this form populates on the /add page
#FlaskForm is a Flas-WTF base class from the library
#contains form classes for submit, validate, fields, ect
class FindMovieForm(FlaskForm):
    #StringField = <input type="text">
    #DataReuired ins built in flaskwtf validator, requires text to be present b4 submit
    title = StringField("Movie Title", validators=[DataRequired()])
    #SubmitField = <input type="submit"> = submission button
    submit = SubmitField("Add Movie")

class RateMovieForm(FlaskForm):
    # --- New Rating Field (Dropdown) ---
    # Create a list of tuples for the choices: (value, label)
    rating_choices = [
        ("10.0", "10"),
        ("9.0", "9"),
        ("8.0", "8"),
        ("7.0", "7"),
        ("6.0", "6"),
        ("5.0", "5"),
        ("4.0", "4"),
        ("3.0", "3"),
        ("2.0", "2"),
        ("1.0", "1"),
    ]

    rating = SelectField(
        label="Your Rating Out of 10",
        choices=rating_choices,
        validators=[validators.DataRequired()]
    )
    # -----------------------------------

    review = StringField("Your Review (optional)")
    submit = SubmitField("Done")

@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()  # convert ScalarResult to Python List

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    return render_template("index.html", movies=all_movies)

#"Add" Route
@app.route("/add", methods=["GET", "POST"])
def add_movie():
    #Form obj we created earlier
    form = FindMovieForm()

    if form.validate_on_submit():
        #form.title =  StringField("Movie Title", validators=[DataRequired()])
        #form.title.data = whatever string the user entered; the data contained in form.title
        movie_title = form.title.data
        #response is an instance of the requests.Response Class
        #response.url = {MOVIE_DB_SEARCH_URL}?api_key="{MOVIE_DB_API_KEY}"&"query"={movie_title}
        response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_DB_API_KEY, "query": movie_title})
        #store the JSON data of the response obj as a dict object (or list in some cases):
        #then get the VALUE of the KEY "results"
        data = response.json()["results"]
        #interupts execution of add_movie() to go to select.html page
        #select.html as an "options" variable
        #return line sets options=data=response.json()["results"] which renders the API's results list
        #url of select.html page is still /add because it is rendered within the /add route.
        return render_template("select.html", options=data)

    #Take the Python object currently stored in the variable form (right side) and make it available in the template under the new variable name form (left side).
    #form=form is more concise and it makes it clear that you are passing the same thing from py to html template
    return render_template("add.html", form=form)

#find route interactes with the api
@app.route("/find")
def find_movie():
    #after user selects movie, the API's "id" gets passed into the url from the select.html page
    #request.args.get reads the url and gets the id
    #code then queries the API to pull data assoc. with the API's movie's id
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        #requests.get() creates and returns a requests.Response object.
        #the object type of the response variable type is requests.Response, a class obj
        #Response is capitalized because it is the Class; a blueprint.
        #where as response.get is lower case because it is a instance or object of the class requests.Response
        #response.url = {movie_api_url}?api_key={MOVIE_DB_API_KEY}&language=en-US
        response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_API_KEY, "language": "en-US"})
        #converts data of the API into a dict or list depending on the data stored in the api
        data = response.json()
        #funnel contents of data obj into a special object that can be added to our database
        new_movie = Movie(
            #set title or db row to the VALUE of the KEY of the data dict, "title"
            title=data["title"],
            #The data in release_date includes month and day, we will want to get rid of.
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        #adds contents of new_movie to SQL db
        db.session.add(new_movie)
        db.session.commit()
        #after addng movie to db, it redirects to /edit to allow you to rate it
        return redirect(url_for("rate_movie", id=new_movie.id))

# Adding the Update functionality
@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)

#add the delete functionality
@app.route("/delete")
def delete_movie():
    #flask request object reads an incoming HTTP request
    #request.args points to the key-value pair eg id=12
    #reuests.path points to the path eg "/delete"
    movie_id = request.args.get("id")
    #db is an instance of Flask-SQLAlchemy
    #get_or_404 is a get with a built in error handling
    movie = db.get_or_404(Movie, movie_id)
    #db.session = temp container to keep track of queries / transactions
    db.session.delete(movie)
    db.session.commit()
    #redirects us to the url assoc. with the home() function
    #the url of the home() function is "/", or the root
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(debug=True)