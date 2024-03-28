from requests.exceptions import RequestException, InvalidJSONError, HTTPError

class PTWrapperLibraryException(RequestException):
    pass

class PTWrapperLibraryJSONResponse(InvalidJSONError):
    pass

class PTWrapperLibraryFailed(HTTPError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
