from Acquisition import aq_base
from Acquisition import aq_inner
from collective.contact.widget import logger
from copy import deepcopy
from plone import api
from plone.base.utils import safe_text
from plone.uuid.interfaces import IUUID
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.utils import getToolByName
from Products.ZCTextIndex.ParseTree import ParseError
from z3c.formwidget.query.interfaces import IQuerySource
from zc.relation.interfaces import ICatalog
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.intid.interfaces import IIntIds
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleTerm


class Term(SimpleTerm):
    def __init__(self, value, token=None, title=None, brain=None):
        super(Term, self).__init__(value, token, title)
        self.brain = brain

    @property
    def url(self):
        return self.brain.getURL()

    @property
    def portal_type(self):
        return self.brain.portal_type

    @property
    def extra(self):
        return ""


def parse_query(query, path_prefix=""):
    """Copied from plone.app.vocabularies.catalog.parse_query
    but depth=1 removed.
    """
    query_parts = query.split()
    query = {"SearchableText": []}
    for part in query_parts:
        if part.startswith("path:"):
            path = part[5:]
            query["path"] = {"query": path}
        else:
            query["SearchableText"].append(part)
    text = " ".join(query["SearchableText"])
    for char in "?-+*()":
        text = text.replace(char, " ")
    query["SearchableText"] = " AND ".join(x + "*" for x in text.split())
    # an empty SearchableText matches nothing since ZCatalog 4 (it was ignored before)
    if query["SearchableText"] == "":
        del query["SearchableText"]
    if "path" in query:
        # query["path"]["depth"] = 1
        query["path"]["query"] = path_prefix + query["path"]["query"]
    return query


def closest_content(context=None):
    """Try to find a usable context, with increasing agression.
    Copied from plone.formwidget.contenttree.utils."""
    # Normally, we should be given a useful context (e.g the page)
    c = _valid_context(context)
    if c is not None:
        return c
    # Subforms (e.g. DataGridField) may not have a context set, find out
    # what page is being published
    c = _valid_context(getattr(getRequest(), "PUBLISHED", None))
    if c is not None:
        return c
    # During widget traversal nothing is being published yet, use getSite()
    c = _valid_context(getSite())
    if c is not None:
        return c
    raise ValueError("Cannot find suitable context to bind to source")


def _valid_context(context):
    """Walk up until finding a content item."""
    # Avoid loops. The object id is used as context may not be hashable
    seen = set()
    while context is not None and id(aq_base(context)) not in seen:
        seen.add(id(aq_base(context)))
        if IContentish.providedBy(context) or IFolderish.providedBy(context):
            return context
        parent = getattr(context, "__parent__", None)
        if parent is None:
            parent = getattr(context, "context", None)
        context = parent
    return None


class CustomFilter(object):
    """Catalog criteria of a source (plone.formwidget.contenttree's, without its unused __call__)."""

    def __init__(self, **kw):
        self.criteria = {}
        for key, value in list(kw.items()):
            if not isinstance(value, (list, tuple, set, frozenset)) and not key == "path":
                self.criteria[key] = [value]
            elif isinstance(value, (set, frozenset)):
                self.criteria[key] = list(value)
            else:
                self.criteria[key] = value


@implementer(IQuerySource)
class ContactSource(object):
    """Source of contents, by physical path (was plone.formwidget.contenttree's ObjPathSource)."""

    relations = None

    def __init__(self, context, selectable_filter, navigation_tree_query=None, default=None, defaultFactory=None, **kw):
        """relations params is a dictionary : {relation_name: related_to_path}
        it filters on all results that have a relation with the content
        """
        selectable_filter = deepcopy(selectable_filter)
        if "relations" in selectable_filter.criteria:
            self.relations = selectable_filter.criteria.pop("relations")[0]
        self.context = context
        self.selectable_filter = selectable_filter
        self.navigation_tree_query = navigation_tree_query
        self.catalog = getToolByName(context, "portal_catalog")
        portal_url = getToolByName(getSite(), "portal_url")
        self.portal_url = portal_url()
        self.portal_path = portal_url.getPortalPath()
        self._default_terms = []
        if default is not None:
            self._default_terms = [self.getTerm(default)]
        elif defaultFactory is not None:
            self._default_terms = [self.getTerm(defaultFactory(context))]

    def __iter__(self):
        return iter(self._default_terms)

    def __len__(self):
        return len(self._default_terms)

    def __contains__(self, value):
        try:
            brain = self._getBrainByValue(value)
            # a missing or invisible item is kept
            if brain is None:
                return True
            return self.isBrainSelectable(brain)
        except (KeyError, IndexError):
            return False

    def getTermByToken(self, token):
        if token.startswith("#error-missing-"):
            return self._placeholderTerm(token.partition("#error-missing-")[2])
        brain = self._getBrainByToken(token)
        if not self.isBrainSelectable(brain):
            raise LookupError(token)
        return self.getTermByBrain(brain)

    def getTerm(self, value):
        brain = self._getBrainByValue(value)
        if brain is None:
            return self._placeholderTerm(value)
        if not self.isBrainSelectable(brain):
            raise LookupError('Value "%s" does not match criteria for field' % value)
        return self.getTermByBrain(brain)

    def _getBrainByToken(self, token):
        rid = self.catalog.getrid(token)
        if not rid:
            return None
        return self.catalog._catalog[rid]

    def _getBrainByValue(self, value):
        return self._getBrainByToken("/".join(value.getPhysicalPath()))

    def _placeholderTerm(self, value):
        """Term to keep a value whose brain can't be found (hidden in the display templates)."""
        return SimpleTerm(str(value), token="#error-missing-" + value, title="Hidden or missing item '%s'" % value)

    def isBrainSelectable(self, brain):
        if brain is None:
            return False

        # Don't check if the brain satisfy criteria to avoid a LookupError
        # for an existing value on an object that doesn't satisfy the criteria
        # anymore
        # index_data = self.catalog.getIndexDataForRID(brain.getRID())
        # return self.selectable_filter(brain, index_data)

        return True

    def getTermByBrain(self, brain, real_value=True):
        if real_value:
            value = brain._unrestrictedGetObject()
        else:
            value = brain.getPath()[len(self.portal_path) :]
        full_title = safe_text(brain.contact_source or brain.Title or brain.id)
        return Term(value, token=brain.getPath(), title=full_title, brain=brain)

    def tokenToPath(self, token):
        """For token='/Plone/a/b', return '/a/b'"""
        return token.replace(self.portal_path, "", 1)

    def tokenToUrl(self, token):
        return token.replace(self.portal_path, self.portal_url, 1)

    def search(self, query, relations=None, limit=50, prefilter=None):
        """Copy from plone.formwidget.contenttree.source,
        to be able to use a modified version of parse_query.
        """
        catalog_query = self.selectable_filter.criteria.copy()
        if catalog_query.get("review_state", None) == [None]:
            del catalog_query["review_state"]
        catalog_query.update(parse_query(query, self.portal_path))

        if limit and "sort_limit" not in catalog_query:
            catalog_query["sort_limit"] = limit

        if self.relations:
            # we apply limit after restriction on relations
            limit = catalog_query.pop("sort_limit", limit)

        if prefilter:
            catalog_query.update(prefilter)

        try:
            if "sort_limit" in catalog_query:  # must limit results because solr sends None for higher limit results
                results = (
                    self.getTermByBrain(brain, real_value=False)
                    for brain in self.catalog(**catalog_query)[: catalog_query["sort_limit"]]
                )
            else:
                results = (self.getTermByBrain(brain, real_value=False) for brain in self.catalog(**catalog_query))
        except ParseError:
            return []

        rels = deepcopy(self.relations or {})
        rels.update(relations or {})
        if not rels:
            return results
        else:
            catalog = getUtility(ICatalog)
            intids = getUtility(IIntIds)
            related_uids = set()
            for relation, related_to_path in list(rels.items()):
                source_object = aq_inner(api.content.get(related_to_path))
                if not source_object:
                    continue

                found_relations = catalog.findRelations(
                    dict(to_id=intids.getId(aq_inner(source_object)), from_attribute=relation)
                )
                for rel in found_relations:
                    try:
                        obj = intids.queryObject(rel.from_id)
                        related_uids.add(IUUID(obj))
                    except KeyError:
                        logger.error(
                            "Related object is missing for relation to %s: %s", source_object, str(rel.__dict__)
                        )

            if not related_uids:
                return []

            def get_results():
                counter = 0
                for r in results:
                    if r.brain.UID in related_uids:
                        yield r
                        counter += 1
                        if counter == limit:
                            return

            return get_results()


# separate base class: collective.contact.contactlist calls super(ContactSourceBinder, self).__call__(context)
@implementer(IContextSourceBinder)
class PathSourceBinder(object):

    def __init__(self, navigation_tree_query=None, default=None, defaultFactory=None, **kw):
        self.selectable_filter = CustomFilter(**kw)
        self.navigation_tree_query = navigation_tree_query
        self.default = default
        self.defaultFactory = defaultFactory

    def __call__(self, context):
        return self.path_source(
            closest_content(context),
            selectable_filter=self.selectable_filter,
            navigation_tree_query=self.navigation_tree_query,
            default=self.default,
            defaultFactory=self.defaultFactory,
        )

    def __contains__(self, value):
        # If used without being properly bound (looks at DataGridField), bind
        # now and pass through to the bound version
        return self(None).__contains__(value)


class ContactSourceBinder(PathSourceBinder):
    path_source = ContactSource
