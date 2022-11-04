import requests

def url_check(url):
    try:
        # Get Url
        get = requests.get(url)
        # if the request succeeds
        if get.status_code < 404:
            return True
        return False

    except requests.exceptions.RequestException as e:
        # print URL with Errs
        return False