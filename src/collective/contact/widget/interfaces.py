from zope.interface import Interface
from z3c.relationfield.interfaces import IRelationChoice, IRelationList
from plone.formwidget.autocomplete.interfaces import IAutocompleteWidget


class IContactContent(Interface):
    """Base class for collective.contact.core content types"""


class IContactAutocompleteWidget(IAutocompleteWidget):
    """Marker interface for the contact autocomplete widget
    """


class IContactAutocompleteSelectionWidget(IContactAutocompleteWidget):
    """Marker interface for the multi selection contact autocomplete widget
    """


class IContactAutocompleteMultiSelectionWidget(IContactAutocompleteWidget):
    """Marker interface for the selection contact autocomplete widget
    """


class IContactChoice(IRelationChoice):
    """A one to one relation where a choice of target objects is available.
    """


class IContactList(IRelationList):
    """A one to many relation.
    """

class IContactWidgetSettings(Interface):
    """Contact widget settings
    """
    def add_contact_infos(widget):
        """Return a dict, each key, value will be set
        as attribute on the widget.
        """
