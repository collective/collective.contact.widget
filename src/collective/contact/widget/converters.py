from collective.contact.widget.interfaces import IContactChoice
from collective.contact.widget.interfaces import IContactList
from z3c.form.converter import CollectionSequenceDataConverter
from z3c.form.converter import SequenceDataConverter
from z3c.form.interfaces import ISequenceWidget
from zope.component import adapter


@adapter(IContactChoice, ISequenceWidget)
class ContactChoiceSelectWidgetConverter(SequenceDataConverter):
    """Data converter of the contact widgets (radio buttons filled by the
    autocomplete), which have a sequence of tokens as value.

    plone.app.z3cform registers RelationChoiceSelectWidgetConverter for
    IRelationChoice (the base of IContactChoice), which expects the single
    token of a select2 widget and gives None for a sequence: nothing was
    saved. This one is more specific and, like the default converter of
    sequence widgets, uses the terms of the widget to find the value (and
    handles the "no value" token).
    """


@adapter(IContactList, ISequenceWidget)
class ContactListSelectWidgetConverter(CollectionSequenceDataConverter):
    """Data converter of the contact list widgets (checkboxes filled by the
    autocomplete), which have a sequence of tokens as value.

    plone.app.z3cform registers RelationListSelectWidgetDataConverter for
    IRelationList (the base of IContactList), which expects UIDs and gives
    an empty list for our path tokens: nothing was saved.
    """
