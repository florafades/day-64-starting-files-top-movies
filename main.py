from flask import Flask, render_template, redirect, url_for, request, session
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
import os
import uuid

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
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///movies.db')
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
    session_id: Mapped[str] = mapped_column(String(100), nullable=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
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
    # Generate a session ID if this is a new visitor
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    
    current_session_id = session["session_id"]

    # 1. Sort the query by Movie.rating in DESCENDING order (highest rating first).
    # Only fetch movies belonging to this session
    result = db.session.execute(db.select(Movie).where(Movie.session_id == current_session_id).order_by(db.desc(Movie.rating)))
    all_movies = result.scalars().all()  # convert ScalarResult to Python List

    # 2. Update the ranking logic: 
    # Since the list is now sorted high-to-low, the ranking calculation needs to be reversed
    # so the first movie gets ranking 1, second gets 2, etc.
    for i in range(len(all_movies)):
        all_movies[i].ranking = i + 1  # The first item (i=0) gets rank 1
    
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
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_API_KEY, "language": "en-US"})
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"],
            session_id=session.get("session_id")  # 👈 this is the only new line
        )
        db.session.add(new_movie)
        db.session.commit()
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