from django.utils import simplejson
from django.forms.util import ErrorDict, ErrorList



class ErrorJSONEncoder(simplejson.JSONEncoder):
    def default(self, o):
        if issubclass(o.__class__, ErrorDict):
            return dict(o)
        if issubclass(o.__class__, ErrorList):
            return list(o)
        else:
            return super(ErrorJSONEncoder, self).default(o)

def dumps(o):
    return simplejson.dumps(o, cls=ErrorJSONEncoder, default=str)