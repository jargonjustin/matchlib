import codecs, encodings
from cStringIO import StringIO

from matchlib.compiler import compile_piped

class MatchPythonStreamReader(codecs.StreamReader):
    def __init__(self, *args, **kwargs):
        super(MatchPythonStreamReader, self).__init__(*args, **kwargs)
        self.__compiled = None
    
    def read(*args, **kwargs):
        return unicode(self.__compile__().read(*args, **kwargs))
    
    def readline(self, *args, **kwargs):
        return unicode(self.__compile__().readline(*args, **kwargs), 'utf8')
        
    def readlines(self, *args, **kwargs):
        return [
            unicode(line, 'utf8') for line in
            self.__compile__().readlines(*args, **kwargs) ]
    
    def __compile__(self):
        if self.__compiled is None:
            self.__compiled = StringIO()
            compile_piped(self.stream, self.__compiled)
            self.__compiled.reset()
        return self.__compiled

def search_function(encoding):
    if encoding != 'match-python':
        return None
    utf8 = encodings.search_function('utf8')
    return codecs.CodecInfo( name='match-python', 
        encode=utf8.encode, decode=utf8.decode,
        incrementalencoder=utf8.incrementalencoder,
        incrementaldecoder=utf8.incrementaldecoder,
        streamreader=MatchPythonStreamReader,
        streamwriter=utf8.streamwriter)

def register():
    codecs.register(search_function)
