import server
import unittest
import json
from pymongo import MongoClient
import base64

test_trip = dict(name="My Trip", start="Joburg", destination="Cape Town", waypoints=["Durban", "Richards Bay"])

updated_trip = dict(name="My Trip", start="Pretoria", destination="Cape Town", waypoints=["Durban", "Richards Bay"])

test_user = dict(username="admin", password="secret")

name_pass = "admin:secret"
b64_str = base64.encodebytes(name_pass.encode("utf-8"))
full_str = "Basic " + b64_str.decode("utf-8").strip('\n')
rheaders = {"Authorization": full_str}


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
        response = self.app.post('/trips/', data=json.dumps(test_trip), content_type='application/json', headers=rheaders)

        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'application/json' in response.content_type
        assert 'My Trip' in responseJSON["name"]

    def test_putting_trip(self):  # Updating a trip
        post_response = self.app.post('/trips/', data=json.dumps(test_trip), content_type='application/json', headers=rheaders)
        postResponseJSON = json.loads(post_response.data.decode())
        postedObjectID = postResponseJSON["_id"]

        response = self.app.put('/trips/'+postedObjectID, data=json.dumps(updated_trip), content_type='application/json')
        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert "Pretoria" in responseJSON["start"]

    def test_getting_trip(self):
        response = self.app.post('/trips/', data=json.dumps(test_trip), content_type='application/json', headers=rheaders)

        postResponseJSON = json.loads(response.data.decode())
        postedObjectID = postResponseJSON["_id"]

        response = self.app.get('/trips/'+postedObjectID, headers=rheaders)
        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'My Trip' in responseJSON["name"]

    def test_getting_user_trips(self):
        response = self.app.post('/trips/', data=json.dumps(test_trip), content_type='application/json', headers=rheaders)
        response = self.app.post('/trips/', data=json.dumps(updated_trip), content_type='application/json', headers=rheaders)

        response = self.app.get('/trips/', headers=rheaders)
        responseJSON = json.loads(response.data.decode())

        self.assertEqual(response.status_code, 200)
        assert 'My Trip' in responseJSON[1]["name"]

    def test_deleting_trip(self):
        response = self.app.post('/trips/', data=json.dumps(test_trip), content_type='application/json', headers=rheaders)

        postResponseJSON = json.loads(response.data.decode())
        postedObjectID = postResponseJSON["_id"]

        response = self.app.delete('/trips/'+postedObjectID)

        self.assertEqual(response.status_code, 200)

    def test_getting_non_existent_trip(self):
        response = self.app.get('/trips/55f0cbb4236f44b7f0e3cb23', headers=rheaders)
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
