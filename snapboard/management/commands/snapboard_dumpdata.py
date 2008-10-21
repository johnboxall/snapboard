from optparse import make_option
import sys

from django.core.management.base import BaseCommand
from django.core.serializers import get_serializer
from django.contrib.auth.models import User

from snapboard import models

def _get_snapboard_objects():
    for model in [models.Category, models.Moderator, models.Thread, models.Post,
            models.AbuseReport,    models.WatchList, models.UserSettings, 
            models.UserBan, models.IPBan, models.Group, models.Invitation,
            User]:
        qs = model.objects.all()
        for obj in qs:
            yield obj

class Command(BaseCommand):
    '''
    Dump all the SNAPboard data in the database to stdout. All of Django's 
    authentication framework's User instances are also included.

    The format is a subset of XML that simply wraps a Django fixture, storing 
    the current SNAPboard version identifier.

    This is useful between releases where SNAPboard's model definitions 
    evolve in some way that affects the database schema. Each such release 
    should also enhance this command's counterpart to convert any old fixture 
    to match the new model definitions and then load the data through Django's 
    fixture support.
    '''

    option_list = BaseCommand.option_list + (
        make_option('--indent', default=None, dest='indent', type='int',
            help='Specifies the indent level to use when pretty-printing output'),
    )

    help = 'Dump all the SNAPboard data in the database to stdout. All of '\
            'Django\'s authentication framework\'s User instances are also '\
            'included.'

    def handle(self, *args, **kwargs):
        s = get_serializer('xml')()
        s.serialize(_get_snapboard_objects(), **kwargs)
        s.stream.seek(0)
        sys.stdout.write(s.stream.read(len('<?xml version="1.0" encoding="utf-8"?>\n')))
        sys.stdout.write('''<snapboardDataDump version="0.1.0">''')
        for chunk in iter(s.stream):
            sys.stdout.write(chunk)
        sys.stdout.write('</snapboardDataDump>')

# vim: ai ts=4 sts=4 et sw=4
