from collective.contact.widget.factory import ContactChoiceField
from collective.contact.widget.factory import ContactChoiceHandler
from collective.contact.widget.factory import ContactHandler
from collective.contact.widget.factory import ContactListChoiceField
from collective.contact.widget.factory import ContactTypesVocabulary
from collective.contact.widget.factory import getContactChoiceFieldSchema
from collective.contact.widget.factory import getContactListChoiceFieldSchema
from collective.contact.widget.interfaces import IContactChoiceField
from collective.contact.widget.schema import ContactChoice
from collective.contact.widget.schema import ContactList
from collective.contact.widget.testing import COLLECTIVE_CONTACT_WIDGET_INTEGRATION
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.schemaeditor.interfaces import IFieldEditFormSchema
from plone.supermodel import loadString
from plone.supermodel.exportimport import BaseHandler
from zope.component import getAdapter
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

import unittest


MODEL = """\
<model xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema>
    <field name="contact" type="collective.contact.widget.schema.ContactChoice">
      <title>Contact</title>
      <source_types>
        <element>organization</element>
      </source_types>
    </field>
    <field name="contacts" type="collective.contact.widget.schema.ContactList">
      <title>Contacts</title>
      <source_types>
        <element>person</element>
      </source_types>
    </field>
  </schema>
</model>
"""


class TestContactHandler(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_WIDGET_INTEGRATION

    def test_read(self):
        self.assertIsInstance(ContactChoiceHandler, ContactHandler)
        self.assertIsInstance(ContactChoiceHandler, BaseHandler)
        # the vocabulary is not exported, it is built from the source types
        for attr in ("vocabulary", "values", "source"):
            self.assertEqual(ContactHandler.filteredAttributes[attr], "w")
        # the source is updated with the read source types
        schema = loadString(MODEL).schema
        contact = schema["contact"]
        self.assertIsInstance(contact, ContactChoice)
        self.assertEqual(contact.source_types, ("organization",))
        self.assertEqual(contact.vocabulary.selectable_filter.criteria["portal_type"], ("organization",))
        contacts = schema["contacts"]
        self.assertIsInstance(contacts, ContactList)
        self.assertEqual(contacts.source_types, ("person",))
        self.assertEqual(contacts.value_type.vocabulary.selectable_filter.criteria["portal_type"], ("person",))


class TestContactChoiceField(unittest.TestCase):

    def test_init(self):
        field = ContactChoice(title="Contact")
        wrapper = ContactChoiceField(field)
        self.assertTrue(IContactChoiceField.providedBy(wrapper))
        self.assertIs(wrapper.field, field)


class TestContactListChoiceField(unittest.TestCase):

    def test_init(self):
        field = ContactList(title="Contacts")
        wrapper = ContactListChoiceField(field)
        self.assertTrue(IContactChoiceField.providedBy(wrapper))
        self.assertIs(wrapper.field, field)


class TestFieldSchemas(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_WIDGET_INTEGRATION

    def test_getContactChoiceFieldSchema(self):
        field = ContactChoice(title="Contact")
        self.assertEqual(getContactChoiceFieldSchema(field), IContactChoiceField)
        # registered adapter
        self.assertEqual(getAdapter(field, IFieldEditFormSchema), IContactChoiceField)

    def test_getContactListChoiceFieldSchema(self):
        field = ContactList(title="Contacts")
        self.assertEqual(getContactListChoiceFieldSchema(field), IContactChoiceField)
        self.assertEqual(getAdapter(field, IFieldEditFormSchema), IContactChoiceField)


class TestContactTypesVocabulary(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_WIDGET_INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_call(self):
        factory = getUtility(IVocabularyFactory, name="collective.contact.vocabulary.sourcetypes")
        self.assertIsInstance(factory, ContactTypesVocabulary)
        vocabulary = factory(self.portal)
        self.assertEqual([t.token for t in vocabulary], ["held_position", "organization", "person", "position"])
        self.assertEqual([t.value for t in vocabulary], ["held_position", "organization", "person", "position"])
        self.assertTrue(all(t.title for t in vocabulary))
