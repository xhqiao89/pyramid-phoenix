from pyramid.settings import asbool

from pyesgf.search import SearchConnection
from pyesgf.search.consts import TYPE_DATASET, TYPE_AGGREGATION, TYPE_FILE

import logging
LOGGER = logging.getLogger(__name__)


def date_from_filename(filename):
    """Example cordex:
    tas_EUR-44i_ECMWF-ERAINT_evaluation_r1i1p1_HMS-ALADIN52_v1_mon_200101-200812.nc
    """
    LOGGER.debug('filename=%s', filename)
    result = None
    value = filename.split('.')
    value.pop()  # remove .nc
    value = value[-1]  # part with date
    value = value.split('_')[-1]  # only date part
    LOGGER.debug('date part = %s', value)
    if value != 'fx':
        value = value.split('-')  # split start-end
        start_year = int(value[0][:4])  # keep only the year
        end_year = int(value[1][:4])
        result = (start_year, end_year)
    return result


def variable_filter(constraints, variables):
    """return True if variable fulfills contraints"""
    var_types = ['variable', 'cf_standard_name', 'variable_long_name']

    success = True
    cs = constraints.mixed()
    # check different types of variables
    for var_type in var_types:
        # is there a constrain for this variable type?
        if var_type in cs:
            # at least one variable constraint must be fulfilled
            success = False
            # do we have this variable type?
            if var_type in variables:
                # do we have an allowed value?
                allowed_values = cs.get(var_type)
                if variables[var_type] in allowed_values:
                    # if one variables matches then we are ok
                    return True
    return success


def temporal_filter(filename, start=None, end=None):
    """return True if file is in timerange start/end"""
    # TODO: keep fixed fields fx ... see esgsearch.js
    """
    // fixed fields are always in time range
    if ($.inArray("fx", doc.time_frequency) >= 0) {
    return true;
    }
    """

    LOGGER.debug('filename=%s, start_date=%s, end_date=%s', filename, start, end)

    if start is None or end is None:
        return True
    start_end = date_from_filename(filename)
    if start_end is None:  # fixed field
        return True
    start_year = start_end[0]
    end_year = start_end[1]
    if end and start_year > end:
        LOGGER.debug('skip: %s > %s', start_year, end)
        return False
    if start and end_year < start:
        LOGGER.debug('skip: %s < %s', end_year, start)
        return False
    LOGGER.debug("pass: %s", filename)
    return True


class ESGFSearch(object):
    def __init__(self, request):
        self.request = request
        settings = self.request.registry.settings
        self.selected = self.request.params.get('selected', 'project')
        self.limit = int(self.request.params.get('limit', '0'))
        self.distrib = asbool(self.request.params.get('distrib', 'false'))
        self.latest = asbool(self.request.params.get('latest', 'true'))
        if self.latest is False:
            self.latest = None  # all versions
        self.replica = asbool(self.request.params.get('replica', 'false'))
        if self.replica is True:
            self.replica = None  # master + replica
        if 'start' in self.request.params and 'end' in self.request.params:
            self.temporal = True
            self.start = int(self.request.params['start'])
            self.end = int(self.request.params['end'])
        else:
            self.temporal = False
            self.start = self.end = None
        self.constraints = self.request.params.get('constraints')
        self.conn = SearchConnection(settings.get('esgfsearch.url'), distrib=self.distrib)

    def search_files(self):
        dataset_id = self.request.params.get(
            'dataset_id',
            'cmip5.output1.MPI-M.MPI-ESM-LR.1pctCO2.day.atmos.cfDay.r1i1p1.v20120314|esgf1.dkrz.de')
        ctx = self.conn.new_context(search_type=TYPE_FILE, latest=self.latest, replica=self.replica)
        ctx = ctx.constrain(dataset_id=dataset_id)
        paged_results = []
        for result in ctx.search():
            LOGGER.debug("check: %s", result.filename)
            if temporal_filter(result.filename, self.start, self.end):
                paged_results.append(dict(
                    filename=result.filename,
                    download_url=result.download_url,
                    opendap_url=result.opendap_url,
                ))
        return dict(files=paged_results)

    def search_datasets(self):
        constraints = dict()
        if self.constraints:
            for constrain in self.constraints.split(','):
                if constrain.strip():
                    key, value = constrain.split(':', 1)
                    constraints[key] = value
        ctx = self.conn.new_context(search_type=TYPE_DATASET, latest=self.latest, replica=self.replica)
        ctx = ctx.constrain(**constraints)
        if self.temporal:
            ctx = ctx.constrain(
                from_timestamp="{}-01-01T12:00:00Z".format(self.start),
                to_timestamp="{}-12-31T12:00:00Z".format(self.end))
        results = ctx.search(batch_size=10, ignore_facet_check=False)
        categories = [tag for tag in ctx.facet_counts if len(ctx.facet_counts[tag]) > 1]
        keywords = ctx.facet_counts[self.selected].keys()
        pinned_facets = []
        for facet in ctx.facet_counts:
            if len(ctx.facet_counts[facet]) == 1:
                pinned_facets.append("{}:{}".format(facet, ctx.facet_counts[facet].keys()[0]))
        paged_results = []
        for i in range(0, min(10, ctx.hit_count)):
            paged_results.append(dict(
                id=results[i].json['master_id'],
                title=results[i].json['title'],
                dataset_id=results[i].dataset_id,
                number_of_files=results[i].number_of_files,
                catalog_url=results[i].urls['THREDDS'][0][0]))
        return dict(
            hit_count=ctx.hit_count,
            categories=','.join(categories),
            keywords=','.join(keywords),
            pinned_facets=','.join(pinned_facets),
            results=paged_results)
