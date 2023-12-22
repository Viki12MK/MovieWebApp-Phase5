from flask_sqlalchemy import SQLAlchemy
from .data_manager_interface import DataManagerInterface
from models.models import User, Movie, UserMoviesRelationship, Review
# from sqlalchemy.exc import IntegrityError


class SQLiteDataManager(DataManagerInterface):
    def __init__(self, db):
        self.db = db
    

    def get_all_users(self):
        users = User.query.all()
        return [{'id': user.id, 'name': user.name, 'email': user.email} for user in users]

    
    def get_user_by_id(self, user_id):
        user = User.query.get(user_id)
        if user:
            return user
        return None
    
    def get_movie_by_id(self, user_id, movie_id):
        movies = self.get_user_movies(user_id)
        for movie in movies:
            if movie['id'] == movie_id:
                return movie
        return None
    
    def get_user_movie(self, user_id, movie_id):
        user = User.query.get(user_id)
        if user:
            movie = Movie.query.get(movie_id)
            if movie and movie in user.movies:
                return {
                    'id': movie.id,
                    'title': movie.title,
                    'director': movie.director,
                    'year': movie.year,
                    'rating': movie.rating
                }
        return None
        
       
    def get_user_movies(self, user_id):
        user = User.query.get(user_id)
        if user:
            movies = Movie.query.join(UserMoviesRelationship, (UserMoviesRelationship.movie_id == Movie.id)).filter_by(
                user_id=user_id).all()

            return [{'id': movie.id, 'title': movie.title, 'director': movie.director,
                 'year': movie.year, 'rating': movie.rating, 'poster': movie.poster} for movie in movies]
        return []
    
    def get_user_by_name(self, user_name):
        user = User.query.filter_by(name=user_name).first()
        return user
        

    def add_user(self, user_name, email):
       new_user = User(name=user_name, email=email)
       self.db.session.add(new_user)
       self.db.session.commit()
       return {'id': new_user.id, 'name': new_user.name, 'email': new_user.email}

    def add_movie(self, user_id, movie_data):
        user = self.get_user_by_id(user_id)

        if user:
            # Extract relevant movie data from the API response
            title = movie_data.get('Title')
            director = movie_data.get('Director')
            year = int(movie_data.get('Year'))
            rating = float(movie_data.get('imdbRating'))
            poster = movie_data.get('Poster')

            # Check if the movie already exists in the database
            existing_movie = Movie.query.filter_by(title=title, director=director, year=year, rating=rating).first()

            if existing_movie:
                # Check if the relationship already exists
                if existing_movie not in user.movies:
                    # Add the existing movie to the user's list
                    user.movies.append(existing_movie)

                # Create a new relationship if it doesn't exist
                if UserMoviesRelationship.query.filter_by(user_id=user.id, movie_id=existing_movie.id).first() is None:
                    relationship = UserMoviesRelationship(user_id=user.id, movie_id=existing_movie.id)
                    self.db.session.add(relationship)

                self.db.session.commit()

                # Return the existing movie
                return existing_movie
            else:
                # Check if the relationship already exists
                if Movie.query.filter(Movie.users.any(id=user_id)).filter_by(title=title).first():
                    return {'error': 'Movie already added to the user.'}
                
                # Create a new Movie instance
                new_movie = Movie(title=title, director=director, year=year, rating=rating, poster=poster)

                # Add the new movie to the user's list
                user.movies.append(new_movie)

                # Add the new movie to the database
                self.db.session.add(new_movie)
                self.db.session.commit()

                # Create a new relationship
                if UserMoviesRelationship.query.filter_by(user_id=user.id, movie_id=new_movie.id).first() is None:
                    relationship = UserMoviesRelationship(user_id=user.id, movie_id=new_movie.id)
                    self.db.session.add(relationship)

                self.db.session.commit()

                return new_movie
        else:
            return None
        

    def update_movie(self, user_id, movie_id, movie_data):
        user = User.query.get(user_id)
        if user:
            movie = Movie.query.get(movie_id)
            if movie:
                # Update movie attributes if present in movie_data
                movie.title = movie_data.get('title', movie.title)
                movie.director = movie_data.get('director', movie.director)
                movie.year = movie_data.get('year', movie.year)
                movie.rating = movie_data.get('rating', movie.rating)
                self.db.session.commit()
                return {'message': 'Movie updated successfully.'}
        return{'error': 'User or movie not found.'}
        

    def delete_movie(self, user_id, movie_id):
        user = User.query.get(user_id)
        if user:
            movie = Movie.query.get(movie_id)
            if movie:
                user.movies.remove(movie)
                self.db.session.commit()
                return {'message': 'Movie deleted successfully.'}
        return {'error': 'User or movie not found.'}
    
    def add_review(self, user_id, movie_id, review_text, rating):
        user = User.query.get(user_id)
        movie = Movie.query.get(movie_id)

        if user and movie:
            # Create a new Review instance and add it to the database
            new_review = Review(user_id=user.id, movie_id=movie.id, review_text=review_text, rating=rating)
            self.db.session.add(new_review)
            self.db.session.commit()
            return new_review
        return None
    
    def get_review_by_id(self, review_id):
        review = Review.query.get(review_id)
        return review
    
    def get_movie_reviews(self, movie_id):
        movie = Movie.query.get(movie_id)
        if movie:
            reviews =  Review.query.filter_by(movie_id=movie_id).all()
            return [{
                'id': review.id,
                'user_id': review.user_id,
                'review_text': review.review_text,
            } for review in reviews]
        return
    
    def get_user_reviews(self, user_id):
        user = User.query.get(user_id)
        if user:
            user_movies = self.get_user_movies(user_id)
            reviews = [{'id': review.id, 'movie_id': review.movie_id, 'review_text': review.review_text, 'rating': review.rating}
                        for review in user.reviews]
            
            if not reviews:
                return user_movies, None
            
            return user_movies, reviews
        return None, None

    def get_all_movie_reviews(self):
        reviews = Review.query.all()
        all_movie_reviews = []

        for review in reviews:
            movie = Movie.query.get(review.movie_id)
            if movie:
                user = User.query.get(review.user_id)
                if user:
                    review_data = {
                        'user_name': user.name,
                        'movie_title': movie.title,
                        'review_text': review.review_text,
                        'rating': review.rating
                    }
                    all_movie_reviews.append(review_data)
        
        return all_movie_reviews
        
    
