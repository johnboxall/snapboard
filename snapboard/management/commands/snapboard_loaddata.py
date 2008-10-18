from optparse import make_option
import os

from django.core.management.base import BaseCommand
from django.core.serializers.xml_serializer import Deserializer

class PreprocessingRequired(Exception):
    '''
    Raised when the data is too old to be loaded directly as a regular
    Django fixture.
    '''
    
    def __init__(self, version):
        self.version = version

class SNAPboardDeserializer(Deserializer):

    def next(self):
        for event, node in self.event_stream:
            if event == "START_ELEMENT":
                if node.nodeName == "object":
                    self.event_stream.expandNode(node)
                    return self._handle_object(node)
                elif node.nodeName == "snapboardDataDump":
                    version = node.getAttribute('version')
                    if not self.check_version_compatibility(version):
                        raise PreprocessingRequired(version)
        raise StopIteration

    @staticmethod
    def check_version_compatibility(version):
        '''
        Returns whether the supplier version number is compatible with the 
        current one.
        '''
        return True

class Command(BaseCommand):
    '''
    Load data dumped by snapboard_dumpdata. Data dumped by earlier 
    releases of SNAPboard is automatically converted if required.
    '''

    option_list = BaseCommand.option_list + (
        make_option('--indent', default=None, dest='indent', type='int',
            help='Specifies the indent level to use when pretty-printing output'),
    )

    help = 'Load data dumped by snapboard_dumpdata. Data dumped by earlier '\
           'releases of SNAPboard is automatically converted if required.'

    args = ['<filename>']

    def handle(self, *args, **kwargs):
        from django.db import transaction
        try:
            f = open(args[0], 'r')
        except OSError, e:
            os.strerror(e.errno)
            return

        # Start transaction management. All fixtures are installed in a
        # single transaction to ensure that all references are resolved.
        transaction.commit_unless_managed()
        transaction.enter_transaction_management()
        transaction.managed(True)

        try:
            try:
                objects = SNAPboardDeserializer(f)
            except PreprocessingRequired, e:
                # This is where future versions must convert data from old
                # releases to the new format.
                raise NotImplementedError
                # stream = SNAPboardConverter(f)
                # f.close()
                # objects = Deserializer(stream)
        except Exception:
            transaction.rollback()
            transaction.leave_transaction_management()
            raise
        try:
            count = 0
            for obj in objects:
                obj.save()
                count += 1
        except Exception:
            transaction.rollback()
            transaction.leave_transaction_management()
            raise
        else:
            transaction.commit()
            transaction.leave_transaction_management()
            print "Successfully loaded %i objects." % count

