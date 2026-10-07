from collective.contact.core.testing import COLLECTIVE_CONTACT_CORE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting

# collective.contact.core depends on this package and provides the contact
# content types and example contents (mydirectory, ...) needed to test it.
COLLECTIVE_CONTACT_WIDGET_INTEGRATION = IntegrationTesting(
    bases=(COLLECTIVE_CONTACT_CORE,),
    name="CollectiveContactWidget:Integration")

COLLECTIVE_CONTACT_WIDGET_FUNCTIONAL = FunctionalTesting(
    bases=(COLLECTIVE_CONTACT_CORE,),
    name="CollectiveContactWidget:Functional")
