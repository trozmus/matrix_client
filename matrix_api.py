import httpx


class MatrixAPI:
    def __init__(self, base_url, access_token=None):
        """Initialize with the base URL and optional access token."""
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.client = httpx.AsyncClient(verify=False)

    def set_access_token(self, token):
        """Set or update the access token."""
        self.access_token = token

    async def _request(self, method, endpoint, data=None, params=None):
        """Generic method for making async HTTP requests."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"} if self.access_token else {}

        try:
            response = await self.client.request(method, url, json=data, params=params, headers=headers)
            response.raise_for_status()  # Raise an error for HTTP 4xx/5xx responses
            # return response.json()
            return response

        except httpx.RequestError as e:
            print(f"Request Error: {e}")
            # return e.response.status_code
            return e.response
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            return e.response

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
