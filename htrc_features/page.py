from __future__ import unicode_literals
from collections import defaultdict
from copy import copy
from htrc_features.token_list import TokenList
import htrc_features.utils as utils
from six import iteritems # Because python2's dict.iteritem is python3's dict.item

class Page:
    def __init__(self, pageobj, volume, default_section='body'):
        self.volume = volume
        self.line_count = pageobj
        self.default_section = default_section
        for (key, item) in iteritems(pageobj):
            setattr(self, key, pageobj[key])

        for sec in ['header', 'body', 'footer']:
            secjson = getattr(self, sec)
            setattr(self, sec, Section(name=sec, data=secjson, page=self))

    def __str__(self):
        return "<page %s of volume %s>" % (self.seq, self.volume.id)

    @property
    def tokenlist(self):
        ''' Returns tokenList for default_section '''
        assert(self.default_section in ['body', 'fullpage', 'header', 'footer'])
        sec = getattr(self, self.default_section)
        return sec.tokenlist

    def total_tokens(self):
        sec = getattr(self, self.default_section)
        return sec.total_tokens()

    @property
    def fullpage(self):
        ''' Merge header, body, and footer ''' 
        # Check if this has already been done
        if hasattr(self, '_fullpage'):
            return self._fullpage
        
        #newdata = {}
        #fullpage = Section(name='fullpage', data=newdata, page=self)
        fullpage = self._combine_sections([self.header, self.body, self.footer])
        fullpage.name = 'full'
        
        # Save merged section for easy recall
        self._fullpage = fullpage

        return fullpage

    def _combine_sections(self, secs):
        # Create a copy of the first section and add the others to it
        new_sec = copy(secs[0])
        for sec in secs[1:]:
            assert(isinstance(sec, Section))
            new_sec.add_Section(sec)
            new_sec.name =  "%s+%s" % (new_sec.name, sec.name)
        return new_sec

class Section:
    def __init__(self, name, data, page):
        self.name = name
        self.page = page
        self.tokenlist = TokenList(data['tokens'])
        
        for (key, value) in iteritems(data):
            if type(value) is int:
                setattr(self, key, value)
            elif key in ['endLineChars', 'beginLineChars']:
                # These field are saved as a defaultdict
                setattr(self, key, defaultdict(int, value))

    def add_Section(self, section):
        ''' Add another section to this one '''
        self.emptyLineCount += section.emptyLineCount
        self.tokenCount += section.tokenCount
        self.lineCount += section.lineCount
        self.sentenceCount += section.sentenceCount

        for key in ['endLineChars', 'beginLineChars']:
            new = defaultdict(int)
            for (char, count) in iteritems(getattr(section, key)):
                getattr(self, key)[char] += count

        self.tokenlist.add_TokenList(section.tokenlist)
    
    def total_tokens(self):
        return sum(self.tokenlist.token_counts(pos=False).values())

    def __str__(self):
        return "<%s section of page %s of volume %s>" % (self.name,
                self.page.seq, self.page.volume.id)

