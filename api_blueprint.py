from flask import Blueprint, jsonify, request
from data_manager.sqlite_data_manager import SQLiteDataManager
from models.models import db


api = Blueprint('api', __name__)

data_manager = SQLiteDataManager(db)


@api.route('users', methods=['GET'])
def get_all_users():
    users = data_manager.get_all_users()
    return jsonify(users)

@api.route('users/<int:user_id>/movies', methods=['GET'])
def get_user_movies(user_id):
    user_movies = data_manager.get_user_movies(user_id)
    return jsonify(user_movies)

@api.route('/users/<int:user_id>/add_movie', methods=['POST'])
def add_movie_to_user(user_id):
    title = request.json['title']
    director = request.json['director']
    year = request.json['year']
    rating = request.json['rating']

    if not all([title, director, year, rating]):
        return jsonify({'message': 'Missing data.'}), 400
    
    movie_data = {'title': title, 'director': director, 'year': year, 'rating': rating}
    result = data_manager.add_movie(user_id, movie_data)

    if result:
        return jsonify({'message': 'Movie added.'})
    else:
        return jsonify({'message': 'Movie not added.'}), 404
    

@api.route('/add_user', methods=['POST'])
def add_user():
    user_name = request.json['name']
    user_email = request.json['email']
    user = data_manager.get_user_by_name(user_name)
    if user:
        return jsonify({'message': 'User already exists.'}), 409
    else:
        user = data_manager.add_user(user_name, user_email)
        return jsonify({'message': 'User added.'})

@api.route('/users/<int:user_id>/update_movie/<int:movie_id>', methods=['PUT'])
def update_movie(user_id, movie_id):
    movie_data = {
        "title": request.json['title'],
        "director": request.json['director'],
        "year": request.json['year'],
        "rating": request.json['rating']
    }
    result = data_manager.update_movie(user_id, movie_id, movie_data)

    if 'error' in result:
        return jsonify({'message': 'Movie not found.'}), 404
    else:
        return jsonify({'message': 'Movie updated.'})
        
@api.route('/users/<int:user_id>/delete_movie/<int:movie_id>', methods=['DELETE'])
def delete_movie(user_id, movie_id):
    result = data_manager.delete_movie(user_id, movie_id)
    if 'error' in result:
        return jsonify({'message': 'Movie not found.'}), 404
    else:
        return jsonify({'message': 'Movie deleted.'})

@api.route('/add_review/<int:user_id>/<int:movie_id>', methods=['POST'])
def add_review(user_id, movie_id):
    movie = data_manager.get_movie_by_id(user_id, movie_id)
    if movie:
        review_text = request.json['review_text']
        rating = request.json['rating']
        data_manager.add_review(user_id, movie_id, review_text, rating)
        return jsonify({'message': 'Review added.'})
    else:
        return jsonify({'message': 'Movie not found.'}), 404
    

@api.route('/users/<int:user_id>/reviews', methods=['GET'])
def get_user_reviews(user_id):
    user = data_manager.get_user_by_id(user_id)
    if user:
        reviews = data_manager.get_user_reviews(user_id)
        return jsonify(reviews)
    else:
        return jsonify({'message': 'User not found.'}), 404