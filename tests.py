import server
import unittest
import json
from pymongo import MongoClient
import base64

test_trip = dict(name="My Trip", start="Joburg", destination="Cape Town", waypoints=["Durban", "Richards Bay"])

updated_trip = dict(name="My Trip", start="Pretoria", destination="Cape Town", waypoints=["Durban", "Richards Bay"])

test_user = dict(username="admin", password="secret")

def make_auth_header(username="ryankim", password="12341234"):
    string = username + ":" + password
    encoded_base64 = base64.b64encode(string.encode("utf-8"))
    decoded_base64 = encoded_base64.decode("utf-8")
    auth_header = "Authorization: Basic " + decoded_base64
    return auth_header

headers = {"content-type": "application/json", "Authentication": make_auth_header()}


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        self.app = server.app.test_client()
        # Run app in testing mode to retrieve exceptions and stack traces
        server.app.config['TESTING'] = True

        # Inject test database into application
        mongo = MongoClient('localhost', 27017)
        db = mongo.test_database
        server.app.db = db

        # Drop collection (significantly faster than dropping entire db)
        db.drop_collection('trip')

    # Trip tests

    def test_posting_trip(self):
        response = self.app.post('/trips/', data=json.dumps(test_trip), content_type='application/json')

        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'application/json' in response.content_type
        assert 'My Trip' in responseJSON["name"]

    def test_putting_trip(self):  # Updating a trip
        post_response = self.app.post('/trips/', data=json.dumps(test_trip), content_type='application/json')
        postResponseJSON = json.loads(post_response.data.decode())
        postedObjectID = postResponseJSON["_id"]

        response = self.app.put('/trips/'+postedObjectID, data=json.dumps(updated_trip), content_type='application/json')
        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert "Pretoria" in responseJSON["start"]

    def test_getting_trip(self):
        response = self.app.post('/trips/', data=json.dumps(test_trip), content_type='application/json')

        postResponseJSON = json.loads(response.data.decode())
        postedObjectID = postResponseJSON["_id"]

        response = self.app.get('/trips/'+postedObjectID)
        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'My Trip' in responseJSON["name"]

    def test_getting_user_trips(self):
        response = self.app.post('/trips/', data=json.dumps(test_trip), content_type='application/json')
        response = self.app.post('/trips/', data=json.dumps(test_trip), content_type='application/json')

        response = self.app.get('/trips/')
        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'My Trip' in responseJSON[0]["name"]

    def test_deleting_trip(self):
        response = self.app.post('/trips/', data=json.dumps(test_trip), content_type='application/json')

        postResponseJSON = json.loads(response.data.decode())
        postedObjectID = postResponseJSON["_id"]

        response = self.app.delete('/trips/'+postedObjectID)

        self.assertEqual(response.status_code, 200)

    def test_getting_non_existent_trip(self):
        response = self.app.get('/trips/55f0cbb4236f44b7f0e3cb23')
        self.assertEqual(response.status_code, 404)

    # User tests
    def test_posting_user(self):
        response = self.app.post('/users/', data=json.dumps(test_user), content_type='application/json')

        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'application/json' in response.content_type
        assert 'admin' in responseJSON["username"]

    def test_validating_user(self):
        response = self.app.post('/users/', data=json.dumps(test_user), content_type='application/json')

        # postResponseJSON = json.loads(response.data.decode())
        # postedObjectID = postResponseJSON["_id"]

        response = self.app.get('/users/', data=json.dumps(test_user), content_type='application/json')
        # responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
