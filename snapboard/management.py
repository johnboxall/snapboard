from django.dispatch import dispatcher 
from django.db.models import signals 

def sync_hook(): 
    # TODO
    pass

dispatcher.connect(sync_hook, signal=signals.post_syncdb) 
