from collective.contact.widget.source import ContactSource
from collective.contact.widget.source import ContactSourceBinder
from collective.contact.widget.source import parse_query
from collective.contact.widget.source import Term
from collective.contact.widget.testing import COLLECTIVE_CONTACT_WIDGET_INTEGRATION

import unittest


class TestParseQuery(unittest.TestCase):

    def test_words_are_and_joined_with_wildcards(self):
        self.assertEqual(
            parse_query("gen arm"), {"SearchableText": "gen* AND arm*"})

    def test_special_chars_are_removed(self):
        self.assertEqual(
            parse_query("a-b (c)?"), {"SearchableText": "a* AND b* AND c*"})

    def test_empty_text_is_ignored(self):
        # an empty SearchableText matches nothing since ZCatalog 4
        self.assertEqual(parse_query(""), {})
        self.assertEqual(parse_query("  ?-+ "), {})

    def test_path_is_prefixed_and_not_limited_in_depth(self):
        query = parse_query("path:/mydirectory foo", path_prefix="/plone")
        self.assertEqual(query["path"], {"query": "/plone/mydirectory"})
        self.assertEqual(query["SearchableText"], "foo*")

    def test_path_only(self):
        query = parse_query("path:/mydirectory", path_prefix="/plone")
        self.assertEqual(query, {"path": {"query": "/plone/mydirectory"}})


class TestContactSource(unittest.TestCase):

    layer = COLLECTIVE_CONTACT_WIDGET_INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        self.mydirectory = self.portal["mydirectory"]

    def get_source(self, **kwargs):
        kwargs.setdefault("portal_type", ("person", "organization"))
        return ContactSourceBinder(**kwargs)(self.portal)

    def token(self, obj):
        return "/".join(obj.getPhysicalPath())

    def brain(self, obj):
        return self.portal.portal_catalog(UID=obj.UID())[0]

    def test_binder_gives_contact_source(self):
        self.assertIsInstance(self.get_source(), ContactSource)

    def test_search_by_text(self):
        terms = list(self.get_source().search("gaulle"))
        self.assertIn(self.token(self.mydirectory["degaulle"]), [t.token for t in terms])

    def test_search_without_text_returns_contacts(self):
        # regression: an empty search matched nothing
        self.assertTrue(list(self.get_source().search("")))

    def test_search_respects_portal_types(self):
        terms = list(self.get_source(portal_type=("person",)).search(""))
        self.assertTrue(terms)
        self.assertEqual({t.portal_type for t in terms}, {"person"})

    def test_search_limit(self):
        self.assertEqual(len(list(self.get_source().search("", limit=1))), 1)

    def test_search_with_path(self):
        source = self.get_source(portal_type=("organization",))
        armee = self.mydirectory["armeedeterre"]
        path = source.tokenToPath(self.token(armee))
        tokens = [t.token for t in source.search("path:%s" % path)]
        self.assertIn(self.token(armee), tokens)
        self.assertIn(self.token(armee["corpsa"]), tokens)
        self.assertNotIn(self.token(self.mydirectory["degaulle"]), tokens)

    def test_search_with_prefilter(self):
        terms = list(self.get_source().search("", prefilter={"portal_type": "person"}))
        self.assertTrue(terms)
        self.assertEqual({t.portal_type for t in terms}, {"person"})

    def test_search_with_unknown_relation_gives_nothing(self):
        # nothing is related to this directory
        self.assertEqual(
            list(self.get_source().search("", relations={"nothing": "/mydirectory"})), [])

    def test_term(self):
        degaulle = self.mydirectory["degaulle"]
        term = self.get_source().getTermByBrain(self.brain(degaulle))
        self.assertIsInstance(term, Term)
        self.assertEqual(term.value, degaulle)
        self.assertEqual(term.token, self.token(degaulle))
        self.assertEqual(term.url, degaulle.absolute_url())
        self.assertEqual(term.portal_type, "person")
        self.assertEqual(term.extra, u"")

    def test_term_without_real_value_is_a_path(self):
        term = self.get_source().getTermByBrain(
            self.brain(self.mydirectory["degaulle"]), real_value=False)
        self.assertEqual(term.value, "/mydirectory/degaulle")

    def test_token_conversions(self):
        source = self.get_source()
        token = self.token(self.mydirectory)
        self.assertEqual(source.tokenToPath(token), "/mydirectory")
        self.assertEqual(source.tokenToUrl(token), self.mydirectory.absolute_url())

    def test_brain_selectable(self):
        source = self.get_source()
        self.assertFalse(source.isBrainSelectable(None))
        self.assertTrue(source.isBrainSelectable(self.brain(self.mydirectory["degaulle"])))
