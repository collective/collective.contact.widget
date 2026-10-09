from collective.contact.widget.source import ContactSource
from collective.contact.widget.source import ContactSourceBinder
from collective.contact.widget.source import parse_query
from collective.contact.widget.source import Term
from collective.contact.widget.testing import COLLECTIVE_CONTACT_WIDGET_INTEGRATION
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.formwidget.contenttree.source import ObjPathSource
from z3c.relationfield.schema import RelationChoice

import unittest


class TestTerm(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_WIDGET_INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.degaulle = self.portal["mydirectory"]["degaulle"]
        self.brain = api.content.find(UID=self.degaulle.UID())[0]
        self.term = Term(self.degaulle, token=self.brain.getPath(), title="De Gaulle", brain=self.brain)

    def test_url(self):
        self.assertEqual(self.term.url, self.degaulle.absolute_url())

    def test_portal_type(self):
        self.assertEqual(self.term.portal_type, "person")

    def test_extra(self):
        self.assertEqual(self.term.extra, "")


class TestParseQuery(unittest.TestCase):

    def test_parse_query(self):
        self.assertEqual(parse_query("gaulle"), {"SearchableText": "gaulle*"})
        # words are combined and special characters removed
        self.assertEqual(parse_query("charles de-gaulle?"), {"SearchableText": "charles* AND de* AND gaulle*"})
        # an empty query does not filter on text
        self.assertEqual(parse_query(""), {})
        self.assertEqual(parse_query("?"), {})
        # the path is prefixed and kept without depth
        self.assertEqual(
            parse_query("path:/mydirectory gaulle", "/plone"),
            {"SearchableText": "gaulle*", "path": {"query": "/plone/mydirectory"}},
        )
        self.assertEqual(parse_query("path:/mydirectory"), {"path": {"query": "/mydirectory"}})


class TestContactSource(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_WIDGET_INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.directory = self.portal["mydirectory"]
        self.degaulle = self.directory["degaulle"]
        self.armeedeterre = self.directory["armeedeterre"]
        self.source = ContactSourceBinder(portal_type=("person", "organization"))(self.portal)
        self.portal_path = "/".join(self.portal.getPhysicalPath())

    def test_init(self):
        self.assertIsInstance(self.source, ContactSource)
        self.assertIsInstance(self.source, ObjPathSource)
        self.assertEqual(self.source.portal_url, self.portal.absolute_url())
        self.assertEqual(self.source.portal_path, self.portal_path)
        self.assertIsNone(self.source.relations)
        # relations are removed from the catalog criteria
        source = ContactSourceBinder(portal_type=("person",), relations=[{"position": "/mydirectory"}])(self.portal)
        self.assertEqual(source.relations, {"position": "/mydirectory"})
        self.assertNotIn("relations", source.selectable_filter.criteria)
        # no default term
        self.assertEqual(list(self.source), [])
        self.assertEqual(len(self.source), 0)
        # default terms, given or built by the factory
        source = ContactSourceBinder(portal_type=("person",), default=self.degaulle)(self.portal)
        self.assertEqual([t.value for t in source], [self.degaulle])
        self.assertEqual(len(source), 1)
        source = ContactSourceBinder(portal_type=("person",), defaultFactory=lambda context: self.degaulle)(self.portal)
        self.assertEqual([t.value for t in source], [self.degaulle])

    def test_contains(self):
        self.assertIn(self.degaulle, self.source)
        # the criteria are not checked: an existing value stays valid
        self.assertIn(self.directory, self.source)
        # a value not found in the catalog is kept too
        self.assertIn(self.portal, self.source)

    def test_getTerm(self):
        term = self.source.getTerm(self.degaulle)
        self.assertIsInstance(term, Term)
        self.assertEqual(term.value, self.degaulle)
        self.assertEqual(term.token, "%s/mydirectory/degaulle" % self.portal_path)
        self.assertEqual(term.title, "Général Charles De Gaulle")
        # the criteria are not checked
        self.assertEqual(self.source.getTerm(self.directory).value, self.directory)

    def test_getTermByToken(self):
        token = "%s/mydirectory/degaulle" % self.portal_path
        term = self.source.getTermByToken(token)
        self.assertEqual(term.value, self.degaulle)
        self.assertEqual(term.token, token)
        # placeholder of a missing value, hidden by the display templates
        term = self.source.getTermByToken("#error-missing-/mydirectory/unknown")
        self.assertEqual(term.value, "/mydirectory/unknown")
        self.assertEqual(term.token, "#error-missing-/mydirectory/unknown")
        self.assertEqual(term.title, "Hidden or missing item '/mydirectory/unknown'")
        # unknown token
        with self.assertRaises(LookupError):
            self.source.getTermByToken("%s/mydirectory/unknown" % self.portal_path)

    def test_isBrainSelectable(self):
        brain = api.content.find(UID=self.degaulle.UID())[0]
        self.assertTrue(self.source.isBrainSelectable(brain))
        self.assertFalse(self.source.isBrainSelectable(None))

    def test_getTermByBrain(self):
        brain = api.content.find(UID=self.degaulle.UID())[0]
        # the value is the object
        term = self.source.getTermByBrain(brain)
        self.assertIsInstance(term, Term)
        self.assertEqual(term.value, self.degaulle)
        self.assertEqual(term.token, brain.getPath())
        self.assertEqual(term.title, brain.contact_source)
        self.assertEqual(term.brain, brain)
        # the value is the path relative to the portal
        term = self.source.getTermByBrain(brain, real_value=False)
        self.assertEqual(term.value, "/mydirectory/degaulle")
        self.assertEqual(term.token, brain.getPath())

    def test_tokenToPath(self):
        self.assertEqual(self.source.tokenToPath("%s/mydirectory/degaulle" % self.portal_path), "/mydirectory/degaulle")

    def test_tokenToUrl(self):
        self.assertEqual(
            self.source.tokenToUrl("%s/mydirectory/degaulle" % self.portal_path), self.degaulle.absolute_url()
        )

    def test_search(self):
        # search on text
        terms = list(self.source.search("gaulle"))
        self.assertIn(self.degaulle.UID(), [t.brain.UID for t in terms])
        self.assertTrue(all(t.brain.portal_type in ("person", "organization") for t in terms))
        # path prefilter
        terms = list(self.source.search("", prefilter={"portal_type": "organization"}))
        self.assertEqual(sorted(set(t.brain.portal_type for t in terms)), ["organization"])
        # limit
        self.assertEqual(len(list(self.source.search("", limit=1))), 1)
        # an invalid query gives no result
        self.assertEqual(list(self.source.search("gaulle AND")), [])
        # restriction on the relations of an object
        source = ContactSourceBinder(portal_type=("held_position",))(self.portal)
        relations = {"position": "/mydirectory/armeedeterre/general_adt"}
        terms = list(source.search("", relations=relations))
        self.assertEqual(len(terms), 1)
        held_position = terms[0].brain.getObject()
        self.assertEqual(held_position.position.to_object, self.armeedeterre["general_adt"])
        # an unknown related object is ignored
        self.assertEqual(list(source.search("", relations={"position": "/unknown"})), [])
        # nothing is related
        self.assertEqual(list(source.search("", relations={"position": "/mydirectory/degaulle"})), [])
        # relations given to the source binder, the limit applies after the restriction
        source = ContactSourceBinder(portal_type=("held_position",), relations={"position": "/mydirectory/armeedeterre"})(
            self.portal
        )
        held_positions = list(source.search(""))
        self.assertEqual([t.brain.getObject() for t in held_positions], [self.degaulle["adt"]])
        self.assertEqual(len(list(source.search("", limit=1))), 1)
        # review state criteria
        source = ContactSourceBinder(portal_type=("person",), review_state=("active",))(self.portal)
        self.assertIn(self.degaulle.UID(), [t.brain.UID for t in source.search("gaulle")])
        source = ContactSourceBinder(portal_type=("person",), review_state=("deactivated",))(self.portal)
        self.assertEqual(list(source.search("gaulle")), [])
        # no review state (fields without review_state)
        source = ContactSourceBinder(portal_type=("person",), review_state=None)(self.portal)
        self.assertIn(self.degaulle.UID(), [t.brain.UID for t in source.search("gaulle")])


class TestContactSourceBinder(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_WIDGET_INTEGRATION

    def test_call(self):
        portal = self.layer["portal"]
        binder = ContactSourceBinder(portal_type=("person",))
        self.assertIs(binder.path_source, ContactSource)
        self.assertIsInstance(binder(portal), ContactSource)
        self.assertIsInstance(RelationChoice(source=binder, title="x"), RelationChoice)
