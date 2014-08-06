import colander

from deform.widget import (
    RadioChoiceWidget,
    TextInputWidget,
    PasswordWidget,
    TextAreaWidget
    )
from .widget import (
    TagsWidget,
    EsgSearchWidget,
    EsgFilesWidget
    )

import logging
logger = logging.getLogger(__name__)

class CredentialsSchema(colander.MappingSchema):
    """
    ESGF user credentials schema
    """
    openid = colander.SchemaNode(
        colander.String(),
        title = "OpenID",
        description = "OpenID from your ESGF provider",
        validator = colander.url,
        missing = '',
        default = '',
        widget = TextInputWidget(template='readonly/textinput'),
        )
    password = colander.SchemaNode(
        colander.String(),
        title = 'Password',
        description = 'Password for this OpenID',
        missing = '',
        default = '',
        widget = PasswordWidget(size=20))

class AccountSchema(colander.MappingSchema):
    """
    User account schema
    """
    name = colander.SchemaNode(
        colander.String(),
        title = "Name",
        description = "Your Name",
        missing = '',
        default = '',
        )
    email = colander.SchemaNode(
        colander.String(),
        title = "EMail",
        description = "eMail used for login",
        validator = colander.Email(),
        missing = '',
        widget = TextInputWidget(template='readonly/textinput'),
        )
    openid = colander.SchemaNode(
        colander.String(),
        title = "OpenID",
        description = "OpenID to access ESGF data",
        validator = colander.url,
        missing = '',
        default = '',
        )
    organisation = colander.SchemaNode(
        colander.String(),
        title = "Organisation",
        description = "Your Organisation",
        missing = '',
        default = '',
        )
    notes = colander.SchemaNode(
        colander.String(),
        title = "Notes",
        description = "Some Notes about you",
        missing = '',
        default = '',
        )
    token = colander.SchemaNode(
        colander.String(),
        title = "Token",
        description = "Access Token",
        missing = '',
        widget = TextInputWidget(template='readonly/textinput'),
        )
    credentials = colander.SchemaNode(
        colander.String(),
        title = "Credentials",
        description = "URL to ESGF Proxy Certificate",
        validator = colander.url,
        missing = '',
        widget = TextInputWidget(template='readonly/textinput'),
        )
    cert_expires = colander.SchemaNode(
        colander.String(),
        title = "Expires",
        description = "When your Proxy Certificate expires",
        missing = '',
        widget = TextInputWidget(template='readonly/textinput'),
        )

@colander.deferred
def deferred_wps_list_widget(node, kw):
    wps_list = kw.get('wps_list', [])
    logger.debug('wps_list %s', wps_list)
    choices = []
    for wps in wps_list:
        title = "%s (%s)" % (wps.get('title'), wps.get('notes'))
        choices.append((wps.get('url'), title))
    return RadioChoiceWidget(values = choices)

class ChooseWPSSchema(colander.MappingSchema):
    url = colander.SchemaNode(
        colander.String(),
        title = 'WPS',
        description = "Select WPS",
        widget = deferred_wps_list_widget
        )

@colander.deferred
def deferred_choose_process_widget(node, kw):
    processes = kw.get('processes', [])

    choices = []
    for process in processes:
        title = "%s [%s]" % (process.title, process.identifier)
        choices.append( (process.identifier, title) )
    return RadioChoiceWidget(values = choices)

class SelectProcessSchema(colander.MappingSchema):
    identifier = colander.SchemaNode(
        colander.String(),
        widget = deferred_choose_process_widget)

@colander.deferred
def deferred_choose_input_parameter_widget(node, kw):
    process = kw.get('process', [])

    choices = []
    for dataInput in process.dataInputs:
        if dataInput.dataType == 'ComplexData':
            choices.append( (dataInput.identifier, dataInput.title) )
    return RadioChoiceWidget(values = choices)

class ChooseInputParamterSchema(colander.MappingSchema):
    identifier = colander.SchemaNode(
        colander.String(),
        widget = deferred_choose_input_parameter_widget)

class ChooseSourceSchema(colander.MappingSchema):
    choices = [('wizard_csw', "CSW Catalog Search"), ('wizard_esgf', "ESGF Source")]
    source = colander.SchemaNode(
        colander.String(),
        widget = RadioChoiceWidget(values = choices))

def esgsearch_validator(node, value):
    import json
    search = json.loads(value)
    if search.get('hit-count', 0) > 20:
        raise Invalid(node, 'More than 20 datasets selected: %r.' %  search['hit-count'])

class ESGFSearchSchema(colander.MappingSchema):
    selection = colander.SchemaNode(
        colander.String(),
        validator = esgsearch_validator,
        title = 'ESGF Search',
        #missing = '{"query": "project:CORDEX"}',
        #default = '{"query": "project:CORDEX"}',
        widget = EsgSearchWidget(url="/esg-search"))

@colander.deferred
def deferred_esgf_files_widget(node, kw):
    import json
    selection = kw.get('selection', {})
    search = json.loads(selection)
    return EsgFilesWidget(url="/esg-search", search_type='File', search=search)
class ESGFFilesSchema(colander.MappingSchema):
    url = colander.SchemaNode(
        colander.Set(),
        description = 'URL',
        widget = deferred_esgf_files_widget)

class CatalogSchema(colander.MappingSchema):
    url = colander.SchemaNode(
        colander.String(),
        title = 'URL',
        description = 'Add WPS URL',
        missing = '',
        default = '',
        validator = colander.url,
        widget = TextInputWidget())

    notes = colander.SchemaNode(
        colander.String(),
        title = 'Notes',
        description = 'Add some notes for this WPS',
        missing = '',
        default = '',
        widget = TextInputWidget())

class PublishSchema(colander.MappingSchema):
    title = colander.SchemaNode(
        colander.String(),
        widget = TextInputWidget(),
        )
    abstract = colander.SchemaNode(
        colander.String(),
        missing = '',
        default = '',
        validator = colander.Length(max=150),
        widget = TextAreaWidget(rows=2, cols=80),
        )
    creator = colander.SchemaNode(
        colander.String(),
        validator = colander.Email(),
        widget = TextInputWidget(),
        )
    url = colander.SchemaNode(
        colander.String(),
        title = 'URL',
        validator = colander.url,
        widget = TextInputWidget())
    mime_type = colander.SchemaNode(
        colander.String(),
        widget = TextInputWidget(),
        )
    keywords = colander.SchemaNode(
        colander.String(),
        default = 'test',
        missing = 'test',
        widget = TagsWidget(),
        )
            
class UserSchema(colander.MappingSchema):
    name = colander.SchemaNode(
        colander.String(),
        title = "Name",
        missing = colander.drop,
        )
    user_id = colander.SchemaNode(
        colander.String(),
        title = "eMail",
        validator = colander.Email(),
        widget = TextInputWidget(),
        )
    openid = colander.SchemaNode(
        colander.String(),
        title = "OpenID",
        validator = colander.url,
        missing = colander.drop,
        )
    organisation = colander.SchemaNode(
        colander.String(),
        title = "Organisation",
        missing = colander.drop,
        )
    notes = colander.SchemaNode(
        colander.String(),
        title = "Notes",
        missing = colander.drop,
        )


