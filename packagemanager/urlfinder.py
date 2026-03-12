import threading
import requests

__URLS = [
    "http://127.0.0.1:5000",
    "http://192.168.0.24:5000",
    "http://moakdoge-laptop.local:5000"
]

url = None
_lock = threading.Lock()


def _check(link):
    global url

    if url is not None:
        return

    try:
        r = requests.get(link + "/package-list", timeout=0.5)
        with _lock:
            if url is None:
                url = link
    except Exception:
        pass


def get_url():
    global url

    if url is not None:
        return url

    threads = []

    for link in __URLS:
        t = threading.Thread(target=_check, args=(link,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    if url is None:
        raise FileNotFoundError("Failed to find valid url!")

    return url