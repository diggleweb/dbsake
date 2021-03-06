"""
dbsake.core.mysql.sieve
~~~~~~~~~~~~~~~~~~~~~~~

Filtering API for mysqldump files
"""
from __future__ import unicode_literals

import collections

from dbsake import pycompat
from dbsake.util import compression
from dbsake.util import dotdict

from . import exc
from . import parser
from . import filters
from . import transform
from . import writers

Error = exc.SieveError


class Options(dotdict.DotDict):
    def __init__(self, *args, **kwargs):
        super(Options, self).__init__(*args, **kwargs)
        self.setdefault('sections', [])
        self.setdefault('exclude_sections', [])

    def exclude_section(self, name):
        self.exclude_sections.append(name)


def sieve(options):
    if options.output_format == 'directory':
        pycompat.makedirs(options.directory, exist_ok=True)

    if not options.table_schema:
        options.exclude_section('tablestructure')
        options.exclude_section('view_temporary')
        options.exclude_section('view')

    if not options.table_data:
        options.exclude_section('tabledata')

    if options.routines is False:
        options.exclude_section('routines')

    if options.events is False:
        options.exclude_section('events')

    if options.triggers is False:
        options.exclude_section('triggers')

    with compression.decompressed(options.input_stream) as input_stream:
        dump_parser = parser.DumpParser(stream=input_stream)
        filter_section = filters.SectionFilter(options)
        transform_section = transform.SectionTransform(options)
        write_section = writers.load(options, context=transform_section)

        stats = collections.defaultdict(int)

        for section in dump_parser:
            if filter_section(section):
                continue
            stats[section.name] += 1
            transform_section(section)
            write_section(section)

    return stats
