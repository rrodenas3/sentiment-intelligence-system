import urllib.request
import urllib.parse
import time

url = 'http://127.0.0.1:8000/auth/login'
# OAuth2PasswordRequestForm needs x-www-form-urlencoded
data = urllib.parse.urlencode({'username': 'test@example.com', 'password': 'password123'}).encode()
headers = {'Content-Type': 'application/x-www-form-urlencoded'}

print("Testing rate limit on /auth/login (Limit: 5/minute)")
for i in range(1, 7):
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        response = urllib.request.urlopen(req, timeout=5)
        print(f"Request {i}: Success HTTP {response.getcode()}")
    except urllib.error.HTTPError as e:
        print(f"Request {i}: Blocked HTTP {e.code} - {e.reason}")
    except Exception as e:
        print(f"Request {i}: Error - {e}")
    time.sleep(0.1)
