import json
import time

from requests import RequestException

from lex.lex_app.helpers.RequestHandler import RequestHandler


class TestExecutor:
    def __init__(self, server_manager, max_retries=3, timeout=10, retry_delay=2):
        self.server_manager = server_manager
        self.request_handler = RequestHandler(
            max_retries=max_retries,
            timeout=timeout,
            retry_delay=retry_delay
        )

    async def execute_test(self, test_file_name, project_name):
        """Execute test in isolated process and return results"""
        server_obj = self.server_manager.restart_server()

        # Wait for server to be ready
        while not server_obj.is_alive() and not server_obj.is_migration_setup_error():
            time.sleep(0.1)

        if server_obj.is_migration_setup_error():
            return {
                'success': False,
                'error': json.loads(server_obj.shared_state['exit'])
            }

        # Allow server to fully initialize
        time.sleep(3)

        return await self._send_test_request(test_file_name, project_name)

    async def _send_test_request(self, test_file_name, project_name):
        """Send test execution request to server"""
        data = {
            'test_file_name': test_file_name,
            'project_name': project_name
        }

        try:
            response = self.request_handler.post_with_retry(
                "http://127.0.0.1:8001/ai/run-test/",
                data
            )

            if response is None:
                return {
                    'success': False,
                    'error': "Failed to get response after all retries"
                }

            response_json = response.json()
            error = "\n".join(response_json['console_output']['stderr'])
            print(error)

            return {
                'success': response_json.get("success"),
                'error': error
            }

        except RequestException as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }