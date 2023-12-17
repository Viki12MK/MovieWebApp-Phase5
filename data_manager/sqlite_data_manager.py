from flask_sqlalchemy import SQLAlchemy
from .data_manager_interface import DataManagerInterface
from models.models import User, Movie, UserMoviesRelationship, Review


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
            return [{'id': movie.id, 'title': movie.title, 'director': movie.director, 
                 'year': movie.year, 'rating': movie.rating} for movie in user.movies]
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
            new_movie = Movie(**movie_data)
            user.movies.append(new_movie)
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
        
    def delete_user(self, user_id):
        user = User.query.get(user_id)
        if user:
            # Delete user 
            self.db.session.delete(user)
            self.db.session.commit()
            return {'message': 'User deleted successfully.'}
        return {'error': 'User not found.'}
    