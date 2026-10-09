from collective.contact.widget.interfaces import IContactChoice
from collective.contact.widget.interfaces import IContactList
from collective.contact.widget.schema import ContactChoice
from collective.contact.widget.schema import ContactList
from collective.contact.widget.source import ContactSourceBinder
from collective.contact.widget.testing import COLLECTIVE_CONTACT_WIDGET_INTEGRATION
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.schema._bootstrapinterfaces import RequiredMissing

import unittest


class TestContactChoice(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_WIDGET_INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_init(self):
        field = ContactChoice(title=u"Contact")
        self.assertTrue(IContactChoice.providedBy(field))
        self.assertEqual(field.slave_fields, ())
        self.assertTrue(field.addlink)
        self.assertIsNone(field.source_types)
        self.assertIsNone(field.review_state)
        self.assertIsNone(field.prefilter_vocabulary)
        self.assertIsNone(field.prefilter_default_value)
        # default source
        source = field.vocabulary
        self.assertIsInstance(source, ContactSourceBinder)
        self.assertEqual(source.selectable_filter.criteria["portal_type"],
                         ("held_position", "person", "organization"))
        # given parameters
        field = ContactChoice(title=u"Contact", source_types=("person",), review_state=("active",),
                              addlink=False, slave_fields=("a",), prefilter_default_value=len)
        self.assertEqual(field.source_types, ("person",))
        self.assertEqual(field.review_state, ("active",))
        self.assertFalse(field.addlink)
        self.assertEqual(field.slave_fields, ("a",))
        self.assertEqual(field.prefilter_default_value, len)
        self.assertEqual(field.vocabulary.selectable_filter.criteria["portal_type"], ("person",))
        # a given source is kept
        binder = ContactSourceBinder(portal_type=("organization",))
        self.assertIs(ContactChoice(title=u"Contact", source=binder).vocabulary, binder)

    def test_update_source(self):
        field = ContactChoice(title=u"Contact")
        field._bound_source = object()
        field.source_types = ("organization",)
        field.update_source()
        self.assertEqual(field.vocabulary.selectable_filter.criteria["portal_type"], ("organization",))
        self.assertFalse(hasattr(field, "_bound_source"))
        field.source_types = None
        field.update_source()
        self.assertEqual(field.vocabulary.selectable_filter.criteria["portal_type"],
                         ("held_position", "person", "organization"))


class TestContactList(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_WIDGET_INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_init(self):
        field = ContactList(title=u"Contacts")
        self.assertTrue(IContactList.providedBy(field))
        self.assertTrue(field.addlink)
        self.assertIsNone(field.source_types)
        self.assertIsNone(field.review_state)
        self.assertIsNone(field.prefilter_vocabulary)
        self.assertIsNone(field.prefilter_default_value)
        # default value type
        self.assertIsInstance(field.value_type, ContactChoice)
        # given parameters are passed to the default value type
        field = ContactList(title=u"Contacts", source_types=("person",), review_state=("active",),
                            addlink=False)
        self.assertEqual(field.source_types, ("person",))
        self.assertEqual(field.review_state, ("active",))
        self.assertFalse(field.addlink)
        self.assertEqual(field.value_type.source_types, ("person",))
        self.assertEqual(field.value_type.review_state, ("active",))
        # a given value type is kept
        value_type = ContactChoice(title=u"Contact")
        self.assertIs(ContactList(title=u"Contacts", value_type=value_type).value_type, value_type)

    def test_update_source(self):
        field = ContactList(title=u"Contacts")
        field.value_type._bound_source = object()
        field.source_types = ("person",)
        field.update_source()
        self.assertEqual(field.value_type.vocabulary.selectable_filter.criteria["portal_type"], ("person",))
        self.assertFalse(hasattr(field.value_type, "_bound_source"))
        field.source_types = None
        field.update_source()
        self.assertEqual(field.value_type.vocabulary.selectable_filter.criteria["portal_type"],
                         ("held_position", "person", "organization"))

    def test_validate(self):
        field = ContactList(title=u"Contacts", required=True)
        field.bind(self.portal)
        with self.assertRaises(RequiredMissing):
            field.validate([])
        with self.assertRaises(RequiredMissing):
            field.validate(None)
        optional = ContactList(title=u"Contacts", required=False)
        optional.validate([])
