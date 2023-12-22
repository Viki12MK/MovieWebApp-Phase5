from flask import Flask, redirect, request, render_template, jsonify, url_for
from data_manager.sqlite_data_manager import SQLiteDataManager
from models.models import db
from api_blueprint import api
import os
import requests

app = Flask(__name__)
app.register_blueprint(api, url_prefix='/api')


# Create the 'data' directory if it doesn't exist
data_directory = os.path.join(os.getcwd(), 'data')
if not os.path.exists(data_directory):
    os.makedirs(data_directory)

# Set up the SQLAlchemy database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(data_directory, 'database.db')

# Initialize the SQLAlchemy instance with the Flask app
db.init_app(app)

with app.app_context():
    if not os.path.exists(os.path.join(data_directory, 'database.db')):
        db.create_all()

data_manager = SQLiteDataManager(db)


@app.route('/')
def home():
    """
    Home page route.

    Returns:
        Response: Rendered template for the home page.
    """
    return render_template('home.html')


@app.route('/users', methods=['GET'])
def get_users():
    """
    Route to display all users.

    Returns:
        Response: Rendered template displaying all users.
    """
    users = data_manager.get_all_users()
    return render_template('users.html', users=users)


@app.route('/user/<int:user_id>/movies', methods=['GET'])
def display_user_movies(user_id):
    """
    Route to display movies for a specific user.

    Args:
        user_id (int): User ID.

    Returns:
        Response: Rendered template displaying user movies.
    """
    user_movies = data_manager.get_user_movies(user_id)
    user = data_manager.get_user_by_id(user_id)
    if user_movies is None or user is None:
        return "User not found.", 404
    return render_template("user_movies.html", user_movies=user_movies, user_id=user_id)


@app.route('/user_movies/<int:user_id>', methods=['GET'])
def get_user_movies(user_id):
    """
    Route to get movies for a specific user.

    Args:
        user_id (int): User ID.

    Returns:
        Response: Rendered template displaying user movies.
    """
    print(f"DEBUG: Inside get_user_movies with user_id: {user_id}")
    user_movies = data_manager.get_user_movies(user_id)
    user = data_manager.get_user_by_id(user_id)
    
    if user_movies is None or user is None:
        print("DEBUG: User not found or no movies available.")
        return "User not found.", 404

    print("DEBUG: Before rendering template")
    return render_template("user_movies.html", user=user, user_movies=user_movies)



# app.py
from flask import jsonify, redirect, url_for

@app.route('/add_user', methods=["GET", "POST"])
def add_user():
    """
    Route to add a new user.

    Returns:
        Response: Redirect to the get_users route or an error message.
    """
    if request.method == "POST":
        user_name = request.form.get('name')
        email = request.form.get('email')

        if not user_name or not email:
            return jsonify({'error': 'User name or email is missing.'}), 400

        # Check if either the user_name or email already exists
        users = data_manager.get_all_users()
        for user in users:
            if user['name'] == user_name or user['email'] == email:
                return jsonify({'error': 'User already exists.'}), 409

        new_user = data_manager.add_user(user_name, email)
        return redirect(url_for('get_users'))

    # Handle GET request
    return render_template("add_user.html")



@app.route('/users/<int:user_id>/add_movie', methods=['GET', 'POST'])
def add_movie(user_id):
    """
    Route to add a movie for a specific user.

    Args:
        user_id (int): User ID.

    Returns:
        Response: Rendered template for adding a movie.
    """
    print(f"DEBUG: user_id in add_movie route: {user_id}")

    if request.method == 'POST':
        # Check if the user exists
        user_movies = data_manager.get_user_movies(user_id)
        user = data_manager.get_user_by_id(user_id)
        user_name = user.name if user else 'Unknown'

        if user_movies is None:
            return jsonify({'error': 'User not found'}), 404

        # Extract the movie title from the request's form data
        movie_title = request.form.get('title')

        # Check if the movie already exists for the user
        movie_exist = next((movie for movie in user_movies if movie['title'] == movie_title), None)

        if movie_exist:
            # Display information about the existing movie
            return render_template('add_movie.html', user_id=user_id, user_name=user_name, movie_exist=movie_exist,
                                   new_movie=None)
        else:
            # Fetch movie details from OMDb API
            omdb_api_key = '770a6d70'  
            omdb_api_url = f'http://www.omdbapi.com/?apikey={omdb_api_key}&t={movie_title}&plot=full'
            response = requests.get(omdb_api_url)
            movie_data_from_api = response.json()

            if response.status_code == 200 and movie_data_from_api['Response'] == 'True':
                # Add the movie to the user's list
                new_movie = data_manager.add_movie(user_id, movie_data_from_api)
                if new_movie is None:
                    return jsonify({'error': 'Failed to add movie to user.'}), 500

                # Redirect to user_movies.html after adding the movie
                return redirect(url_for('get_user_movies', user_id=user_id))
            else:
                 return jsonify({'error': 'Failed to fetch movie details from OMDb API.'}), 500

    else:
        # If the request is GET, render the template for adding a movie
        print(f"DEBUG: Rendering add_movie.html with user_id: {user_id}")
        user = data_manager.get_user_by_id(user_id)
        user_name = user.name if user else 'Unknown'
        return render_template('add_movie.html', user_id=user_id, user_name=user_name, movie_exist=None, new_movie=None)


@app.route('/users/<int:user_id>/update_movie/<int:movie_id>', methods=['GET', 'POST', 'PUT'])
def update_movie(user_id, movie_id):
    """
    Route to update a movie for a specific user.

    Args:
        user_id (int): User ID.
        movie_id (int): Movie ID.

    Returns:
        Response: Rendered template for updating a movie.
    """
    if request.method == 'GET':
        # Retrieve the movie details from the data manager and pass them to the template
        movie = data_manager.get_user_movie(user_id, movie_id)
        return render_template('update_movie.html', user_id=user_id, movie_id=movie_id, movie=movie)

    elif request.method == 'POST' or request.method == 'PUT':
        movie_data = request.form.to_dict()
        result = data_manager.update_movie(user_id, movie_id, movie_data)
        if 'message' in result and result['message'] == 'Movie updated successfully.':
            # If the movie was successfully updated, redirect to get_user_movies
            return redirect(url_for('get_user_movies', user_id=user_id))
        else:
            # If the movie update failed, display an error message or handle the error scenario here
            return render_template('update_movie.html', user_id=user_id, movie_id=movie_id, movie=None, updated=False)
    else:
        # Handle other methods if needed
        return "Method Not Allowed", 405
    

@app.route('/users/<int:user_id>/delete_movie/<int:movie_id>', methods=['GET', 'POST'])
def delete_movie(user_id, movie_id):
    """
    Route to delete a movie for a specific user.

    Args:
        user_id (int): User ID.
        movie_id (int): Movie ID.

    Returns:
        Response: Redirect to user_movies or render delete_movie template.
    """
    user = data_manager.get_user_by_id(user_id)
    if user:
        movie = data_manager.get_movie_by_id(user_id, movie_id)
        if movie:
            if request.method == 'POST':
                result = data_manager.delete_movie(user_id, movie_id)
                return redirect(url_for('get_user_movies', user_id=user_id))
                # return render_template('delete_movie.html', user=user, movie=movie, result=result)
            return render_template('delete_movie.html', user=user, movie=movie)
    return "User or movie not found.", 404


@app.route('/add_review/<int:user_id>/<int:movie_id>', methods=['GET', 'POST'])
def add_review(user_id, movie_id):
    """
    Route to add a review for a specific movie and user.

    Args:
        user_id (int): User ID.
        movie_id (int): Movie ID.

    Returns:
        Response: Rendered template for adding a review.
    """
    if request.method == 'POST':
        # Extract user_id and movie_id from the form data
        review_text = request.form.get('review_text')
        rating = request.form.get('rating')

        try:
            # Try converting user_id and movie_id to integers
            user_id = int(user_id)
            movie_id = int(movie_id)
        except ValueError:
            return "Invalid user_id or movie_id.", 400

        # Get user and movie information for display in the template
        user = data_manager.get_user_by_id(user_id)
        movie = data_manager.get_user_movie(user_id, movie_id)

        # Handle the case where user or movie is None
        if user is None or movie is None:
            return f"User or movie not found. user_id: {user_id}, movie_id: {movie_id}", 404

        # Add the review to the database
        new_review = data_manager.add_review(user_id, movie_id, review_text, rating)

        # Redirect to user_reviews.html after adding the review
        return redirect(url_for('get_user_reviews', user_id=user_id))

    elif request.method == 'GET':
        # Handle GET request
        user = data_manager.get_user_by_id(user_id)
        movie = data_manager.get_user_movie(user_id, movie_id)

        # Handle the case where user or movie is None
        if user is None or movie is None:
            return f"User or movie not found. user_id: {user_id}, movie_id: {movie_id}", 404

        # Retrieve all reviews for the movie when displaying the form
        reviews = data_manager.get_movie_reviews(movie_id)

        # Render the template with or without new_review
        return render_template('add_review.html', user=user, movie=movie, reviews=reviews)

    else:
        # Handle other methods if needed
        return "Method Not Allowed", 405


@app.route('/display_review/<int:user_id>/<int:movie_id>/<int:review_id>', methods=['GET'])
def display_review(user_id, movie_id, review_id):
    """
    Route to display a specific review for a movie and user.

    Args:
        user_id (int): User ID.
        movie_id (int): Movie ID.
        review_id (int): Review ID.

    Returns:
        Response: Rendered template displaying the review.
    """
    user = data_manager.get_user_by_id(user_id)
    movie = data_manager.get_user_movie(user_id, movie_id)
    review = data_manager.get_review_by_id(review_id)

    if user is None or movie is None or review is None:
        return "User, movie, or review not found.", 404

    return render_template('display_review.html', user=user, movie=movie, review=review)


def get_movie_reviews(user_id, movie_id):
    """
    Helper function to get all reviews for a specific movie.

    Args:
        user_id (int): User ID.
        movie_id (int): Movie ID.

    Returns:
        Response: Rendered template displaying movie reviews.
    """
    reviews = data_manager.get_movie_reviews(movie_id)
    movie = data_manager.get_user_movie(user_id, movie_id)

    if reviews is None or movie is None:
        return "Movie not found.", 404

    return render_template('user_reviews.html', user_id=user_id, movie=movie, reviews=reviews)


@app.route('/users/<int:user_id>/reviews', methods=['GET'])
def get_user_reviews(user_id):
    """
    Route to display all reviews for a specific user.

    Args:
        user_id (int): User ID.

    Returns:
        Response: Rendered template displaying user reviews.
    """
    try:
        user_movies, reviews = data_manager.get_user_reviews(user_id)
        print("DEBUG: user_movies:", user_movies)
        print("DEBUG: reviews:", reviews)
        user = data_manager.get_user_by_id(user_id)
        return render_template('user_reviews.html', user=user, user_movies=user_movies, reviews=reviews)
    except Exception as e:
        print("Error:", e)
        return "Internal Server Error", 500




@app.route('/movie_reviews')
def movie_reviews():
    """
    Route to display all movie reviews.

    Returns:
        Response: Rendered template displaying all movie reviews.
    """
    # Get all movie reviews
    all_movie_reviews = data_manager.get_all_movie_reviews()

    # Check if there are reviews available
    if not all_movie_reviews:
        return "No movie reviews available.", 404
    
    return render_template('movie_reviews.html', movie_reviews=all_movie_reviews)


@app.errorhandler(404)
def page_not_found(error):
    """
    Error handler for 404 Not Found.

    Args:
        error: The error message.

    Returns:
        Response: Rendered template for 404 error.
    """
    return render_template('404.html', error=error), 404


# Initialize the SQLiteDataManager with the SQLAlchemy db object
data_manager = SQLiteDataManager(db)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
