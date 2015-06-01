from pyramid.view import view_config

from pyramid.httpexceptions import HTTPException, HTTPFound, HTTPNotFound

from . import SettingsView

import logging
logger = logging.getLogger(__name__)

class Catalog(SettingsView):
    def __init__(self, request):
        super(Catalog, self).__init__(
            request, name='settings_catalog', title='Catalog')
        self.csw = self.request.csw
        self.description = self.csw.identification.title

    def breadcrumbs(self):
        breadcrumbs = super(Catalog, self).breadcrumbs()
        breadcrumbs.append(dict(route_path=self.request.route_path(self.name), title=self.title))
        return breadcrumbs
        
    @view_config(route_name='remove_all_records')
    def remove_all(self):
        try:
            self.csw.getrecords2(maxrecords=0)
            count = self.csw.results.get('matches'),
            self.csw.transaction(ttype='delete', typename='csw:Record')
            self.session.flash("%d Records deleted." % count, queue='info')
        except Exception,e:
            logger.exception('could not remove datasets.')
            self.session.flash('Ooops ... self destruction out of order. %s' % e, queue="danger")
        return HTTPFound(location=self.request.route_path(self.name))
 
    @view_config(route_name='remove_record')
    def remove(self):
        try:
            recordid = self.request.matchdict.get('recordid')
            self.csw.transaction(ttype='delete', typename='csw:Record', identifier=recordid )
            self.session.flash('Removed record %s.' % recordid, queue="info")
        except Exception,e:
            logger.exception("Could not remove record")
            self.session.flash('Could not remove record. %s' % e, queue="danger")
        return HTTPFound(location=self.request.route_path(self.name))

    @view_config(route_name="settings_catalog", renderer='../templates/settings/catalog.pt')
    def view(self):
        self.csw.getrecords2(esn="full", maxrecords=20)
            
        grid = CSWGrid(
                self.request,
                self.csw.records.values(),
                ['title', 'format', ''],
            )
        self.csw.getrecords2(maxrecords=0)
        return dict(datasets_found=self.csw.results.get('matches'), grid=grid)

from phoenix.grid import MyGrid
class CSWGrid(MyGrid):
    def __init__(self, request, *args, **kwargs):
        super(CSWGrid, self).__init__(request, *args, **kwargs)
        self.column_formats[''] = self.action_td
        self.column_formats['title'] = self.title_td
        self.column_formats['format'] = self.format_td
        self.column_formats['modified'] = self.modified_td
        self.exclude_ordering = self.columns

    def title_td(self, col_num, i, item):
        return self.render_title_td(item.title, item.abstract, item.subjects)

    def format_td(self, col_num, i, item):
        return self.render_format_td(item.format, item.source)

    def modified_td(self, col_num, i, item):
        return self.render_time_ago_td(from_time=item.modified)

    def action_td(self, col_num, i, item):
        buttongroup = []
        buttongroup.append(
            ("remove", item.identifier, "glyphicon glyphicon-trash text-danger", "",
            self.request.route_path('remove_record', recordid=item.identifier),
            False) )
        return self.render_action_td(buttongroup)
       
