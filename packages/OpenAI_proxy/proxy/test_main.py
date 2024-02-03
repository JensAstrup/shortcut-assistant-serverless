from unittest import TestCase
from unittest.mock import patch, MagicMock
import os

from __main__ import main


class MainFunctionTestCase(TestCase):
    def setUp(self):
        self.event = {"description": "test description"}
        self.context = MagicMock(
            activation_id="activation_id",
            api_host="api_host",
            api_key="api_key",
            deadline="deadline",
            function_name="function_name",
            function_version="function_version",
            namespace="namespace",
            request_id="request_id"
        )
        os.environ["OPENAI_API_TOKEN"] = "fake_token"

    @patch("main.requests.post")
    @patch("main.logger.debug")
    def test_main__successful_response(self, _, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "response content"}}
            ]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        expected_response = {
            "body": {
                "description": "test description",
                "content": "response content"
            }
        }

        response = main(self.event, self.context)

        self.assertEqual(response, expected_response)
        mock_post.assert_called_once()

    @patch("main.requests.post")
    @patch("main.logger.exception")
    @patch("main.logger.debug")
    def test_main__failed_response(self, _, mock_logger_exception, mock_post):
        mock_response = MagicMock()
        mock_response.json.side_effect = Exception("Failed to decode JSON")
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        expected_response = {
            "body": {
                "description": "Something went wrong while making a request to OpenAI API"
            },
            "statusCode": 500
        }

        response = main(self.event, self.context)

        self.assertEqual(response, expected_response)
        mock_logger_exception.assert_called_once_with(mock_response.json.side_effect)
