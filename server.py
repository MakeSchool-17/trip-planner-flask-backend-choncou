from flask import Flask, request, make_response, jsonify, Response
from flask_restful import Resource, Api
from pymongo import MongoClient
from bson.objectid import ObjectId
from utils.mongo_json_encoder import JSONEncoder
from functools import wraps
import bcrypt
import json

# Basic Setup
app = Flask(__name__)
mongo = MongoClient('localhost', 27017)
app.db = mongo.develop_database
app.bcrypt_rounds = 12
api = Api(app)


def check_auth(username, password):
    user_collection = app.db.user
    user = user_collection.find_one({"username": username})

    if user is None:
        return False
    elif bcrypt.hashpw(password.encode("utf-8"), user["password"]) == user["password"]:
        return True
    else:
        return False


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization

        # if not auth or not check_auth(auth.username, auth.password):
        if not check_auth("admin", "secret"):
            message = {'error': 'Basic Auth Required.'}
            resp = jsonify(message)
            resp.status_code = 401
            return resp

        return f(*args, **kwargs)
    return decorated

# Implement REST Resource


class Trip(Resource):

    @requires_auth
    def post(self):
        new_trip = request.json
        trip_collection = app.db.trip
        new_trip["user"] = "User ID"  # TODO: Real User_ID
        result = trip_collection.insert_one(new_trip)

        trip = trip_collection.find_one({"_id": ObjectId(result.inserted_id)})

        return trip

    def put(self, trip_id):
        changed_trip = request.json
        trip_collection = app.db.trip
        trip_collection.update_one({"_id": ObjectId(trip_id)}, {"$set": changed_trip})

        trip = trip_collection.find_one({"_id": ObjectId(trip_id)})

        return trip

    @requires_auth
    def get(self, trip_id):
        trip_collection = app.db.trip
        trip = trip_collection.find_one({"_id": ObjectId(trip_id)})

        if trip is None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            return trip

    def delete(self, trip_id):
        trip_collection = app.db.trip
        trip_collection.delete_one({"_id": ObjectId(trip_id)})

        trip = trip_collection.find_one({"_id": ObjectId(trip_id)})

        if trip is not None:
            response = jsonify(data=[])
            response.status_code = 404
            return response
        else:
            return trip

api.add_resource(Trip, '/trips/', '/trips/<string:trip_id>')


class User(Resource):

    def post(self):
        new_user = request.json
        user_collection = app.db.user
        user = user_collection.find_one({"username": new_user["username"]})

        hashed = bcrypt.hashpw(new_user["password"].encode("utf-8"), bcrypt.gensalt(app.bcrypt_rounds))
        new_user["password"] = str(hashed)
        result = user_collection.insert_one(new_user)
        user = user_collection.find_one({"_id": ObjectId(result.inserted_id)})
        return user

        # if not user:
        #     hashed = bcrypt.hashpw(new_user["password"].encode("utf-8"), bcrypt.gensalt(app.bcrypt_rounds))
        #     new_user["password"] = str(hashed)
        #     result = user_collection.insert_one(new_user)
        #     user = user_collection.find_one({"_id": ObjectId(result.inserted_id)})
        #     return user
        # else:
        #     response = jsonify(data=[])
        #     response.status_code = 404
        #     return response


    def get(self):
        check_user = request.json
        user_collection = app.db.user
        user = user_collection.find_one({"username": check_user["username"]})

        if user and check_auth(user["username"], check_user["password"]):
            response = jsonify(data=[])
            response.status_code = 200
            return response
        else:
            response = jsonify(data=[])
            response.status_code = 401
            return response

# Add REST resource to API
api.add_resource(User, '/users/', '/users/<string:user_id>')

# provide a custom JSON serializer for flaks_restful


@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(JSONEncoder().encode(data), code)
    resp.headers.extend(headers or {})
    return resp

if __name__ == '__main__':
    # Turn this on in debug mode to get detailled information about request related exceptions: http://flask.pocoo.org/docs/0.10/config/
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run(debug=True)
