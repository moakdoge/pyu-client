import sys

import requests
__URLS = [
    "http://127.0.0.1:5000",
    "http://192.168.0.24:5000",
    "http://moakdoge-laptop.local:5000"
]

url = None
def get_url():
    global url
    if url is not None:
        return url
    for link in __URLS:
        try:
            r = requests.get(link+"/package-list", timeout=0.05)
            if r.status_code == 404 or r.ok:
                url = link
                break
        except Exception as e:
            #print(f"error on link {link}: {e}")
            continue
    if url is None:
        raise FileNotFoundError(f"Failed to find valid url!")

    return url
