# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 expandtab:
#{{{Preformatter and entryparser for the pyblogsom
'''
Preformatter and entryparser for the pyblogsom
This plugin is heavily based work done by Wari Wahab <wari at wari dot per dot sg>

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the 'Software'), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the
Software, and to permit persons to whom the Software is furnished
to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Copyright 2010, Glennie Vignarajah
'''
#}}}

__author__ = 'Glennie Vignarajah <glennie@glennie.fr>'
__version__ = 'moinmoin.py 0.192-2010-11-26 01:50:50Z Glennie $'
__description__ = 'This plugin allows to write entries using moinmoin wiki formating'

try:
    from MoinMoin.web.contexts import ScriptContext as MoinMoinScriptContext
    from MoinMoin.Page import Page as MoinMoinPage
    from MoinMoin import wikiutil as MoinMoinWikiutil
    from wikiconfig import Config as MoinConfigForPybloxsom
    import_moinmoin_done = True
except:
    import_moinmoin_done = False

from Pyblosxom import tools as PyblosxomTools


import sys, os
import hashlib

PREFORMATTER_ID = 'moinmoin'
MOINMOIN_VERSION = '193'


class MoinMoinEntryParser:
#{{{MoinMoinEntryParser class object
    '''
    This class contains evrything in order to parse a file using MoinMoin
    dervied Objects
    '''

    def __init__(self, url = '', pybloxsom_config = None):
#{{{Init method for the MoinMoinEntryParser class
        '''
        init method for MoinMoinEntryParser Object
        '''
        self.PREFORMATTER_ID = PREFORMATTER_ID

        # New MoinMoin request
        self.request = MoinMoinScriptContext(url)
        self.logger = PyblosxomTools.get_logger()
        self.url = url
        self.entryfile=''
        self.entrytitle = ''
        self.page_name = ''

        # Initial parser configuration if config is usable
        if pybloxsom_config is not None:
            self.pybloxsom_config = pybloxsom_config
            # Use moinmoin cache
            self.request.cacheable = self.request.use_cache = self.pybloxsom_config.get('moinmoin_use_cache', '0') == '1'
            #self.request.cacheable = self.request.use_cache = False

            # moinmoin encoding 
            self.output_charset = self.pybloxsom_config.get('blog_encoding', 'utf-8')
        # We don't have the config, using default
        else:
            self.request.cacheable = False
            self.output_charset = 'utf-8'
#}}}
        self.logger.debug('Moinmoin parser Object created')

    def create_page(self, entryfile = '', load_from_disk = True):
#{{{Here we create a moinmoin page object
        '''Creates a new MoinMoin Page Object.'''

        '''
        If load_from_disk is true, then the file is loaded from the disk using the entryfile as the filename.
        If not, we use the entryfile string as the raw file body
        '''
        # New MoinMoinPage
        if load_from_disk:
            page_dir, self.page_name = os.path.split(entryfile)
        else:
            self.page_name = str(hashlib.md5(entryfile).hexdigest())
        
        self.page = MoinMoinPage(self.request, page_name=self.page_name, formatter=None)

        # Load New page from file
        if load_from_disk:
            self.page.__body = None
            self.page._text_filename_force = entryfile
            self.logger.debug('Entry file to convert: %s' % entryfile)
        # Extracting page title
            tmp_body = self.page.get_body()
            self.entrytitle = tmp_body.split('\n')[0]
            self.page.set_raw_body(tmp_body[len(self.entrytitle)+1:])
            del tmp_body
        else:
            self.page.set_raw_body(entryfile)
            self.logger.debug('Using data got from pyblosxom')

        self.page.hilite_re = None
        self.page.output_charset = self.output_charset
        self.parser = None
        self.formatter = None
        self.default_parser = 'wiki'
        self.output_format = u'text/html'
        self.request.page = self.page
        self.page.__pi = self.page.parse_processing_instructions()
        self.logger.debug('New moinmoin page created')
#}}}

    def create_parser(self, line_anchors = False):
#{{{Here we create a moinmoin paser object
        '''Creating parser object'''
        
        Parser = MoinMoinWikiutil.searchAndImportPlugin(self.request.cfg, 'parser', self.request.getPragma('format', self.default_parser.lower()))
        self.parser = Parser(self.page.get_body(), self.request, line_anchors = line_anchors)
        self.logger.debug('New moinmoin parser created')
#}}}

    def create_formatter(self):
#{{{Here we create a moinmoin formatter object
        '''Creating formatter object'''

        Formatter = MoinMoinWikiutil.searchAndImportPlugin(self.request.cfg, 'formatter', self.request.getPragma('output-format', self.output_format).lower())

        self.formatter = Formatter(self.request)
        self.formatter.setPage(self.page)
        self.request.formatter = self.page.formatter = self.formatter
        self.logger.debug('New moinmoin formatter created')
#}}}

    def parse_entry(self, content_only = 1):
#{{{parsing the entry file return the result
        '''parse the entryfile and return the result string'''
        return self.request.redirectedOutput(self.page.send_page,content_id=self.page_name, content_only = content_only, do_cache=self.request.cacheable)
#}}}

#}}}

def cb_preformat(args):
#{{{Hooking to pybloxsom callback entry parser
    '''
    preformat chain callback.
    postformat callbacks are also called.

    @param args: dict 
    @type args: dict
    @rtype: string
    '''
    if args['parser'] == PREFORMATTER_ID:
        if args.has_key('filename'):
            return parse_moimoin(args['filename'], args['request'], load_from_disk = True)
        else: 
            return parse_moimoin(''.join(args['story']), args['request'], load_from_disk = False)
    else:
        return ''.join(args['story'])
#}}}

def parse_moimoin(entry, bloxsom_request = None, load_from_disk = False, from_entryparser = False):
#{{{callback function for preformat hook
    '''
    Inialize the a moinmoin class object in order to parse the string or the file.

    @param entry: moinmoin formatted string or a filename
    @type entry: string
    @param bloxsom_request: The pybloxsom request object
    @type request: L{Pyblosxom.pyblosxom.Request} object
    @param load_from_disk: indicates if we need to load the file from disk
    @type load_from_disk: boolean
    @returns: Data of the entry
    @rtype: string
    '''
    moinmoin = MoinMoinEntryParser(pybloxsom_config = bloxsom_request.get_configuration())
    moinmoin.create_page(entryfile = entry, load_from_disk = load_from_disk)
    moinmoin.create_formatter()
    moinmoin.create_parser()
    return moinmoin.parse_entry()
#}}}

def verify_installation(request):
#{{{check installation process
    verify_return_code = 1
    pybloxsom_config = request.get_configuration()

    try:
        from MoinMoin import version as MoinMoinVersion
        print 'MoinMoin Version: %s' % (MoinMoinVersion.release)
        if MoinMoinVersion.release_short != MOINMOIN_VERSION:
            print 'Warning: this parser is was tested only with 1.9+ of Moinmoin.'
    except:
        verify_return_code = 0

    if (verify_return_code == 0) or (import_moinmoin_done == False):
        print 'Check if MoinMoin is correctly installed'
        return 0

    # Use moinmoin cache?
    encoding = pybloxsom_config.get('blog_encoding', 'utf-8')
    if pybloxsom_config.get('use_moinmoin_cache', '0') == '1':
        cache_text = 'Using moinmoin cache.'
    else:
        cache_text = 'Not using moinmoin cache. Use py[\'use_moinmoin_cache\']=\'1\' to change it.'

    print 'Encodig: %s. Use py[\'blog_encoding\'] to change it.' % encoding
    print '%s' % cache_text

    return 1
#}}}
