from AccessControl import Unauthorized
from Acquisition.interfaces import IAcquirer
from collective.contact.widget.interfaces import IContactAutocompleteMultiSelectionWidget
from collective.contact.widget.interfaces import IContactAutocompleteSelectionWidget
from collective.contact.widget.interfaces import IContactAutocompleteWidget
from collective.contact.widget.schema import ContactChoice
from collective.contact.widget.schema import ContactList
from collective.contact.widget.source import ContactSource
from collective.contact.widget.source import ContactSourceBinder
from collective.contact.widget.testing import COLLECTIVE_CONTACT_WIDGET_INTEGRATION
from collective.contact.widget.widgets import AutocompleteSearch
from collective.contact.widget.widgets import ContactAutocompleteFieldWidget
from collective.contact.widget.widgets import ContactAutocompleteMultiFieldWidget
from collective.contact.widget.widgets import ContactAutocompleteMultiSelectionWidget
from collective.contact.widget.widgets import ContactAutocompleteSelectionWidget
from collective.contact.widget.widgets import LivesearchSearch
from collective.contact.widget.widgets import MasterSelect
from collective.contact.widget.widgets import TermViewlet
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.z3cform.interfaces import IPloneFormLayer
from z3c.form import field
from z3c.form import form
from z3c.form.interfaces import DISPLAY_MODE
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.interfaces import IFieldWidget
from z3c.form.interfaces import INPUT_MODE
from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.interface import directlyProvides
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import html
import json
import unittest


class UnsortedContactSource(ContactSource):
    """Results in the order of the catalog (do_post_sort)."""

    do_post_sort = False


class UnsortedContactSourceBinder(ContactSourceBinder):
    path_source = UnsortedContactSource


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
        self.directory_path = "/".join(self.directory.getPhysicalPath())
        self.pepper = self.directory["pepper"]
        self.token_pepper = "/".join(self.pepper.getPhysicalPath())

    def get_widget(self, contact_field=None, tokens=None, mode=INPUT_MODE):
        """Get the widget of a field in a form, like the browser does,
        with the contacts of the tokens selected."""
        if contact_field is None:
            contact_field = ContactChoice(__name__="contact", title="Contact")
        if tokens is not None:
            # a submitted form: Plone ignores the values of a GET request
            self.request["REQUEST_METHOD"] = "POST"
            self.request.form["form.widgets.%s" % contact_field.__name__] = tokens
        test_form = form.Form(self.portal, self.request)
        test_form.fields = field.Fields(contact_field)
        test_form.ignoreContext = True
        test_form.mode = mode
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

    def test_security(self):
        # public object for the ++widget++<name>/@@livesearch-search traversal, not an IAcquirer
        self.assertIsNone(self.widget.__roles__)
        self.assertFalse(IAcquirer.providedBy(self.widget))

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
        contacts = ContactList(__name__="contacts", title="Contacts")
        url_degaulle = self.degaulle.absolute_url()
        url_pepper = self.pepper.absolute_url()
        # input mode: the selected contacts are checked, with a link to them
        rendered = self.get_widget(contacts, [self.token_degaulle, self.token_pepper]).render()
        self.assertEqual(rendered.count('type="checkbox"'), 2)
        self.assertEqual(rendered.count('checked="checked"'), 2)
        self.assertIn('<a class="link-tooltip" target="_new" href="%s"' % url_degaulle, rendered)
        self.assertIn(">Général Charles De Gaulle</a>", rendered)
        rendered = self.get_widget(tokens=[self.token_degaulle]).render()
        self.assertIn('type="radio"', rendered)
        self.assertIn('<a class="link-tooltip" target="_new" href="%s"' % url_degaulle, rendered)
        # display mode: links to the selected contacts
        rendered = self.get_widget(tokens=[self.token_degaulle], mode=DISPLAY_MODE).render()
        self.assertTrue(rendered.startswith('<span id="form-widgets-contact"'))
        self.assertIn('<a class="link-tooltip" target="_new" href="%s"' % url_degaulle, rendered)
        self.assertIn(">Général Charles De Gaulle</a>", rendered)
        rendered = self.get_widget(contacts, [self.token_degaulle, self.token_pepper], DISPLAY_MODE).render()
        self.assertTrue(rendered.startswith('<ul id="form-widgets-contacts"'))
        self.assertEqual(rendered.count("<li>"), 2)
        self.assertIn('href="%s"' % url_degaulle, rendered)
        self.assertIn('href="%s"' % url_pepper, rendered)
        # missing contacts are hidden
        missing = "#error-missing-/mydirectory/unknown"
        rendered = self.get_widget(contacts, [self.token_degaulle, missing], DISPLAY_MODE).render()
        self.assertIn('href="%s"' % url_degaulle, rendered)
        self.assertNotIn("unknown", rendered)
        self.assertNotIn("unknown", self.get_widget(tokens=[missing], mode=DISPLAY_MODE).render())
        # hidden mode: the selected contacts
        rendered = self.get_widget(contacts, [self.token_degaulle, self.token_pepper], HIDDEN_MODE).render()
        self.assertEqual(rendered.count('type="hidden"'), 2)
        self.assertIn('value="%s"' % self.token_degaulle, rendered)
        self.assertIn('value="%s"' % self.token_pepper, rendered)
        # rtf mode: the titles, separated by commas
        widget = self.get_widget(contacts, [self.token_degaulle, self.token_pepper])
        widget.mode = "rtf"
        self.assertEqual(" ".join(widget.render().split()), "Général Charles De Gaulle , Mister Pepper")

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


class TestMasterSelect(WidgetTestCase):

    def test_getSlaves(self):
        slave = {"name": "position", "action": "hide", "hide_values": ("",)}
        widget = self.get_widget(ContactChoice(__name__="contact", title="Contact", slave_fields=(slave,)))
        self.assertIsInstance(widget, MasterSelect)
        # copies of the slave fields of the field
        slaves = list(widget.getSlaves())
        self.assertEqual(slaves, [slave])
        self.assertIsNot(slaves[0], slave)


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
        self.assertTrue(len(titles) > 2)
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
        # no prefilter parameter (jQuery autocomplete setOptions replaces the extraParams)
        del self.request.form["prefilter"]
        self.assertIn("organization", set(t.portal_type for t in self.search.get_terms()))
        # restriction on the relations of an object
        self.request.form.pop("path")
        self.request.form["q"] = "gaulle"
        self.request.form["relations"] = {"position": "/mydirectory/armeedeterre/general_adt"}
        self.assertEqual([t.token for t in self.search.get_terms()], ["%s/gadt" % self.token_degaulle])
        del self.request.form["relations"]
        # the source can keep the order of its results
        widget = self.get_widget(
            ContactChoice(
                __name__="unsorted", title="Contact", source=UnsortedContactSourceBinder(portal_type=("person",))
            )
        )
        self.request.form.pop("q")
        self.request.form["path"] = self.directory_path
        tokens = [t.token for t in AutocompleteSearch(widget, self.request).get_terms()]
        # catalog order, not sorted by title
        self.assertEqual(tokens, ["%s/%s" % (self.directory_path, i) for i in ("degaulle", "pepper", "rambo", "draper")])
        # the user must be allowed to open the form of the widget
        setRoles(self.portal, TEST_USER_ID, ["Member"])
        self.request.URL = self.portal.absolute_url() + "/@@overview-controlpanel"
        with self.assertRaises(Unauthorized):
            self.search.get_terms()

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
