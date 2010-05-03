from piston.handler import BaseHandler
from piston.utils import rc, require_mime, require_extended

from snapboard.models import Thread
from snapboard.api.forms import ThreadForm


class ThreadHandler(BaseHandler):
    allowed_methods = ('POST',)
    model = Thread
    
    # validates?    
    def create(self, request):
        """
        Create a new post in a thread.
        
        """
        form = ThreadForm(request.POST or None, request=request)
        if form.is_valid():
            form.save()
            return rc.CREATED
        
        # NEED SOME SPECIAL FIELDS.
        
        #        print form.errorskeys()            
        print form.errors
            
        return rc.BAD_REQUEST