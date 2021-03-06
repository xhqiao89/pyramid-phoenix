from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound
from deform import Form
from deform import ValidationFailure

from phoenix.views import MyView
from phoenix.settings.schema import AuthProtocolSchema as Schema

import logging
logger = logging.getLogger(__name__)


@view_defaults(permission='admin', layout='default')
class Auth(MyView):
    def __init__(self, request):
        super(Auth, self).__init__(request, name='settings_auth', title='Auth')
        self.collection = self.request.db.settings

    def breadcrumbs(self):
        breadcrumbs = super(Auth, self).breadcrumbs()
        breadcrumbs.append(dict(route_path=self.request.route_path('settings'), title="Settings"))
        breadcrumbs.append(dict(route_path=self.request.route_path(self.name), title=self.title))
        return breadcrumbs

    def generate_form(self):
        return Form(schema=Schema(), buttons=('submit',), formid='deform')

    def process_form(self, form):
        try:
            controls = self.request.POST.items()
            appstruct = form.validate(controls)
        except ValidationFailure, e:
            logger.exception('validation of user form failed')
            return dict(title=self.title, form=e.render())
        except Exception as e:
            logger.exception('edit auth failed.')
            self.session.flash('Edit auth failed. {}'.format(e), queue="danger")
        else:
            settings = self.collection.find_one() or {}
            protocols = list(appstruct['auth_protocol'])
            if 'phoenix' not in protocols:
                protocols.append('phoenix')
            settings.update({'auth_protocol': protocols})
            self.collection.save(settings)
            #self.request.registry.notify(SettingsChanged(self.request, appstruct))
            self.session.flash('Successfully updated Auth settings!', queue='success')
        return HTTPFound(location=self.request.route_path('settings_auth'))

    def appstruct(self):
        return self.collection.find_one() or {}

    @view_config(route_name='settings_auth', renderer='../templates/settings/auth.pt')
    def view(self):
        form = self.generate_form()
        if 'submit' in self.request.POST:
            return self.process_form(form)
        return dict(title=self.title, form=form.render(self.appstruct()))
