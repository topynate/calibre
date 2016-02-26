#!/usr/bin/env python2
# vim:fileencoding=utf-8
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__ = 'GPL v3'
__copyright__ = '2015, Kovid Goyal <kovid at kovidgoyal.net>'

from itertools import izip_longest
from collections import namedtuple, OrderedDict
from operator import attrgetter
from functools import partial

Option = namedtuple('Option', 'name default longdoc shortdoc choices')

class Choices(frozenset):
    def __new__(cls, *args):
        self = super(Choices, cls).__new__(cls, args)
        self.default = args[0]
        return self

raw_options = (

    _('Path to the SSL certificate file'),
    'ssl_certfile', None,
    None,

    _('Path to the SSL private key file'),
    'ssl_keyfile', None,
    None,

    _('Time (in seconds) after which an idle connection is closed'),
    'timeout', 120.0,
    None,

    _('Total time in seconds to wait for clean shutdown'),
    'shutdown_timeout', 5.0,
    None,

    _('Enable/disable socket pre-allocation, for example, with systemd socket activation'),
    'allow_socket_preallocation', True,
    None,

    _('Max. size of single HTTP header (in KB)'),
    'max_header_line_size', 8.0,
    None,

    _('Max. allowed size for files uploaded to the server (in MB)'),
    'max_request_body_size', 500.0,
    None,

    _('Minimum size for which responses use data compression (in bytes)'),
    'compress_min_size', 1024,
    None,

    _('Number of worker threads used to process requests'),
    'worker_count', 10,
    None,

    _('The port on which to listen for connections'),
    'port', 8080,
    None,

    _('A prefix to prepend to all URLs'),
    'url_prefix', None,
    _('Useful if you wish to run this server behind a reverse proxy.'),

    _('Advertise OPDS feeds via BonJour'),
    'use_bonjour', True,
    _('Advertise the OPDS feeds via the BonJour service, so that OPDS based'
    ' reading apps can detect and connect to the server automatically.'),

    _('Maximum number of books in OPDS feeds'),
    'max_opds_items', 30,
    _('The maximum number of books that the server will return in a single'
    ' OPDS acquisition feed.'),

    _('Maximum number of ungrouped items in OPDS feeds'),
    'max_opds_ungrouped_items', 100,
    _('Group items in categories such as author/tags by first letter when'
    ' there are more than this number of items. Set to zero to disable.'),

    _('The interface on which to listen for connections'),
    'listen_on', '0.0.0.0',
    _('The default is to listen on all available interfaces. You can change this to, for'
    ' example, "127.0.0.1" to only listen for connections from the local machine, or'
    ' to "::" to listen to all incoming IPv6 and IPv4 connections.'),

    _('Fallback to auto-detected interface'),
    'fallback_to_detected_interface', True,
    _('If for some reason the server is unable to bind to the interface specified in'
    ' the listen_on option, then it will try to detect an interface that connects'
    ' to the outside world and bind to that.'),

    _('Enable/disable zero copy file transfers for increased performance'),
    'use_sendfile', True,
    _('This will use zero-copy in-kernel transfers when sending files over the network,'
    ' increasing performance. However, it can cause corrupted file transfers on some'
    ' broken filesystems. If you experience corrupted file transfers, turn it off.'),

    _('Max. log file size (in MB)'),
    'max_log_size', 20,
    _('The maximum size of log files, generated by the server. When the log becomes larger'
    ' than this size, it is automatically rotated. Set to zero to disable log rotation.'),

    _('Enable/disable logging of not found http requests'),
    'log_not_found', True,
    _('By default, the server logs all HTTP requests for resources that are not found.'
    ' This can generate a lot of log spam, if your server is targeted by bots.'
    ' Use this option to turn it off.'),

    _('Enable/disable password based authentication to access the server'),
    'auth', False,
    _('By default, the server is unrestricted, allowing anyone to access it. You can'
    ' restrict access to predefined users with this option.'),

    _('Path to user database'),
    'userdb', None,
    _('Path to a file in which to store the user and password information. By default a'
    ' file in the calibre configuration directory is used.'),

    _('Choose the type of authentication used'),
    'auth_mode', Choices('auto', 'basic', 'digest'),
    _('Set the HTTP authentication mode used by the server. Set to "basic" is you are'
    ' putting this server behind an SSL proxy. Otherwise, leave it as "auto", which'
    ' will use "basic" if SSL is configured otherwise it will use "digest".'),

    _('Ignored user-defined metadata fields'),
    'ignored_fields', None,
    _('Comma separated list of user-defined metadata fields that will not be displayed'
      ' by the content server in the /opds and /mobile views.'),

    _('Only display user-defined fields'),
    'displayed_fields', None,
    _('Comma separated list of user-defined metadata fields that will be displayed'
      ' by the content server in the /opds and /mobile views. If you specify this'
      ' option, any fields not in this list will not be displayed.'),


)
assert len(raw_options) % 4 == 0

options = []

def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return izip_longest(*args, fillvalue=fillvalue)

for shortdoc, name, default, doc in grouper(4, raw_options):
    choices = None
    if isinstance(default, Choices):
        choices = sorted(default)
        default = default.default
    options.append(Option(name, default, doc, shortdoc, choices))
options = OrderedDict([(o.name, o) for o in sorted(options, key=attrgetter('name'))])
del raw_options

class Options(object):

    __slots__ = tuple(name for name in options)

    def __init__(self, **kwargs):
        for opt in options.itervalues():
            setattr(self, opt.name, kwargs.get(opt.name, opt.default))

def opt_to_cli_help(opt):
    ans = opt.shortdoc
    if not ans.endswith('.'):
        ans += '.'
    if opt.longdoc:
        ans += '\n\t' + opt.longdoc
    return ans

def boolean_option(add_option, opt):
    name = opt.name.replace('_', '-')
    help = opt_to_cli_help(opt)
    add_option('--enable-' + name, action='store_true', help=help)
    add_option('--disable-' + name, action='store_false', help=help)

def opts_to_parser(usage):
    from calibre.utils.config import OptionParser
    parser =  OptionParser(usage)
    for opt in options.itervalues():
        add_option = partial(parser.add_option, dest=opt.name, help=opt_to_cli_help(opt), default=opt.default)
        if opt.default is True or opt.default is False:
            boolean_option(add_option, opt)
        elif opt.choices:
            name = '--' + opt.name.replace('_', '-')
            add_option(name, choices=opt.choices)
        else:
            name = '--' + opt.name.replace('_', '-')
            otype = 'string'
            if isinstance(opt.default, (int, long, float)):
                otype = type(opt.default).__name__
            add_option(name, type=otype)

    return parser
