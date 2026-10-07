from collective.contact.widget.converters import ContactChoiceSelectWidgetConverter
from collective.contact.widget.converters import ContactListSelectWidgetConverter
from collective.contact.widget.schema import ContactChoice
from collective.contact.widget.schema import ContactList
from collective.contact.widget.testing import COLLECTIVE_CONTACT_WIDGET_INTEGRATION
from plone.app.z3cform.interfaces import IPloneFormLayer
from z3c.form.interfaces import IDataConverter
from z3c.form.interfaces import IFieldWidget
from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.publisher.browser import TestRequest

import unittest


class TestConverters(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_WIDGET_INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        self.mydirectory = self.portal["mydirectory"]
        self.degaulle = self.mydirectory["degaulle"]
        self.armee = self.mydirectory["armeedeterre"]

    def get_widget(self, field):
        field.__name__ = "contacts"
        request = TestRequest()
        alsoProvides(request, IPloneFormLayer)
        widget = getMultiAdapter((field, request), IFieldWidget)
        widget.context = self.portal
        widget.name = "form.widgets.contacts"
        return widget

    def token(self, obj):
        return "/".join(obj.getPhysicalPath())

    def test_choice_converter_lookup(self):
        widget = self.get_widget(ContactChoice(source_types=("person",)))
        converter = getMultiAdapter((widget.field, widget), IDataConverter)
        self.assertIsInstance(converter, ContactChoiceSelectWidgetConverter)

    def test_list_converter_lookup(self):
        widget = self.get_widget(ContactList(source_types=("person",)))
        converter = getMultiAdapter((widget.field, widget), IDataConverter)
        self.assertIsInstance(converter, ContactListSelectWidgetConverter)

    def test_choice_to_field_value(self):
        widget = self.get_widget(ContactChoice(source_types=("person",)))
        converter = getMultiAdapter((widget.field, widget), IDataConverter)
        self.assertEqual(
            converter.toFieldValue([self.token(self.degaulle)]), self.degaulle)

    def test_choice_to_field_value_without_value(self):
        widget = self.get_widget(ContactChoice(source_types=("person",)))
        converter = getMultiAdapter((widget.field, widget), IDataConverter)
        self.assertIsNone(converter.toFieldValue([]))
        self.assertIsNone(converter.toFieldValue(["--NOVALUE--"]))

    def test_list_to_field_value(self):
        widget = self.get_widget(ContactList(source_types=("person", "organization")))
        converter = getMultiAdapter((widget.field, widget), IDataConverter)
        self.assertEqual(
            converter.toFieldValue([self.token(self.degaulle), self.token(self.armee)]),
            [self.degaulle, self.armee])

    def test_list_to_field_value_without_value(self):
        widget = self.get_widget(ContactList(source_types=("person",)))
        converter = getMultiAdapter((widget.field, widget), IDataConverter)
        self.assertEqual(converter.toFieldValue([]), [])
