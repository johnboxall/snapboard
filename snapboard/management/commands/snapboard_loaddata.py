from optparse import make_option
from StringIO import StringIO
import os

from django.core.management.base import BaseCommand
from django.core.serializers.xml_serializer import Deserializer

# For any version <= 0.2.0 where this command existed, there is no backwards-incompatible schema change

# Note:
# The data converters take XML and output XML; this is highly inefficient
# When chaining converters to convert large datasets, this command will take 
# a long time to run
#
# It can be fixed later though

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
                    version = tuple((int(x) for x in node.getAttribute('version').split('.')))
                    if not self.check_version_compatibility(version):
                        raise PreprocessingRequired(version)
        raise StopIteration

    @staticmethod
    def check_version_compatibility(version):
        '''
        Returns whether the supplier version number is compatible with the 
        current one.
        '''
        for v in converters.keys():
            if v > version:
                return False
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
                objects = list(SNAPboardDeserializer(f))
            except PreprocessingRequired, e:
                converter_versions = [v for v in converters.iterkeys() if v > e.version]
                converter_versions.sort()
                f.seek(0)
                stream = StringIO(f.read())
                stream.seek(0)
                for v in converter_versions:
                    stream = converters[v](stream)
                objects = Deserializer(stream)
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

#from xml.dom import pulldom
#from StringIO import StringIO
#class BaseConverter(object):
#
#   def __init__(self, stream):
#       self.event_stream = pulldom.parse(stream)
#       self.out_stream = StringIO()
#
#   def convert(self):
#       '''
#       Returns a converted stream that contains the serialized data for this 
#       version.
#       '''
#       self._begin_stream()
#       for event, node in self.event_stream:
#           if event == "START_ELEMENT" and node.nodeName == "object":
#               self.event_stream.expandNode(node)
#               self._handle_object(node)
#       self._end_stream()
#       return self.out_stream
#
#   def _write_node(self, node):
#       self.out_stream
#   def _begin_stream(self):
#       raise NotImplementedError
#
#   def _end_stream(self):
#       raise NotImplementedError
#
#   def _handle_object(self, node):
#       raise NotImplementedError

def to_0_2_1(stream):
    '''
    Sets the is_private attribute of Post objects.
    '''
    try:
        from lxml import etree
        from lxml.builder import E
    except ImportError:
        print 'lxml could not be found. It is required for the conversion to work. Get lxml at http://codespeak.net/lxml/'
        import sys
        sys.exit(1)
    stream.seek(0)
    tree = etree.parse(stream)
    stream.truncate()
    root = tree.getroot()
    for elt in root.iterfind('.//field[@name="private"]'):
        if len(elt):
            # The element has children: set is_private=True on its parent
            elt.getparent().append(E.field('True', {'name': 'is_private', 'type': 'BooleanField'}))
    tree.write(stream)
    stream.seek(0)
    return stream

# Mapping of version triples to converters
converters = {
    (0, 2, 1): to_0_2_1
}

