from collective.contact.widget.interfaces import IContactAutocompleteMultiSelectionWidget
from collective.contact.widget.interfaces import IContactAutocompleteSelectionWidget
from collective.contact.widget.interfaces import IContactAutocompleteWidget
from collective.contact.widget.schema import ContactChoice
from collective.contact.widget.schema import ContactList
from collective.contact.widget.testing import COLLECTIVE_CONTACT_WIDGET_INTEGRATION
from collective.contact.widget.widgets import AutocompleteSearch
from collective.contact.widget.widgets import ContactAutocompleteFieldWidget
from collective.contact.widget.widgets import ContactAutocompleteMultiFieldWidget
from collective.contact.widget.widgets import ContactAutocompleteMultiSelectionWidget
from collective.contact.widget.widgets import ContactAutocompleteSelectionWidget
from collective.contact.widget.widgets import LivesearchSearch
from collective.contact.widget.widgets import TermViewlet
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.z3cform.interfaces import IPloneFormLayer
from z3c.form import field
from z3c.form import form
from z3c.form.interfaces import DISPLAY_MODE
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.interfaces import IFieldWidget
from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.interface import directlyProvides
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import html
import json
import unittest


class WidgetTestCase(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_WIDGET_INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        alsoProvides(self.request, IPloneFormLayer)
        # the search views check the access to the view of the form
        self.request.URL = self.portal.absolute_url() + "/@@search"
        self.directory = self.portal["mydirectory"]
        self.degaulle = self.directory["degaulle"]
        self.token_degaulle = "/".join(self.degaulle.getPhysicalPath())

    def get_widget(self, contact_field=None):
        """Get the widget of a field in a form, like the browser does."""
        if contact_field is None:
            contact_field = ContactChoice(__name__="contact", title="Contact")
        test_form = form.Form(self.portal, self.request)
        test_form.fields = field.Fields(contact_field)
        test_form.ignoreContext = True
        test_form.update()
        return test_form.widgets[contact_field.__name__]


class TestTermViewlet(WidgetTestCase):

    def setUp(self):
        super(TestTermViewlet, self).setUp()
        self.viewlet = TermViewlet(self.degaulle, self.request, None, None)

    def test_token(self):
        self.assertEqual(self.viewlet.token, self.token_degaulle)

    def test_title(self):
        self.assertEqual(self.viewlet.title, html.escape(self.degaulle.get_full_title()))
        # the title of a content without full title is escaped
        self.directory.title = "Contacts & <others>"
        self.assertEqual(TermViewlet(self.directory, self.request, None, None).title, "Contacts &amp; &lt;others&gt;")

    def test_portal_type(self):
        self.assertEqual(self.viewlet.portal_type, "person")

    def test_url(self):
        self.assertEqual(self.viewlet.url, self.degaulle.absolute_url())

    def test_render(self):
        self.assertEqual(
            self.viewlet.render(),
            '<input type="hidden" name="objpath" value="%s|%s|person|%s" />'
            % (self.token_degaulle, html.escape(self.degaulle.get_full_title()), self.degaulle.absolute_url()),
        )


class TestContactBaseWidget(WidgetTestCase):

    def setUp(self):
        super(TestContactBaseWidget, self).setUp()
        self.widget = self.get_widget()

    def test_livesearch_url(self):
        self.assertEqual(
            self.widget.livesearch_url(),
            "%s/++widget++%s/@@livesearch-search" % (self.request.getURL(), self.widget.name),
        )

    def test_addnew_modal_options(self):
        options = json.loads(self.widget.addnew_modal_options())
        self.assertEqual(options["actionOptions"]["onSuccess"], "ccwAddNewSuccess")
        self.assertFalse(options["actionOptions"]["displayInModal"])
        self.assertFalse(options["actionOptions"]["reloadWindowOnClose"])
        self.widget.livesearch = False
        self.assertIsNone(self.widget.addnew_modal_options())

    def test_livesearch_options(self):
        options = json.loads(self.widget.livesearch_options())
        self.assertEqual(options["ajaxUrl"], self.widget.livesearch_url())
        self.assertEqual(options["minimumInputLength"], 3)
        self.assertEqual(options["perPage"], self.widget.maxResults)
        self.assertIn("<%- token %>", options["itemTemplate"])
        self.widget.livesearch = False
        self.assertIsNone(self.widget.livesearch_options())

    def test_bound_source(self):
        self.assertEqual(self.widget.bound_source.portal_url, self.portal.absolute_url())

    def test_tokenToUrl(self):
        self.assertEqual(self.widget.tokenToUrl(self.token_degaulle), self.degaulle.absolute_url())
        self.assertEqual(self.widget.tokenToUrl("--NOVALUE--"), "")

    def test_render(self):
        self.assertIsInstance(self.widget, ContactAutocompleteSelectionWidget)
        self.assertTrue(IContactAutocompleteWidget.providedBy(self.widget))
        self.assertTrue(self.widget.livesearch)
        # input mode
        rendered = self.widget.render()
        self.assertIn(self.widget.livesearch_url(), rendered)
        self.assertIn("pat-livesearch", rendered)
        # display mode
        self.widget.mode = DISPLAY_MODE
        self.assertNotIn("pat-livesearch", self.widget.render())
        # hidden mode
        self.widget.mode = HIDDEN_MODE
        self.assertNotIn("pat-livesearch", self.widget.render())

    def test_js_extra(self):
        self.widget.render()
        # the default action opens the form to add a contact
        self.widget.actions = [{"klass": "other", "formselector": "#other"}]
        self.assertIn(".find('.other')", self.widget.js_extra())
        self.assertNotIn(".find('.addnew')", self.widget.js_extra())
        self.widget.actions = [{"klass": "addnew"}]
        self.assertIn(".find('.addnew')", self.widget.js_extra())

    def test_prefilter_terms(self):
        # no prefilter
        self.assertEqual(self.widget.prefilter_terms(), [])
        # name of a vocabulary
        self.widget.field.prefilter_vocabulary = "collective.contact.vocabulary.sourcetypes"
        self.assertEqual(
            [t.token for t in self.widget.prefilter_terms()], ["held_position", "organization", "person", "position"]
        )
        # vocabulary
        vocabulary = SimpleVocabulary([SimpleTerm(value="", title="No filter")])
        self.widget.field.prefilter_vocabulary = vocabulary
        self.assertIs(self.widget.prefilter_terms(), vocabulary)
        # source binder

        def binder(context):
            return vocabulary

        directlyProvides(binder, IContextSourceBinder)
        self.widget.field.prefilter_vocabulary = binder
        self.assertIs(self.widget.prefilter_terms(), vocabulary)

    def test_prefilter_default_value(self):
        self.assertIsNone(self.widget.prefilter_default_value())
        self.widget.field.prefilter_default_value = lambda context: '{"portal_type":"person"}'
        self.assertEqual(self.widget.prefilter_default_value(), '{"portal_type":"person"}')


class TestContactAutocompleteSelectionWidget(WidgetTestCase):

    def test_factory(self):
        contact_field = ContactChoice(__name__="contact", title="Contact")
        widget = ContactAutocompleteFieldWidget(contact_field, self.request)
        self.assertIsInstance(widget, ContactAutocompleteSelectionWidget)
        self.assertTrue(IFieldWidget.providedBy(widget))
        self.assertTrue(IContactAutocompleteSelectionWidget.providedBy(widget))
        self.assertIs(widget.field, contact_field)
        # registered adapter
        widget = getMultiAdapter((contact_field, self.request), IFieldWidget)
        self.assertIsInstance(widget, ContactAutocompleteSelectionWidget)


class TestContactAutocompleteMultiSelectionWidget(WidgetTestCase):

    def test_factory(self):
        contact_field = ContactList(__name__="contacts", title="Contacts")
        widget = ContactAutocompleteMultiFieldWidget(contact_field, self.request)
        self.assertIsInstance(widget, ContactAutocompleteMultiSelectionWidget)
        self.assertTrue(IFieldWidget.providedBy(widget))
        self.assertTrue(IContactAutocompleteMultiSelectionWidget.providedBy(widget))
        self.assertIs(widget.field, contact_field)
        widget = getMultiAdapter((contact_field, self.request), IFieldWidget)
        self.assertIsInstance(widget, ContactAutocompleteMultiSelectionWidget)


class TestAutocompleteSearch(WidgetTestCase):

    def setUp(self):
        super(TestAutocompleteSearch, self).setUp()
        self.widget = self.get_widget()
        self.search = AutocompleteSearch(self.widget, self.request)

    def test_get_query(self):
        self.assertIsNone(self.search.get_query())
        self.request.form["q"] = "gaulle"
        self.assertEqual(self.search.get_query(), "gaulle")

    def test_get_terms(self):
        # no query
        self.assertEqual(self.search.get_terms(), ())
        # query
        self.request.form["q"] = "gaulle"
        self.assertIn(self.token_degaulle, [t.token for t in self.search.get_terms()])
        # terms are sorted by title
        self.request.form["q"] = "a"
        titles = [t.title for t in self.search.get_terms()]
        self.assertEqual(titles, sorted(titles))
        # path without query
        self.request.form.pop("q")
        self.request.form["path"] = "/".join(self.directory.getPhysicalPath())
        terms = self.search.get_terms()
        self.assertIn(self.token_degaulle, [t.token for t in terms])
        # prefilter
        self.request.form["prefilter"] = '{"portal_type": "organization"}'
        terms = self.search.get_terms()
        self.assertTrue(terms)
        self.assertEqual(set(t.portal_type for t in terms), {"organization"})
        # an invalid prefilter is ignored
        self.request.form["prefilter"] = "invalid"
        self.assertIn(self.token_degaulle, [t.token for t in self.search.get_terms()])
        # a prefilter keeps the matching contacts
        self.request.form["prefilter"] = '{"portal_type": "person"}'
        terms = self.search.get_terms()
        self.assertIn(self.token_degaulle, [t.token for t in terms])
        self.assertEqual(set(t.portal_type for t in terms), {"person"})
        # an empty prefilter ("No filter" term) and a json value that isn't an object are ignored
        for prefilter in ("", '["person"]'):
            self.request.form["prefilter"] = prefilter
            self.assertIn("organization", set(t.portal_type for t in self.search.get_terms()))

    def test_call(self):
        self.request.form["q"] = "gaulle"
        result = self.search()
        self.assertTrue(self.request.response.getHeader("Content-type").startswith("text/plain"))
        lines = [line.split("|") for line in result.splitlines()]
        line = [x for x in lines if x[0] == self.token_degaulle][0]
        self.assertEqual(line[2:], ["person", self.degaulle.absolute_url(), ""])
        # nothing found
        self.request.form["q"] = "doesnotexist"
        self.assertEqual(self.search(), "")


class TestLivesearchSearch(WidgetTestCase):

    def setUp(self):
        super(TestLivesearchSearch, self).setUp()
        self.widget = self.get_widget()
        self.search = LivesearchSearch(self.widget, self.request)

    def test_get_query(self):
        self.assertIsNone(self.search.get_query())
        # the query of the livesearch form
        self.request.form["%s.widgets.query" % self.widget.name] = "gaulle"
        self.assertEqual(self.search.get_query(), "gaulle")
        self.request.form["q"] = "pepper"
        self.assertEqual(self.search.get_query(), "pepper")

    def test_call(self):
        self.request.form["q"] = "gaulle"
        result = json.loads(self.search())
        self.assertEqual(self.request.response.getHeader("Content-type"), "application/json")
        self.assertEqual(result["total"], len(result["items"]))
        item = [i for i in result["items"] if i["token"] == self.token_degaulle][0]
        self.assertEqual(item["contact_url"], self.degaulle.absolute_url())
        self.assertEqual(item["url"], "#livesearch-select")
        self.assertTrue(item["error"])
        self.assertEqual(item["icon"], "%s/@@iconresolver/contenttype/person" % self.portal.absolute_url())
        self.assertTrue(item["title"])
        # results are limited
        self.widget.maxResults = 1
        self.request.form["q"] = "a"
        self.assertEqual(json.loads(self.search())["total"], 1)
