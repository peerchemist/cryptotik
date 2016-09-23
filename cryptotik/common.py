
## common API classes and methods

class APIError(Exception):
    "Raise exception when the Poloniex API returned an error."
    pass
    
headers = {    # common HTTPS headers
    'Accept': 'application/json',
    'Accept-Charset': 'utf-8',
    'Accept-Encoding': 'identity',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive'
    }

