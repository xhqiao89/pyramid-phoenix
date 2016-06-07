import colander
from deform.widget import RadioChoiceWidget

from pyramid.view import view_config

from owslib.wps import WebProcessingService
from twitcher.registry import proxy_url

from phoenix.wizard.views import Wizard

class SourceSchemaNode(colander.SchemaNode):
    schema_type = colander.String

    def after_bind(self, node, kw):
        choices = [
            ('wizard_esgf_search', "Earth System Grid (ESGF)"),
            #('wizard_swift_login', "Swift Cloud"),
            ('wizard_threddsservice', "Thredds Catalog Service"),
            ('wizard_upload', "Local Storage"),           
            ]
        if kw['request'].solr_activated:
            choices.append( ('wizard_solr', "Birdhouse Solr Search") )
        self.widget = RadioChoiceWidget(values = choices)

class Schema(colander.MappingSchema):
    source = SourceSchemaNode()

class ChooseSource(Wizard):
    def __init__(self, request):
        super(ChooseSource, self).__init__(
            request, name='wizard_source', title="Choose Data Source")
        wps = WebProcessingService(proxy_url(request, self.wizard_state.get('wizard_wps')['identifier']),
                                        verify=False, skip_caps=True)
        process = wps.describeprocess(self.wizard_state.get('wizard_process')['identifier'])
        for data_input in process.dataInputs:
            if data_input.identifier == self.wizard_state.get('wizard_complex_inputs')['identifier']:
                self.title = "Choose Data Source for %s" % data_input.title
                break
        #self.description = self.wizard_state.get('wizard_complex_inputs')['identifier']

    def breadcrumbs(self):
        breadcrumbs = super(ChooseSource, self).breadcrumbs()
        breadcrumbs.append(dict(route_path=self.request.route_path(self.name), title=self.title))
        return breadcrumbs
        
    def schema(self):
        return Schema().bind(request=self.request)

    def next_success(self, appstruct):
        self.success(appstruct)
        return self.next( appstruct.get('source') )
        
    @view_config(route_name='wizard_source', renderer='../templates/wizard/default.pt')
    def view(self):
        return super(ChooseSource, self).view()
    
