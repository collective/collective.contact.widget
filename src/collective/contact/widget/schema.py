from zope.interface import implements
from z3c.relationfield.schema import RelationChoice, RelationList

from .interfaces import IContactChoice, IContactList
from .source import ContactSourceBinder


class ContactList(RelationList):
    implements(IContactList)
    source_types = None

    def __init__(self, *args, **kwargs):
        self.addlink = kwargs.pop('addlink', True)
        self.source_types = kwargs.pop('source_types',
                                    self.source_types or None)
        if not 'value_type' in kwargs:
            kwargs['value_type'] = ContactChoice(source_types=self.source_types)

        super(ContactList, self).__init__(*args, **kwargs)

    def update_source(self):
        self.value_type.vocabulary = ContactSourceBinder(
            portal_type=self.source_types or ('held_position', 'person', 'organization'))
        if hasattr(self.value_type, '_bound_source'):
            del self.value_type._bound_source


class ContactChoice(RelationChoice):
    implements(IContactChoice)
    source_types = None

    def __init__(self, *args, **kwargs):
        self.addlink = kwargs.pop('addlink', True)
        self.source_types = kwargs.pop('source_types',
                                    self.source_types or None)
        if not ('values' in kwargs or 'vocabulary' in kwargs or 'source' in kwargs):
            kwargs['source'] = ContactSourceBinder(portal_type=self.source_types
                                    or ('held_position', 'person', 'organization'))

        super(ContactChoice, self).__init__(*args, **kwargs)

    def update_source(self):
        self.vocabulary = ContactSourceBinder(
            portal_type=self.source_types or ('held_position', 'person', 'organization'))
        if hasattr(self, '_bound_source'):
            del self._bound_source
