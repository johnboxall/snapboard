"""This is Textile
A Humane Web Text Generator

USING TEXTILE

Block modifier syntax:

Header: hn. 
Paragraphs beginning with 'hn. ' (where n is 1-6) are wrapped in header tags.
Example: <h1>Text</h1>

Header with CSS class: hn(class).
Paragraphs beginning with 'hn(class). ' receive a CSS class attribute. 
Example: <h1 class="class">Text</h1>

Paragraph: p. (applied by default)
Paragraphs beginning with 'p. ' are wrapped in paragraph tags.
Example: <p>Text</p>

Paragraph with CSS class: p(class).
Paragraphs beginning with 'p(class). ' receive a CSS class attribute. 
Example: <p class="class">Text</p>

Blockquote: bq.
Paragraphs beginning with 'bq. ' are wrapped in block quote tags.
Example: <blockquote>Text</blockquote>

Blockquote with citation: bq(citeurl).
Paragraphs beginning with 'bq(citeurl). ' receive a citation attribute. 
Example: <blockquote cite="citeurl">Text</blockquote>

Numeric list: #
Consecutive paragraphs beginning with # are wrapped in ordered list tags.
Example: <ol><li>ordered list</li></ol>

Bulleted list: *
Consecutive paragraphs beginning with * are wrapped in unordered list tags.
Example: <ul><li>unordered list</li></ul>


Phrase modifier syntax:

_emphasis_             <em>emphasis</em>
__italic__             <i>italic</i>
*strong*               <strong>strong</strong>
**bold**               <b>bold</b>
??citation??           <cite>citation</cite>
-deleted text-         <del>deleted</del>
+inserted text+        <ins>inserted</ins>
^superscript^          <sup>superscript</sup>
~subscript~            <sub>subscript</sub>
@code@                 <code>computer code</code>

==notextile==          leave text alone (do not format)

"linktext":url         <a href="url">linktext</a>
"linktext(title)":url  <a href="url" title="title">linktext</a>

!imageurl!             <img src="imageurl">
!imageurl(alt text)!   <img src="imageurl" alt="alt text" />
!imageurl!:linkurl     <a href="linkurl"><img src="imageurl" /></a>

ABC(Always Be Closing) <acronym title="Always Be Closing">ABC</acronym>
"""

__author__ = "Mark Pilgrim (f8dy@diveintomark.org)"
__version__ = "1.1"
__date__ = "2003/06/06"
__copyright__ = """
Copyright (c) 2003, Mark Pilgrim, http://diveintomark.org/
All rights reserved.

Original PHP version:
Version 1.0
21 Feb, 2003

Copyright (c) 2003, Dean Allen, www.textism.com
All rights reserved.
"""
__license__ = """
Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, 
  this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name Textile nor the names of its contributors may be used to
  endorse or promote products derived from this software without specific
  prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE 
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""
__history__ = """
1.0  - 2003/03/19 - MAP - initial release
1.01 - 2003/03/19 - MAP - don't strip whitespace within <pre> tags;
  map high-bit ASCII to HTML numeric entities
1.02 - 2003/03/19 - MAP - changed hyperlink qtag expression to only
  match valid URL characters (per RFC 2396); fixed preg_replace to
  not match across line breaks (solves lots of problems with
  mistakenly matching overlapping inline markup); fixed whitespace
  stripping to only strip whitespace from beginning and end of lines,
  not immediately before and after HTML tags.
1.03 - 2003/03/20 - MAP - changed hyperlink qtag again to more
  closely match original Textile (fixes problems with links
  immediately followed by punctuation -- somewhere Dean is
  grinning right now); handle curly apostrophe with "ve"
  contraction; clean up empty titles at end.
1.04 - 2003/03/23 - MAP - lstrip input to deal with extra spaces at
  beginning of first line; tweaked list loop to handle consecutive lists
1.1 - 2003/06/06 - MAP - created initial test suite for links and images,
  and fixed a bunch of related bugs to pass them

Modified 2007/01/30 by Bo Shi
- added "rel='nofollow'" attribute to all hyperlinks, since this library will
  only be used in snapboard posts
"""
import re

DEBUGLEVEL = 0
def _debug(s, level=1):
    if DEBUGLEVEL >= level:
        print s
        
# map 8-bit ASCII codes to HTML numerical entity equivalents
_demoroniserMap = [(128, 8364), (129, 0), (130, 8218), (131, 402), (132, 8222), (133, 8230), (134, 8224), (135, 8225), (136, 710), (137, 8240), (138, 352), (139, 8249), (140, 338), (141, 0), (142, 0), (143, 0), (144, 0), (145, 8216), (146, 8217), (147, 8220), (148, 8221), (149, 8226), (150, 8211), (151, 8212), (152, 732), (153, 8482), (154, 353), (155, 8250), (156, 339), (157, 0), (158, 0), (159, 376)]
_demoroniserMap = [(chr(a), b and ('&#%s;' % b) or '') for (a, b) in _demoroniserMap]
def demoroniser(text):
    for a, b in _demoroniserMap:
        text = text.replace(a, b)
    return text

def preg_replace(pattern, replacement, text):
    # this acts like re.sub, except it replaces empty groups with ''
    #  instead of raising an exception
    def replacement_func(matchobj):
        counter = 1
        rc = replacement
        _debug(matchobj.groups())
        for matchitem in matchobj.groups():
            if not matchitem:
                matchitem = ''
            rc = rc.replace(r'\%s' % counter, matchitem)
            counter += 1
        return rc
    p = re.compile(pattern)
    _debug(pattern)
    return p.sub(replacement_func, text) 

ENT_COMPAT = 0
ENT_NOQUOTES = 1
ENT_QUOTES = 2
def htmlspecialchars(text, mode):
    text = text.replace('&', '&amp;')
    if mode != ENT_NOQUOTES:
        text = text.replace('"', '&quot;')
    if mode == ENT_QUOTES:
        text = text.replace("'", '&#039;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

def textile(text):

### Basic global changes

    text = text.lstrip()
    
    # turn any incoming ampersands into a dummy character for now.
    #  This uses a negative lookahead for alphanumerics followed by a semicolon,
    #  implying an incoming html entity, to be skipped 
    text = preg_replace(r"&(?![#a-zA-Z0-9]+;)", r"x%x%", text);

    # entify illegal high-bit ASCII
    text = demoroniser(text)
    
    # unentify angle brackets and ampersands
    text = text.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
	
    # zap carriage returns
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # if there is no html, trim each line unequivocally
    if not re.search(r'''<.*>''', text):
        # trim each line
        text = "\n".join([l.strip() for l in text.split("\n")])
    else:
        # else split the text into an array at <> and only trim lines
        #  that are not within a <pre> tag
        lines = []
        pre = 0
        for line in re.split('(<.*?>)', text):
            if re.match('<pre>', line.lower()):
                pre = 1
            elif re.match('</pre>', line.lower()):
                pre = 0
            if not pre:
                line = preg_replace('''(\\s*?)\n(\\s*?)''', '\n', line)
            lines.append(line)
        text = ''.join(lines)

### Find and replace quick tags

    # double equal signs mean <notextile>
    text = preg_replace(r"""(^|\s)==(.*?)==([^\w]{0,2})""", r"""\1<notextile>\2</notextile>\3""", text);

    # image qtag
    text = preg_replace(r"""!([^\s\(=!]+?)\s?(\(([^\)]+?)\))?!""", r"""<img src="\1" alt="\3" />""", text);

    # image with hyperlink
    hyperlink = r"""(\S+?)([^\w\s\/;=\?]*?)(\s|$)"""
    text = preg_replace(r"""(<img.+ \/>):""" + hyperlink, r"""<a rel='nofollow' href="\2">\1</a>\3\4""", text);

    # hyperlink qtag
    text = preg_replace(r'''"([^"\(]+)\s?(\(([^\)]+)\))?":''' + hyperlink, r'''<a rel='nofollow' href="\4" title="\3">\1</a>\5\6''', text)
    
    # arrange qtag delineators and replacements in an array
    qtags = [(r'\*\*', 'b'),
             (r'\*', 'strong'),
             (r'\?\?', 'cite'),
             (r'-', 'del'),
             (r'\+', 'ins'),
             (r'~', 'sub'),
             (r'@', 'code')]

    # loop through the array, replacing qtags with html
    for texttag, htmltag in qtags:
        text = preg_replace(r'''(^|\s|>)''' + texttag + r'''\b(.+?)\b([^\w\s]*?)''' + texttag + r'''([^\w\s]{0,2})''',
                            r'''\1<''' + htmltag + r'''>\2\3</''' + htmltag + r'''>\4''',
                            text);

    # some weird bs with underscores and \b word boundaries, 
    #  so we'll do those on their own
    text = preg_replace(r'''(^|\s)__(.*?)__([^\w\s]{0,2})''', r'''\1<i>\2</i>\3''', text)
    text = preg_replace(r'''(^|\s)_(.*?)_([^\w\s]{0,2})''', r'''\1<em>\2</em>\3''', text)
    text = preg_replace(r'''\^(.*?)\^''', r'''<sup>\1</sup>''', text)

### Find and replace typographic chars and special tags

    # small problem with double quotes at the end of a string, so add a dummy space
    text = preg_replace(r'''"$''', r'''" ''', text);

    # NB: all these will wreak havoc inside <html> tags

    glyphs = [(r'''([^\s[{(>])?\'([dmst]\b|ll\b|ve\b|\s|:|$)''', r'''\1&#8217;\2'''), # single closing
              (r'''\'''', r'''&#8216;'''), # single opening
	      (r'''([^\s[{(])?"(\s|:|$)''', r'''\1&#8221;\2'''), # double closing
              (r'''"''', r'''&#8220;'''), # double opening
	      (r'''\b( )?\.{3}''', r'''\1&#8230;'''), # ellipsis
              (r'''\b([A-Z][A-Z0-9]{2,})\b(\(([^\)]+)\))''', r'''<acronym title="\3">\1</acronym>'''), # 3+ uppercase acronym
              (r'''(^|[^"][>\s])([A-Z][A-Z0-9 ]{2,})([^<a-z0-9]|$)''', r'''\1<span class="caps">\2</span>\3'''), # 3+ uppercase caps
              (r'''\s?--\s?''', r'''&#8212;'''), # em dash
              (r'''\s-\s''', r''' &#8211; '''), # en dash
              (r'''(\d+) ?x ?(\d+)''', r'''\1&#215;\2'''), # dimension sign
              (r'''\b ?(\((tm|TM)\))''', r'''&#8482;'''), # trademark
              (r'''\b ?(\([rR]\))''', r'''&#174;'''), # registered
              (r'''\b ?(\([cC]\))''', r'''&#169;'''), # registered
               ]

    # set toggle for turning off replacements between <code> or <pre>
    codepre = 0

    # if there is no html, do a simple search and replace
    if not re.search(r'''<.*>''', text):
        for glyph_search, glyph_replace in glyphs:
            _debug(text)
            _debug("applying %s" % glyph_search)
            text = preg_replace(glyph_search, glyph_replace, text)
        _debug(text)
    else:
        lines = []
        # else split the text into an array at <>
        for line in re.split('(<.*?>)', text):
            if re.match('<(code|pre|kbd|notextile)>', line.lower()):
                codepre = 1
            elif re.match('</(code|pre|kbd|notextile)>', line.lower()):
                codepre = 0
            if (not re.match('<.*?>', line)) and (not codepre):
                for glyph_search, glyph_replace in glyphs:
                    line = preg_replace(glyph_search, glyph_replace, line)
            if codepre:
                # escape <>& if between <code>
                line = htmlspecialchars(line, ENT_NOQUOTES)
                line = line.replace('&lt;pre&gt;', '<pre>')
                line = line.replace('&lt;code&gt;', '<code>')
            lines.append(line)
        text = ''.join(lines)

### Block level formatting

    # deal with forced breaks; this is going to be a problem between
    #  <pre> tags, but we'll clean them later
    text = preg_replace('''(\\S)(_*?)([^\\w\\s]*?) *?\n([^#*\\s])''', r'''\1\2\3<br />\4''', text)

    # might be a problem with lists
    text = text.replace(r'''l><br />''', '''l>\n''')

    blocks = [(r'''^\s?\*\s(.*)''', '''\t<liu>\\1</liu>'''), # bulleted list *
              (r'''^\s?#\s(.*)''', '''\t<lio>\\1</lio>'''), # numeric list #
              (r'''^bq\. (.*)''', '''\t<blockquote>\\1</blockquote>'''), # blockquote bq.
              (r'''^h(\d)\(([\w]+)\)\.\s(.*)''', '''\t<h\\1 class=\"\\2\">\\3</h\\1>'''), # header hn(class).  w/ css class
              (r'''^h(\d)\. (.*)''', '''\t<h\\1>\\2</h\\1>'''), # plain header hn.
              (r'''^p\(([\w]+)\)\.\s(.*)''', '''\t<p class="\\1">\\2</p>'''), # para p(class).  w/ css class
              (r'''^p\. (.*)''', '''\t<p>\\1</p>'''), # plain paragraph
              ('''^([^\t ]+.*)''', '''\t<p>\\1</p>''') # remaining plain paragraph
              ]

    list = ''
    pre = 0
    rc = []
    for line in text.split('\n') + [' ']:
        # make sure line isn't blank
        if line:
            # matches are off if we're between <pre> or <code> tags
            if re.search('<pre>', line.lower()):
                pre = 1

            # deal with block replacements first, then see if we're in a list
            if not pre:
                for block_find, block_replace in blocks:
                    line = preg_replace(block_find, block_replace, line)

            # kill any br tags that slipped in earlier
            if pre:
                line = line.replace(r'''<br />''', '''\n''')

            # matches back on after </pre> 
            if re.search('</pre>', line.lower()):
                pre = 0
            
        # at the beginning of a list, $line switches to a value
        if (not list) and re.match('\t<li', line):
            line = preg_replace('''^(\t<li)(o|u)''', '''\n<\\2l>\n\\1\\2''', line)
            list = line[2] # "u" or "o", presumably
        elif list and (not re.match('''\t<li''' + list, line)):
            # at the end of a list, $line switches to empty
            line = preg_replace('''^(.*)$''', '''</''' + list + '''l>\n\\1''', line)
            list = ''

        rc.append(line)
    text = '\n'.join(rc)

    #clean up <notextile>
    text = preg_replace(r'''<\/?notextile>''', "", text)
	
    # clean up liu and lio
    text = preg_replace(r'''<(\/?)li(u|o)>''', r'''<\1li>''', text)

    # clean up empty titles
    text = text.replace(' title=""', '')

    # turn the temp char back to an ampersand entity
    text = text.replace("x%x%", "&#38;")
	
    # Newline linebreaks, just for markup tidiness
    text = text.replace('''<br />''', '''<br />\n''')

    return text

if __name__ == '__main__':
    import sys
    print textile(sys.stdin.read())
# vim: ai ts=4 sts=4 et sw=4
