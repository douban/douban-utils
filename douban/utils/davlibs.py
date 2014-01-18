# pylint: disable=W0311,W0201,W0402,W0102,W0701,W0613,W0141,
# pylint: disable=W0612,W0231,R0912,R0903,C0321,R0904,E0611,E1101,E1103
#
# DAV client library
#
# Copyright (C) 1998-2000 Guido van Rossum. All Rights Reserved.
# Written by Greg Stein. Given to Guido. Licensed using the Python license.
#
# This module is maintained by Greg and is available at:
#    http://www.lyra.org/greg/python/davlib.py
#
# Since this isn't in the Python distribution yet, we'll use the CVS ID
# for tracking:
#   $Id: davlib.py,v 1.8 2001/03/28 03:28:25 gstein Exp $
#

#
# qp_xml: Quick Parsing for XML
#
# Written by Greg Stein. Public Domain.
# No Copyright, no Rights Reserved, and no Warranties.
#
# This module is maintained by Greg and is available as part of the XML-SIG
# distribution. This module and its changelog can be fetched at:
#    http://www.lyra.org/cgi-bin/viewcvs.cgi/xml/xml/utils/qp_xml.py
#
# Additional information can be found on Greg's Python page at:
#    http://www.lyra.org/greg/python/
#
# This module was added to the XML-SIG distribution on February 14, 2000.
# As part of that distribution, it falls under the XML distribution license.
#

import string
try:
    import qp_xml
except:
    pass

try:
    import pyexpat
except ImportError:
    from xml.parsers import pyexpat

error = __name__ + '.error'


#
# The parsing class. Instantiate and pass a string/file to .parse()
#
class Parser:

    def __init__(self):
        self.reset()

    def reset(self):
        self.root = None
        self.cur_elem = None

    def find_prefix(self, prefix):
        elem = self.cur_elem
        while elem:
            if elem.ns_scope.has_key(prefix):
                return elem.ns_scope[prefix]
            elem = elem.parent

        if prefix == '':
            return ''		# empty URL for "no namespace"

        return None

    def process_prefix(self, name, use_default):
        idx = string.find(name, ':')
        if idx == -1:
            if use_default:
                return self.find_prefix(''), name
            return '', name  # no namespace

        if string.lower(name[:3]) == 'xml':
            return '', name	# name is reserved by XML. don't break out a NS.

        ns = self.find_prefix(name[:idx])
        if ns is None:
            raise error, 'namespace prefix not found'

        return ns, name[idx+1:]

    def start(self, name, attrs):
        elem = _element(name=name, lang=None, parent=None,
                        children=[], ns_scope={}, attrs={},
                        first_cdata='', following_cdata='')

        if self.cur_elem:
            elem.parent = self.cur_elem
            elem.parent.children.append(elem)
            self.cur_elem = elem
        else:
            self.cur_elem = self.root = elem

        work_attrs = []

        # scan for namespace declarations (and xml:lang while we're at it)
        for name, value in attrs.items():
            if name == 'xmlns':
                elem.ns_scope[''] = value
            elif name[:6] == 'xmlns:':
                elem.ns_scope[name[6:]] = value
            elif name == 'xml:lang':
                elem.lang = value
            else:
                work_attrs.append((name, value))

        # inherit xml:lang from parent
        if elem.lang is None and elem.parent:
            elem.lang = elem.parent.lang

        # process prefix of the element name
        elem.ns, elem.name = self.process_prefix(elem.name, 1)

        # process attributes' namespace prefixes
        for name, value in work_attrs:
            elem.attrs[self.process_prefix(name, 0)] = value

    def end(self, name):
        parent = self.cur_elem.parent

        del self.cur_elem.ns_scope
        del self.cur_elem.parent

        self.cur_elem = parent

    def cdata(self, data):
        elem = self.cur_elem
        if elem.children:
            last = elem.children[-1]
            last.following_cdata = last.following_cdata + data
        else:
            elem.first_cdata = elem.first_cdata + data

    def parse(self, input):
        self.reset()

        p = pyexpat.ParserCreate()
        p.StartElementHandler = self.start
        p.EndElementHandler = self.end
        p.CharacterDataHandler = self.cdata

        try:
            if type(input) == type(''):
                p.Parse(input, 1)
            else:
                while 1:
                    s = input.read(_BLOCKSIZE)
                    if not s:
                        p.Parse('', 1)
                        break

            p.Parse(s, 0)

        finally:
            if self.root:
                _clean_tree(self.root)

        return self.root


#
# handy function for dumping a tree that is returned by Parser
#
def dump(f, root):
    f.write('<?xml version="1.0"?>\n')
    namespaces = _collect_ns(root)
    _dump_recurse(f, root, namespaces, dump_ns=1)
    f.write('\n')


#
# This function returns the element's CDATA. Note: this is not recursive --
# it only returns the CDATA immediately within the element, excluding the
# CDATA in child elements.
#
def textof(elem):
    return elem.textof()


#########################################################################
#
# private stuff for qp_xml
#

_BLOCKSIZE = 16384	# chunk size for parsing input


class _element:

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def textof(self):
        '''Return the CDATA of this element.

        Note: this is not recursive -- it only returns the CDATA immediately
        within the element, excluding the CDATA in child elements.
        '''
        s = self.first_cdata
        for child in self.children:
            s = s + child.following_cdata
        return s

    def find(self, name, ns=''):
        for elem in self.children:
            if elem.name == name and elem.ns == ns:
                return elem
        return None


def _clean_tree(elem):
    elem.parent = None
    del elem.parent
    map(_clean_tree, elem.children)


def _collect_recurse(elem, dict):
    dict[elem.ns] = None
    for ns, name in elem.attrs.keys():
        dict[ns] = None
    for child in elem.children:
        _collect_recurse(child, dict)


def _collect_ns(elem):
    "Collect all namespaces into a NAMESPACE -> PREFIX mapping."
    d = { '' : None }
    _collect_recurse(elem, d)
    del d['']	# make sure we don't pick up no-namespace entries
    keys = d.keys()
    for i in range(len(keys)):
        d[keys[i]] = i
    return d


def _dump_recurse(f, elem, namespaces, lang=None, dump_ns=0):
    if elem.ns:
        f.write('<ns%d:%s' % (namespaces[elem.ns], elem.name))
    else:
        f.write('<' + elem.name)
    for (ns, name), value in elem.attrs.items():
        if ns:
            f.write(' ns%d:%s="%s"' % (namespaces[ns], name, value))
        else:
            f.write(' %s="%s"' % (name, value))
    if dump_ns:
        for ns, id in namespaces.items():
            f.write(' xmlns:ns%d="%s"' % (id, ns))
    if elem.lang != lang:
        f.write(' xml:lang="%s"' % elem.lang)
    if elem.children or elem.first_cdata:
        f.write('>' + elem.first_cdata)
        for child in elem.children:
            _dump_recurse(f, child, namespaces, elem.lang)
            f.write(child.following_cdata)
        if elem.ns:
            f.write('</ns%d:%s>' % (namespaces[elem.ns], elem.name))
        else:
            f.write('</%s>' % elem.name)
    else:
        f.write('/>')

# end of qp_xml

import httplib
import urllib
import types
import mimetypes


INFINITY = 'infinity'
XML_DOC_HEADER = '<?xml version="1.0" encoding="utf-8"?>'
XML_CONTENT_TYPE = 'text/xml; charset="utf-8"'

# block size for copying files up to the server
BLOCKSIZE = 16384


class HTTPConnectionAuth(httplib.HTTPConnection):

    def __init__(self, *args, **kw):
        apply(httplib.HTTPConnection.__init__, (self,) + args, kw)

        self.__username = None
        self.__password = None
        self.__nonce = None
        self.__opaque = None

    def setauth(self, username, password):
        self.__username = username
        self.__password = password


def _parse_status(elem):
    text = elem.textof()
    idx1 = string.find(text, ' ')
    idx2 = string.find(text, ' ', idx1+1)
    return int(text[idx1:idx2]), text[idx2+1:]


class _blank:

    def __init__(self, **kw):
        self.__dict__.update(kw)


class _propstat(_blank):
    pass


class _response(_blank):
    pass


class _multistatus(_blank):
    pass


def _extract_propstat(elem):
    ps = _propstat(prop={}, status=None, responsedescription=None)
    for child in elem.children:
        if child.ns != 'DAV:':
            continue
        if child.name == 'prop':
            for prop in child.children:
                ps.prop[(prop.ns, prop.name)] = prop
        elif child.name == 'status':
            ps.status = _parse_status(child)
        elif child.name == 'responsedescription':
            ps.responsedescription = child.textof()
        ### unknown element name

    return ps


def _extract_response(elem):
    resp = _response(href=[], status=None, responsedescription=None, propstat=[])
    for child in elem.children:
        if child.ns != 'DAV:':
            continue
        if child.name == 'href':
            resp.href.append(child.textof())
        elif child.name == 'status':
            resp.status = _parse_status(child)
        elif child.name == 'responsedescription':
            resp.responsedescription = child.textof()
        elif child.name == 'propstat':
            resp.propstat.append(_extract_propstat(child))
        ### unknown child element

    return resp


def _extract_msr(root):
    if root.ns != 'DAV:' or root.name != 'multistatus':
        raise 'invalid response: <DAV:multistatus> expected'

    msr = _multistatus(responses=[ ], responsedescription=None)

    for child in root.children:
        if child.ns != 'DAV:':
            continue
        if child.name == 'responsedescription':
            msr.responsedescription = child.textof()
        elif child.name == 'response':
            msr.responses.append(_extract_response(child))
        ### unknown child element

    return msr


def _extract_locktoken(root):
    if root.ns != 'DAV:' or root.name != 'prop':
        raise 'invalid response: <DAV:prop> expected'
    elem = root.find('lockdiscovery', 'DAV:')
    if not elem:
        raise 'invalid response: <DAV:lockdiscovery> expected'
    elem = elem.find('activelock', 'DAV:')
    if not elem:
        raise 'invalid response: <DAV:activelock> expected'
    elem = elem.find('locktoken', 'DAV:')
    if not elem:
        raise 'invalid response: <DAV:locktoken> expected'
    elem = elem.find('href', 'DAV:')
    if not elem:
        raise 'invalid response: <DAV:href> expected'
    return elem.textof()


class DAVResponse(httplib.HTTPResponse):

    def parse_multistatus(self):
        self.root = qp_xml.Parser().parse(self)
        self.msr = _extract_msr(self.root)

    def parse_lock_response(self):
        self.root = qp_xml.Parser().parse(self)
        self.locktoken = _extract_locktoken(self.root)


class DAV(HTTPConnectionAuth):

    response_class = DAVResponse

    def get(self, url, extra_hdrs={ }):
        return self._request('GET', url, extra_hdrs=extra_hdrs)

    def head(self, url, extra_hdrs={ }):
        return self._request('HEAD', url, extra_hdrs=extra_hdrs)

    def post(self, url, data={ }, body=None, extra_hdrs={ }):
        headers = extra_hdrs.copy()

        assert body or data, "body or data must be supplied"
        assert not (body and data), "cannot supply both body and data"
        if data:
            body = ''
            for key, value in data.items():
                if isinstance(value, types.ListType):
                    for item in value:
                        body = body + '&' + key + '=' + urllib.quote(str(item))
                else:
                    body = body + '&' + key + '=' + urllib.quote(str(value))
            body = body[1:]
            headers['Content-Type'] = 'application/x-www-form-urlencoded'

        return self._request('POST', url, body, headers)

    def options(self, url='*', extra_hdrs={ }):
        return self._request('OPTIONS', url, extra_hdrs=extra_hdrs)

    def trace(self, url, extra_hdrs={ }):
        return self._request('TRACE', url, extra_hdrs=extra_hdrs)

    def put(self, url, contents,
            content_type=None, content_enc=None, extra_hdrs={ }):

        if not content_type:
            content_type, content_enc = mimetypes.guess_type(url)

        headers = extra_hdrs.copy()
        if content_type:
            headers['Content-Type'] = content_type
        if content_enc:
            headers['Content-Encoding'] = content_enc
        return self._request('PUT', url, contents, headers)

    def delete(self, url, extra_hdrs={ }):
        return self._request('DELETE', url, extra_hdrs=extra_hdrs)

    def propfind(self, url, body=None, depth=None, extra_hdrs={ }):
        headers = extra_hdrs.copy()
        headers['Content-Type'] = XML_CONTENT_TYPE
        if depth is not None:
            headers['Depth'] = str(depth)
        return self._request('PROPFIND', url, body, headers)

    def proppatch(self, url, body, extra_hdrs={ }):
        headers = extra_hdrs.copy()
        headers['Content-Type'] = XML_CONTENT_TYPE
        return self._request('PROPPATCH', url, body, headers)

    def mkcol(self, url, extra_hdrs={ }):
        return self._request('MKCOL', url, extra_hdrs=extra_hdrs)

    def move(self, src, dst, extra_hdrs={ }):
        headers = extra_hdrs.copy()
        headers['Destination'] = dst
        return self._request('MOVE', src, extra_hdrs=headers)

    def copy(self, src, dst, depth=None, extra_hdrs={ }):
        headers = extra_hdrs.copy()
        headers['Destination'] = dst
        if depth is not None:
            headers['Depth'] = str(depth)
        return self._request('COPY', src, extra_hdrs=headers)

    def lock(self, url, owner='', timeout=None, depth=None,
             scope='exclusive', type='write', extra_hdrs={ }):
        headers = extra_hdrs.copy()
        headers['Content-Type'] = XML_CONTENT_TYPE
        if depth is not None:
            headers['Depth'] = str(depth)
        if timeout is not None:
            headers['Timeout'] = timeout
        body = XML_DOC_HEADER + \
            '<DAV:lockinfo xmlns:DAV="DAV:">' + \
            '<DAV:lockscope><DAV:%s/></DAV:lockscope>' % scope + \
            '<DAV:locktype><DAV:%s/></DAV:locktype>' % type + \
            owner + \
            '</DAV:lockinfo>'
        return self._request('LOCK', url, body, extra_hdrs=headers)

    def unlock(self, url, locktoken, extra_hdrs={ }):
        headers = extra_hdrs.copy()
        if locktoken[0] != '<':
            locktoken = '<' + locktoken + '>'
        headers['Lock-Token'] = locktoken
        return self._request('UNLOCK', url, extra_hdrs=headers)

    def _request(self, method, url, body=None, extra_hdrs={}):
        "Internal method for sending a request."

        self.request(method, url, body, extra_hdrs)
        return self.getresponse()


    #
    # Higher-level methods for typical client use
    #
    def allprops(self, url, depth=None):
        return self.propfind(url, depth=depth)

    def propnames(self, url, depth=None):
        body = XML_DOC_HEADER + \
            '<DAV:propfind xmlns:DAV="DAV:"><DAV:propname/></DAV:propfind>'
        return self.propfind(url, body, depth)

    def getprops(self, url, *names, **kw):
        assert names, 'at least one property name must be provided'
        if kw.has_key('ns'):
            xmlns = ' xmlns:NS="' + kw['ns'] + '"'
            ns = 'NS:'
            del kw['ns']
        else:
            xmlns = ns = ''
        if kw.has_key('depth'):
            depth = kw['depth']
            del kw['depth']
        else:
            depth = 0
        assert not kw, 'unknown arguments'
        body = XML_DOC_HEADER + \
            '<DAV:propfind xmlns:DAV="DAV:"' + xmlns + '><DAV:prop><' + ns + \
            string.joinfields(names, '/><' + ns) + \
            '/></DAV:prop></DAV:propfind>'
        return self.propfind(url, body, depth)

    def delprops(self, url, *names, **kw):
        assert names, 'at least one property name must be provided'
        if kw.has_key('ns'):
            xmlns = ' xmlns:NS="' + kw['ns'] + '"'
            ns = 'NS:'
            del kw['ns']
        else:
            xmlns = ns = ''
        assert not kw, 'unknown arguments'
        body = XML_DOC_HEADER + \
            '<DAV:propertyupdate xmlns:DAV="DAV:"' + xmlns + \
            '><DAV:remove><DAV:prop><' + ns + \
            string.joinfields(names, '/><' + ns) + \
            '/></DAV:prop></DAV:remove></DAV:propertyupdate>'
        return self.proppatch(url, body)

    def setprops(self, url, *xmlprops, **props):
        assert xmlprops or props, 'at least one property must be provided'
        xmlprops = list(xmlprops)
        if props.has_key('ns'):
            xmlns = ' xmlns:NS="' + props['ns'] + '"'
            ns = 'NS:'
            del props['ns']
        else:
            xmlns = ns = ''
        for key, value in props.items():
            if value:
                xmlprops.append('<%s%s>%s</%s%s>' % (ns, key, value, ns, key))
            else:
                xmlprops.append('<%s%s/>' % (ns, key))
        elems = string.joinfields(xmlprops, '')
        body = XML_DOC_HEADER + \
            '<DAV:propertyupdate xmlns:DAV="DAV:"' + xmlns + \
            '><DAV:set><DAV:prop>' + \
            elems + \
            '</DAV:prop></DAV:set></DAV:propertyupdate>'
        return self.proppatch(url, body)

    def get_lock(self, url, owner='', timeout=None, depth=None):
        response = self.lock(url, owner, timeout, depth)
        response.parse_lock_response()
        return response.locktoken
