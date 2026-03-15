import sys
import unittest
from unittest.mock import MagicMock, patch

# Start by mocking the MongoDB client before server import to prevent connection errors
with patch('pymongo.MongoClient') as mock_mongo:
    from backend.server import app, chat

class TestChatResilience(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.ctx = app.test_request_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    @patch('backend.server.session')
    @patch('backend.server.logs')
    @patch('backend.server.profiles')
    @patch('requests.post')
    def test_chat_error_handling(self, mock_post, mock_profiles, mock_logs, mock_session):
        # 1. Setup Mock Data
        mock_session.get.return_value = "test_user"
        mock_session.__contains__.return_value = True # for 'user_id' in session
        
        mock_profiles.find_one.return_value = {"full_name": "TestUser"}
        mock_logs.find.return_value.sort.return_value.limit.return_value = [] # No telemetry
        
        # 2. Mock a 401 Error from API (Case: Invalid Key)
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": {"message": "Invalid API Key"}}
        mock_post.return_value = mock_response
        
        # 3. Call the function with a request context
        with app.test_request_context(json={"message": "hello"}):
            response = chat()
            data = response[0].get_json()
        
        print(f"Result for 'hello': {data['reply']}")
        self.assertIn("Neural Nexus assistant", data['reply'])
        self.assertIn("API offline", data['reply'])

    @patch('backend.server.session')
    @patch('backend.server.logs')
    @patch('backend.server.profiles')
    @patch('requests.post')
    def test_fatigue_keyword_fallback(self, mock_post, mock_profiles, mock_logs, mock_session):
        # Setup for 'fatigue' query
        mock_session.get.return_value = "test_user"
        mock_session.__contains__.return_value = True
        
        mock_profiles.find_one.return_value = {"full_name": "TestUser"}
        
        # Mock some telemetry data
        mock_logs.find.return_value.sort.return_value.limit.return_value = [{"fatigue": 85, "distance": 40}]
        
        # Mock API error
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        with app.test_request_context(json={"message": "about my fatigue"}):
            response = chat()
            data = response[0].get_json()
            
        print(f"Result for 'fatigue': {data['reply']}")
        self.assertIn("85%", data['reply'])
        self.assertIn("high risk", data['reply'].lower())

if __name__ == "__main__":
    unittest.main()
