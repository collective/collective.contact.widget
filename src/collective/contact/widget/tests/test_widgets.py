from collective.contact.widget.interfaces import (
    IContactAutocompleteMultiSelectionWidget,
)
from collective.contact.widget.interfaces import IContactAutocompleteSelectionWidget
from collective.contact.widget.schema import ContactChoice
from collective.contact.widget.schema import ContactList
from collective.contact.widget.testing import COLLECTIVE_CONTACT_WIDGET_INTEGRATION
from collective.contact.widget.widgets import LivesearchSearch
from collective.contact.widget.widgets import TermViewlet
from plone.app.z3cform.interfaces import IPloneFormLayer
from z3c.form.interfaces import IFieldWidget
from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.publisher.browser import TestRequest

import json
import unittest


class TestWidgets(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_WIDGET_INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        self.mydirectory = self.portal["mydirectory"]
        self.degaulle = self.mydirectory["degaulle"]

    def get_widget(self, field, **form):
        field.__name__ = "contacts"
        request = TestRequest(form=form)
        alsoProvides(request, IPloneFormLayer)
        widget = getMultiAdapter((field, request), IFieldWidget)
        widget.context = self.portal
        widget.name = "form.widgets.contacts"
        return widget

    def test_widget_of_choice(self):
        widget = self.get_widget(ContactChoice())
        self.assertTrue(IContactAutocompleteSelectionWidget.providedBy(widget))
        self.assertTrue(widget.livesearch)

    def test_widget_of_list(self):
        widget = self.get_widget(ContactList())
        self.assertTrue(IContactAutocompleteMultiSelectionWidget.providedBy(widget))
        self.assertTrue(widget.livesearch)

    def test_livesearch_options(self):
        widget = self.get_widget(ContactChoice())
        options = json.loads(widget.livesearch_options())
        self.assertEqual(options["minimumInputLength"], widget.livesearch_min_chars)
        self.assertEqual(options["perPage"], widget.maxResults)
        self.assertTrue(options["ajaxUrl"].endswith(
            "/++widget++form.widgets.contacts/@@livesearch-search"))

    def test_no_livesearch_options_without_livesearch(self):
        widget = self.get_widget(ContactChoice())
        widget.livesearch = False
        self.assertIsNone(widget.livesearch_options())
        self.assertIsNone(widget.addnew_modal_options())

    def test_addnew_modal_options(self):
        options = json.loads(self.get_widget(ContactChoice()).addnew_modal_options())
        self.assertEqual(options["actionOptions"]["onSuccess"], "ccwAddNewSuccess")
        self.assertFalse(options["actionOptions"]["reloadWindowOnClose"])

    def test_token_to_url(self):
        widget = self.get_widget(ContactChoice())
        token = "/".join(self.degaulle.getPhysicalPath())
        self.assertEqual(widget.tokenToUrl(token), self.degaulle.absolute_url())
        self.assertEqual(widget.tokenToUrl("--NOVALUE--"), "")

    def test_prefilter_default_value(self):
        widget = self.get_widget(ContactChoice(prefilter_default_value=lambda context: u"foo"))
        self.assertEqual(widget.prefilter_default_value(), u"foo")
        self.assertIsNone(self.get_widget(ContactChoice()).prefilter_default_value())

    def test_prefilter_terms(self):
        self.assertEqual(self.get_widget(ContactChoice()).prefilter_terms(), [])
        widget = self.get_widget(ContactChoice(prefilter_vocabulary="plone.app.vocabularies.WorkflowStates"))
        self.assertTrue(len(widget.prefilter_terms()))


class TestLivesearch(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_WIDGET_INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        self.degaulle = self.portal["mydirectory"]["degaulle"]

    def search(self, **form):
        field = ContactList(source_types=("person",))
        field.__name__ = "contacts"
        request = TestRequest(form=form)
        alsoProvides(request, IPloneFormLayer)
        widget = getMultiAdapter((field, request), IFieldWidget)
        widget.context = self.portal
        widget.name = "form.widgets.contacts"
        view = LivesearchSearch(widget, request)
        view.validate_access = lambda: None
        return json.loads(view())

    def test_query_of_the_livesearch_form(self):
        result = self.search(**{"form.widgets.contacts.widgets.query": "gaulle"})
        tokens = [item["token"] for item in result["items"]]
        self.assertEqual(tokens, ["/".join(self.degaulle.getPhysicalPath())])
        self.assertEqual(result["total"], 1)
        item = result["items"][0]
        self.assertEqual(item["contact_url"], self.degaulle.absolute_url())
        self.assertTrue(item["icon"].endswith("/@@iconresolver/contenttype/person"))

    def test_query_param(self):
        result = self.search(q="gaulle")
        self.assertEqual(result["total"], 1)

    def test_empty_query_gives_nothing(self):
        self.assertEqual(self.search(), {"items": [], "total": 0})


class TestTermViewlet(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_WIDGET_INTEGRATION

    def test_render(self):
        degaulle = self.layer["portal"]["mydirectory"]["degaulle"]
        viewlet = TermViewlet(degaulle, degaulle.REQUEST, None, None)
        self.assertEqual(viewlet.portal_type, "person")
        self.assertEqual(viewlet.url, degaulle.absolute_url())
        parts = viewlet.render().split('value="')[1].rstrip('" />').split("|")
        self.assertEqual(parts[0], "/".join(degaulle.getPhysicalPath()))
        self.assertEqual(parts[-2:], ["person", degaulle.absolute_url()])
