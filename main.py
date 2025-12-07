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
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()

## After adding the new_movie the code needs to be commented out/deleted.
## So you are not trying to add the same movie twice. The db will reject non-unique movie titles.
# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# with app.app_context():
#     db.session.add(new_movie)
#     db.session.commit()
# second_movie = Movie(
#     title="Avatar The Way of Water",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     rating=7.3,
#     ranking=9,
#     review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )
# with app.app_context():
#     db.session.add(second_movie)
#     db.session.commit()

with app.app_context():
    db.create_all()

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

    review = StringField("Your Review")
    submit = SubmitField("Done")

@app.route("/")
def home():
    #runs SQL query, a SELECT statement
    result = db.session.execute(db.select(Movie))
    #convert query results into usable py obj
    all_movies = result.scalars().all()
    return render_template("index.html", movies=all_movies)

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
    #flask request object reads and incoming HTTP request
    #request.args points to the key-value pair eg id=12
    #reuests.path points to the path eg "/delete"
    movie_id = request.args.get("id")
    #db is an instance of Flask-SQLAlchemy
    #get_or_404 is a get with a built in error handling
    movie = db.get_or_404(Movie, movie_id)
    #db.session = temp container to keep track of queries / transactions
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))





if __name__ == '__main__':
    app.run(debug=True)