from pyramid.view import view_config

from phoenix.wizard.views import Wizard
from phoenix.utils import user_cert_valid

import logging
logger = logging.getLogger(__name__)


def includeme(config):
    config.add_route('wizard_esgf_search', '/wizard/esgf_search')
    config.add_view('phoenix.wizard.views.esgfsearch.ESGFSearch',
                    route_name='wizard_esgf_search',
                    attr='view',
                    renderer='../templates/wizard/esgfsearch.pt')
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


class ESGFSearch(Wizard):
    def __init__(self, request):
        super(ESGFSearch, self).__init__(request, name='wizard_esgf_search', title="ESGF Search")

    def breadcrumbs(self):
        breadcrumbs = super(ESGFSearch, self).breadcrumbs()
        breadcrumbs.append(dict(route_path=self.request.route_path(self.name), title=self.title))
        return breadcrumbs

    def schema(self):
        from phoenix.esgfsearch.schema import ESGFSearchSchema
        return ESGFSearchSchema()

    def next_success(self, appstruct):
        self.success(appstruct)

        # TODO: need to check pre conditions in wizard
        if not self.request.has_permission('submit') or user_cert_valid(self.request):
            return self.next('wizard_done')
        return self.next('wizard_esgf_logon')

    def view(self):
        return super(ESGFSearch, self).view()
