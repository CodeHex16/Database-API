import unittest
from app import create_app, db
from app.models.user_model import User
from werkzeug.security import generate_password_hash, check_password_hash

class UserTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the test environment"""
        # Create a Flask app and configure it for testing
        self.app = create_app(True)
        self.client = self.app.test_client()
        # Create the database and tables
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up after each test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_user(self):
        """Test creating a user""" 
        response = self.client.post('/users/', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'pbkdf2:sha256:260000$xEjndHbYuDfUi2hU$aaf584bca9e1c0e54eba1a6389b843067c3e526b6f6c8efba46187ab0846094e'
        })
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('id', data)
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')


    def test_get_users(self):
        """Test retrieving all users"""
        # First, create a user
        self.client.post('/users/', json={
            'username': 'testuser1',
            'email': 'test1@example.com',
            'password': 'pbkdf2:sha256:260000$xEjndHbYuDfUi2hU$aaf584bca9e1c0e54eba1a6389b843067c3e526b6f6c8efba46187ab0846094e'
        })
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertGreater(len(data), 0)  # Ensure that we have at least one user

    def test_get_user(self):
        """Test retrieving a specific user by ID"""
        # First, create a user
        response = self.client.post('/users/', json={
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'pbkdf2:sha256:260000$xEjndHbYuDfUi2hU$aaf584bca9e1c0e54eba1a6389b843067c3e526b6f6c8efba46187ab0846094e'
        })
        user_id = response.get_json()['id']

        # Retrieve the created user by ID
        response = self.client.get(f'/users/{user_id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['username'], 'testuser2')
        self.assertEqual(data['email'], 'test2@example.com')

    def test_update_user(self):
        """Test updating a user"""
        # First, create a user
        response = self.client.post('/users/', json={
            'username': 'testuser3',
            'email': 'test3@example.com',
            'password': 'pbkdf2:sha256:260000$xEjndHbYuDfUi2hU$aaf584bca9e1c0e54eba1a6389b843067c3e526b6f6c8efba46187ab0846094e'
        })
        user_id = response.get_json()['id']

        # Update the user's username and email
        response = self.client.put(f'/users/{user_id}', json={
            'username': 'updateduser',
            'email': 'updated@example.com',
            'password': 'newpbkdf2:sha256:260000$xEjndHbYuDfUi2hU$aaf584bca9e1c0e54eba1a6389b843067c3e526b6f6c8efba46187ab0846094e'
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['username'], 'updateduser')
        self.assertEqual(data['email'], 'updated@example.com')

    def test_delete_user(self):
        """Test deleting a user"""
        # First, create a user
        response = self.client.post('/users/', json={
            'username': 'testuser4',
            'email': 'test4@example.com',
            'password': 'pbkdf2:sha256:260000$xEjndHbYuDfUi2hU$aaf584bca9e1c0e54eba1a6389b843067c3e526b6f6c8efba46187ab0846094e'
        })
        user_id = response.get_json()['id']

        # Delete the user
        response = self.client.delete(f'/users/{user_id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['message'], 'User deleted')

        # Ensure the user no longer exists
        response = self.client.get(f'/users/{user_id}')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data['error'], 'User not found')

if __name__ == '__main__':
    unittest.main()
