from .get import get_request


def http_github():
    url = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/refs/heads/master/http.txt"
    protocol = "http"
    # every like a new http proxy with the format: ip:port
    response = get_request(url, None)
    if response.status == 200:
        data = response.text()
        return data.split("\n")
