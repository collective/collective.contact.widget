from collective.contact.core.testing import COLLECTIVE_CONTACT_CORE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.testing.zope import WSGI_SERVER_FIXTURE


# collective.contact.core depends on this package and provides the contact
# content types and example contents (mydirectory, ...) needed to test it.
COLLECTIVE_CONTACT_WIDGET_INTEGRATION = IntegrationTesting(
    bases=(COLLECTIVE_CONTACT_CORE,), name="CollectiveContactWidget:Integration"
)

COLLECTIVE_CONTACT_WIDGET_FUNCTIONAL = FunctionalTesting(
    bases=(COLLECTIVE_CONTACT_CORE,), name="CollectiveContactWidget:Functional"
)

ACCEPTANCE = FunctionalTesting(
    bases=(COLLECTIVE_CONTACT_CORE, REMOTE_LIBRARY_BUNDLE_FIXTURE, WSGI_SERVER_FIXTURE),
    name="CollectiveContactWidget:Acceptance",
)
