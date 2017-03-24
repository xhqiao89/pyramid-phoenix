from pyramid.view import view_config
from pyramid.settings import asbool

import datetime

from phoenix.wizard.views import Wizard
from phoenix.utils import user_cert_valid

from phoenix.esgfsearch.schema import ESGFSearchSchema
from phoenix.esgfsearch.search import ESGFSearch

import logging
LOGGER = logging.getLogger(__name__)


def includeme(config):
    config.add_route('wizard_esgf_search', '/wizard/esgfsearch')
    config.add_view('phoenix.wizard.views.esgfsearch.ESGFSearchView',
                    route_name='wizard_esgf_search',
                    attr='view',
                    renderer='phoenix.esgfsearch:templates/esgfsearch/esgfsearch.pt')
    config.add_route('wizard_esgf_logon', '/wizard/esgf_logon')
    config.add_view('phoenix.wizard.views.esgflogon.ESGFLogon',
                    route_name='wizard_esgf_logon',
                    attr='view',
                    renderer='../templates/wizard/default.pt')
    config.add_route('wizard_loading', '/wizard/loading')
    config.add_view('phoenix.wizard.views.esgflogon.ESGFLogon',
                    route_name='wizard_loading',
                    attr='loading',
                    renderer='../templates/wizard/loading.pt')
    config.add_route('wizard_check_logon', '/wizard/check_logon.json')
    config.add_view('phoenix.wizard.views.esgflogon.ESGFLogon',
                    route_name='wizard_check_logon',
                    attr='check_logon',
                    renderer='json')


class ESGFSearchView(Wizard):
    def __init__(self, request):
        super(ESGFSearchView, self).__init__(request, name='wizard_esgf_search', title="ESGF Search")
        self.esgfsearch = ESGFSearch(self.request)

    def breadcrumbs(self):
        breadcrumbs = super(ESGFSearchView, self).breadcrumbs()
        breadcrumbs.append(dict(route_path=self.request.route_path(self.name), title=self.title))
        return breadcrumbs

    def schema(self):
        return ESGFSearchSchema()

    def appstruct(self):
        appstruct = super(ESGFSearchView, self).appstruct()
        appstruct['query'] = self.esgfsearch.query
        appstruct['distrib'] = self.esgfsearch.distrib
        appstruct['replica'] = self.esgfsearch.replica
        appstruct['latest'] = self.esgfsearch.latest
        appstruct['temporal'] = self.esgfsearch.temporal
        if self.esgfsearch.start and self.esgfsearch.end:
            appstruct['start'] = datetime.datetime(int(self.esgfsearch.start), 1, 1)
            appstruct['end'] = datetime.datetime(int(self.esgfsearch.end), 12, 31)
        appstruct['constraints'] = self.esgfsearch.constraints
        LOGGER.debug("esgfsearch appstruct before: %s", appstruct)
        return appstruct

    def next_success(self, appstruct):
        LOGGER.debug("esgfsearch appstruct after: %s", appstruct)
        self.success(appstruct)

        # TODO: need to check pre conditions in wizard
        if not self.request.has_permission('submit') or user_cert_valid(self.request):
            return self.next('wizard_done')
        return self.next('wizard_esgf_logon')

    def custom_view(self):
        result = dict()
        result.update(self.esgfsearch.query_params())
        result.update(self.esgfsearch.search_datasets())
        result['quickview'] = False
        return result
