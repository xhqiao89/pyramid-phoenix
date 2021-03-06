"""
see pyramid security:

* http://docs.pylonsproject.org/projects/pyramid/en/latest/tutorials/wiki2/authentication.html
"""

from collections import OrderedDict

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.exceptions import HTTPForbidden
from pyramid.security import (
    Allow,
    Everyone,
    Authenticated,
    ALL_PERMISSIONS)

from authomatic import Authomatic, provider_id
from authomatic.providers import oauth2, openid
from phoenix.providers import esgfopenid

from phoenix.twitcherclient import is_public

import logging
logger = logging.getLogger(__name__)

Admin = 'group.admin'
User = 'group.user'
Guest = 'group.guest'

AUTH_PROTOCOLS = OrderedDict([
    ('phoenix', 'Phoenix'),
    ('esgf', 'ESGF OpenID'),
    ('openid', 'OpenID'),
    ('oauth2', 'OAuth 2.0'),
    ('ldap', 'LDAP')])


def has_execute_permission(request, service_name):
    return is_public(request.registry, service_name) or request.has_permission('submit')


def allowed_auth_protocols(request):
    # TODO: refactor auth settings handling
    settings = request.db.settings.find_one() or {}
    protocols = ['phoenix', 'esgf', 'oauth2']
    if 'auth_protocol' in settings:
        protocols.extend(settings['auth_protocol'])
    return protocols


def default_auth_protocol(request):
    allowed_protocols = allowed_auth_protocols(request)
    # use reverse order to get defaul protocol
    for protocol in AUTH_PROTOCOLS.keys()[::-1]:
        if protocol in allowed_protocols:
            return protocol


def passwd_check(request, passphrase):
    """
    code taken from IPython.lib.security
    TODO: maybe import ipython

    >>> passwd_check('sha1:0e112c3ddfce:a68df677475c2b47b6e86d0467eec97ac5f4b85a',
    ...              'anotherpassword')
    False
    """
    import hashlib
    hashed_passphrase = request.registry.settings.get('phoenix.password', u'')

    try:
        algorithm, salt, pw_digest = hashed_passphrase.split(':', 2)
    except (ValueError, TypeError):
        return False

    try:
        h = hashlib.new(algorithm)
    except ValueError:
        return False

    if len(pw_digest) == 0:
        return False

    try:
        h.update(passphrase.encode('utf-8') + salt.encode('ascii'))
    except:
        return False

    return h.hexdigest() == pw_digest


def groupfinder(userid, request):
    user = request.db.users.find_one({'identifier': userid})
    if user:
        if user.get('group') == Admin:
            return [Admin]
        elif user.get('group') == User:
            return [User]
        else:
            return [Guest]
    return HTTPForbidden()


# Authentication and Authorization

class Root():
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, Authenticated, 'edit'),
        (Allow, User, 'submit'),
        (Allow, Admin, ALL_PERMISSIONS)
    ]

    def __init__(self, request):
        self.request = request


def root_factory(request):
    return Root(request)

# Authomatic


def authomatic(request):
    return Authomatic(
        config=authomatic_config(request),
        secret=request.registry.settings.get('authomatic.secret'),
        report_errors=True,
        logging_level=logger.level)


def authomatic_config(request):

    DEFAULTS = {
        'popup': True,
    }

    OPENID = {
        'openid': {
            'class_': openid.OpenID,
        },
    }

    ESGF = {
        'dkrz': {
            'class_': esgfopenid.ESGFOpenID,
            'hostname': 'esgf-data.dkrz.de',
        },
        'ipsl': {
            'class_': esgfopenid.ESGFOpenID,
            'hostname': 'esgf-node.ipsl.fr',
        },
        'badc': {
            'class_': esgfopenid.ESGFOpenID,
            'hostname': 'ceda.ac.uk',
            'provider_url': 'https://{hostname}/openid/{username}'
        },
        'pcmdi': {
            'class_': esgfopenid.ESGFOpenID,
            'hostname': 'pcmdi.llnl.gov',
        },
        'smhi': {
            'class_': esgfopenid.ESGFOpenID,
            'hostname': 'esg-dn1.nsc.liu.se',
        },
    }

    OAUTH2 = {
        'github': {
            'class_': oauth2.GitHub,
            'consumer_key': request.registry.settings.get('github.client.id'),
            'consumer_secret': request.registry.settings.get('github.client.secret'),
            'access_headers': {'User-Agent': 'Phoenix'},
            'id': provider_id(),
            'scope': oauth2.GitHub.user_info_scope,
            '_apis': {
                'Get your events': ('GET', 'https://api.github.com/users/{user.username}/events'),
                'Get your watched repos': ('GET', 'https://api.github.com/user/subscriptions'),
            },
        },
    }

    # Concatenate the configs.
    config = {}
    config.update(OAUTH2)
    config.update(OPENID)
    config.update(ESGF)
    config['__defaults__'] = DEFAULTS
    return config


class MyAuthenticationPolicy(AuthTktAuthenticationPolicy):
    def authenticated_userid(self, request):
        user = request.user
        if user is not None:
            return user.get('identifier')


def get_user(request):
    user_id = request.unauthenticated_userid
    if user_id is not None:
        user = request.db.users.find_one({'identifier': user_id})
        return user


def includeme(config):
    settings = config.get_settings()

    authn_policy = MyAuthenticationPolicy(
        settings.get('authomatic.secret'),
        callback=groupfinder,
        hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()
    config.set_root_factory(root_factory)
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.add_request_method(get_user, 'user', reify=True)
