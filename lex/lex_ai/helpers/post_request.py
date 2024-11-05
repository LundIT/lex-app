import requests
from django.http import JsonResponse

def post_request(url, data):
    """Sends a POST request to the specified URL with the given data."""
    try:
        # Sending a POST request with JSON data
        response = requests.post(url, json=data)

        return response
    except requests.exceptions.RequestException as e:
        # Handle connection errors
        return JsonResponse({'error': str(e)}, status=500)