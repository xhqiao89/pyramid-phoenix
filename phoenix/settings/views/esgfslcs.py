from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound
from deform import Form
from deform import ValidationFailure

from phoenix.views import MyView
from phoenix.settings.schema import ESGFSLCSSchema
from phoenix.events import SettingsChanged

import logging
logger = logging.getLogger(__name__)


@view_defaults(permission='admin', layout='default')
class ESGFSLCSSettings(MyView):
    def __init__(self, request):
        super(ESGFSLCSSettings, self).__init__(request, name='settings_esgf', title='ESGF')
        self.collection = self.request.db.settings

    def breadcrumbs(self):
        breadcrumbs = super(ESGFSLCSSettings, self).breadcrumbs()
        breadcrumbs.append(dict(route_path=self.request.route_path('settings'), title="Settings"))
        breadcrumbs.append(dict(route_path=self.request.route_path(self.name), title=self.title))
        return breadcrumbs

    def generate_form(self):
        return Form(schema=ESGFSLCSSchema(), buttons=('submit',), formid='deform')

    def process_form(self, form):
        try:
            controls = self.request.POST.items()
            appstruct = form.validate(controls)
        except ValidationFailure, e:
            logger.exception('validation of ESGF form failed')
            return dict(title=self.title, form=e.render())
        except Exception, e:
            msg = 'saving of ESGF settings failed'
            logger.exception(msg)
            self.session.flash(msg, queue="danger")
        else:
            settings = self.collection.find_one() or {}
            settings.update(appstruct)
            self.collection.save(settings)
            self.request.registry.notify(SettingsChanged(self.request, appstruct))
            self.session.flash('Successfully updated ESGF settings!', queue='success')
        return HTTPFound(location=self.request.route_path('settings_esgf'))

    def appstruct(self):
        return self.collection.find_one() or {}

    @view_config(route_name='settings_esgf', renderer='../templates/settings/default.pt')
    def view(self):
        form = self.generate_form()
        if 'submit' in self.request.POST:
            return self.process_form(form)
        return dict(title=self.title, form=form.render(self.appstruct()))
