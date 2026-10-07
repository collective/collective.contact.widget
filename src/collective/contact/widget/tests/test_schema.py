from collective.contact.widget.interfaces import IContactChoice
from collective.contact.widget.interfaces import IContactList
from collective.contact.widget.schema import ContactChoice
from collective.contact.widget.schema import ContactList
from collective.contact.widget.source import ContactSourceBinder
from zope.schema._bootstrapinterfaces import RequiredMissing

import unittest


def criteria(binder):
    return {key: list(value)
            for key, value in binder.selectable_filter.criteria.items()}


class TestContactChoice(unittest.TestCase):

    def test_interface(self):
        self.assertTrue(IContactChoice.providedBy(ContactChoice()))

    def test_default_source(self):
        field = ContactChoice(source_types=("person",), review_state=("private",))
        self.assertIsInstance(field.vocabulary, ContactSourceBinder)
        self.assertEqual(criteria(field.vocabulary)["portal_type"], ["person"])
        self.assertEqual(criteria(field.vocabulary)["review_state"], ["private"])

    def test_default_source_types(self):
        field = ContactChoice()
        self.assertEqual(
            sorted(criteria(field.vocabulary)["portal_type"]),
            ["held_position", "organization", "person"])

    def test_options(self):
        field = ContactChoice(addlink=False, prefilter_vocabulary="voc",
                              source_types=("person",))
        self.assertFalse(field.addlink)
        self.assertEqual(field.prefilter_vocabulary, "voc")
        self.assertEqual(field.source_types, ("person",))
        self.assertTrue(ContactChoice().addlink)

    def test_update_source(self):
        field = ContactChoice(source_types=("person",))
        field._bound_source = object()
        field.source_types = ("organization",)
        field.update_source()
        self.assertFalse(hasattr(field, "_bound_source"))
        self.assertEqual(criteria(field.vocabulary)["portal_type"], ["organization"])


class TestContactList(unittest.TestCase):

    def test_interface(self):
        self.assertTrue(IContactList.providedBy(ContactList()))

    def test_value_type(self):
        field = ContactList(source_types=("person",))
        self.assertIsInstance(field.value_type, ContactChoice)
        self.assertEqual(field.value_type.source_types, ("person",))

    def test_given_value_type_is_kept(self):
        value_type = ContactChoice(source_types=("organization",))
        self.assertIs(ContactList(value_type=value_type).value_type, value_type)

    def test_required_empty_value(self):
        with self.assertRaises(RequiredMissing):
            ContactList(required=True).validate([])
        ContactList(required=False).validate([])

    def test_update_source(self):
        field = ContactList(source_types=("person",))
        field.value_type._bound_source = object()
        field.update_source()
        self.assertFalse(hasattr(field.value_type, "_bound_source"))
        self.assertEqual(criteria(field.value_type.vocabulary)["portal_type"], ["person"])
