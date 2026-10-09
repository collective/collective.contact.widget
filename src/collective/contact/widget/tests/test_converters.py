from collective.contact.widget.converters import ContactChoiceSelectWidgetConverter
from collective.contact.widget.converters import ContactListSelectWidgetConverter
from collective.contact.widget.schema import ContactChoice
from collective.contact.widget.schema import ContactList
from collective.contact.widget.testing import COLLECTIVE_CONTACT_WIDGET_INTEGRATION
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.z3cform.interfaces import IPloneFormLayer
from z3c.form.interfaces import IDataConverter
from z3c.form.interfaces import IFieldWidget
from zope.component import getMultiAdapter
from zope.interface import alsoProvides

import unittest


class ConverterTestCase(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_WIDGET_INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        alsoProvides(self.request, IPloneFormLayer)
        directory = self.portal["mydirectory"]
        self.degaulle = directory["degaulle"]
        self.pepper = directory["pepper"]
        self.token_degaulle = "/".join(self.degaulle.getPhysicalPath())
        self.token_pepper = "/".join(self.pepper.getPhysicalPath())

    def get_widget(self, field, tokens):
        """Widget whose terms are those of the selected contacts, like in a form."""
        field.__name__ = "contact"
        widget = getMultiAdapter((field, self.request), IFieldWidget)
        widget.context = self.portal
        self.request.form[widget.name] = tokens
        widget.update()
        return widget


class TestContactChoiceSelectWidgetConverter(ConverterTestCase):

    def setUp(self):
        super(TestContactChoiceSelectWidgetConverter, self).setUp()
        self.widget = self.get_widget(ContactChoice(title="Contact", source_types=("person",)), [self.token_degaulle])
        self.converter = getMultiAdapter((self.widget.field, self.widget), IDataConverter)

    def test_converter(self):
        # the converter of the contact widgets is used, not the one of the relations
        self.assertIsInstance(self.converter, ContactChoiceSelectWidgetConverter)
        # the value of the widget is a sequence of tokens
        self.assertEqual(self.converter.toWidgetValue(self.degaulle), [self.token_degaulle])
        self.assertEqual(self.converter.toWidgetValue(None), [])
        self.assertEqual(self.converter.toFieldValue([self.token_degaulle]), self.degaulle)
        # no value
        self.assertIsNone(self.converter.toFieldValue([]))
        self.assertIsNone(self.converter.toFieldValue(["--NOVALUE--"]))


class TestContactListSelectWidgetConverter(ConverterTestCase):

    def setUp(self):
        super(TestContactListSelectWidgetConverter, self).setUp()
        self.widget = self.get_widget(
            ContactList(title="Contacts", source_types=("person",)), [self.token_degaulle, self.token_pepper]
        )
        self.converter = getMultiAdapter((self.widget.field, self.widget), IDataConverter)

    def test_converter(self):
        self.assertIsInstance(self.converter, ContactListSelectWidgetConverter)
        self.assertEqual(
            self.converter.toWidgetValue([self.degaulle, self.pepper]), [self.token_degaulle, self.token_pepper]
        )
        self.assertEqual(self.converter.toWidgetValue([]), [])
        self.assertEqual(
            self.converter.toFieldValue([self.token_degaulle, self.token_pepper]), [self.degaulle, self.pepper]
        )
        self.assertEqual(self.converter.toFieldValue([]), [])
