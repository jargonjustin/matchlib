from matchlib.extractors import caseclass
import token

class PVar(caseclass('name')): pass
class PSym(caseclass('name')): pass

class PLit(caseclass('token')):
    def __repr__ (self):
        return 'PLit(%s, %s)' % (token.tok_name[self.token[0]], repr(self.token[1]))

class PTuple(caseclass('patterns')): pass
class PList(caseclass('patterns')): pass
class PDict(caseclass('pairings')): pass

class PExtractor(caseclass('extractor', 'patterns')): pass

class PBind(caseclass('name', 'pattern')): pass
class PSplat(caseclass('name')): pass
