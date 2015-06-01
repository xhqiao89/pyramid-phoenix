from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from phoenix.views.settings import SettingsView

import logging
logger = logging.getLogger(__name__)

class Jobs(SettingsView):
    def __init__(self, request):
        super(Jobs, self).__init__(request, name='settings_jobs', title='Jobs')
        self.jobsdb = self.request.db.jobs

    def breadcrumbs(self):
        breadcrumbs = super(Jobs, self).breadcrumbs()
        breadcrumbs.append(dict(route_path=self.request.route_path(self.name), title=self.title))
        return breadcrumbs

    @view_config(route_name='remove_all_jobs')
    def remove_all(self):
        count = self.jobsdb.count()
        self.jobsdb.drop()
        self.session.flash("%d Jobs deleted." % count, queue='info')
        return HTTPFound(location=self.request.route_path(self.name))

    @view_config(route_name='settings_jobs', renderer='phoenix:templates/settings/jobs.pt')
    def view(self):
        jobs = list(self.jobsdb.find().sort('created', -1))
        
        from phoenix.grid.jobs import JobsGrid
        grid = JobsGrid(self.request, jobs,
                ['status', 'job', 'email', 'duration', 'finished', 'progress', ''],
            )
        return dict(grid=grid)


