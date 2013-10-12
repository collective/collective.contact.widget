from zope.interface import Interface, implements
from zope import schema
from zope.schema.interfaces import IField

from plone.formwidget.autocomplete.interfaces import IAutocompleteWidget
from z3c.relationfield.interfaces import IRelationChoice, IRelationList

from collective.contact.widget import _


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


class IContactSourceTypes(Interface):


    source_types = schema.Tuple(
       title=_(u"Contact types"),
       description=_(u"Contact content types that should be provided by autocompletion"),
       default=('held_position', 'organization', 'person'),
       value_type=schema.Choice(vocabulary='collective.contact.vocabulary.sourcetypes'),
       )


class IContactChoice(IContactSourceTypes, IRelationChoice):
    """A one to one relation where a choice of target objects is available.
    """


class IContactList(IContactSourceTypes, IRelationList):
    """A one to many relation.
    """


class IContactWidgetSettings(Interface):
    """Contact widget settings
    """

    def add_contact_infos(widget):
        """Return a dict, each key, value will be set
        as attribute on the widget.
        """


class IContactTypeChoiceField(IContactSourceTypes, IField):
    """
    """


class ContactTypeChoiceField(object):
    implements(IContactTypeChoiceField)