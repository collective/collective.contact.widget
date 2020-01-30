from Acquisition import aq_inner
from collective.contact.widget import logger
from copy import deepcopy
from plone import api
from plone.formwidget.contenttree.source import CustomFilter
from plone.formwidget.contenttree.source import ObjPathSource
from plone.formwidget.contenttree.source import PathSourceBinder
from plone.uuid.interfaces import IUUID
from Products.CMFPlone.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from Products.ZCTextIndex.ParseTree import ParseError
from zc.relation.interfaces import ICatalog
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.intid.interfaces import IIntIds
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
        return u""


def parse_query(query, path_prefix=""):
    """Copied from plone.app.vocabularies.catalog.parse_query
    but depth=1 removed.
    """
    query_parts = query.split()
    query = {'SearchableText': []}
    for part in query_parts:
        if part.startswith('path:'):
            path = part[5:]
            query['path'] = {'query': path}
        else:
            query['SearchableText'].append(part)
    text = " ".join(query['SearchableText'])
    for char in '?-+*()':
        text = text.replace(char, ' ')
    query['SearchableText'] = " AND ".join(x + "*" for x in text.split())
    if 'path' in query:
        if query['SearchableText'] == '':
            del query['SearchableText']
        # query["path"]["depth"] = 1
        query["path"]["query"] = path_prefix + query["path"]["query"]
    return query


class ContactSource(ObjPathSource):
    relations = None

    def __init__(self, context, selectable_filter,
                 default=None, defaultFactory=None, **kw):
        """relations params is a dictionary : {relation_name: related_to_path}
        it filters on all results that have a relation with the content
        """
        selectable_filter = deepcopy(selectable_filter)
        if 'relations' in selectable_filter.criteria:
            self.relations = selectable_filter.criteria.pop('relations')[0]
        super(ContactSource, self).__init__(
            context, selectable_filter, {},
            default, defaultFactory, **kw
        )
        self.selectable_filter = selectable_filter
        portal_url = getToolByName(getSite(), 'portal_url')
        self.portal_url = portal_url()
        self.portal_path = portal_url.getPortalPath()

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
            value = brain.getPath()[len(self.portal_path):]
        full_title = safe_unicode(brain.contact_source or brain.Title or brain.id)
        return Term(value, token=brain.getPath(), title=full_title, brain=brain)

    def tokenToPath(self, token):
        """For token='/Plone/a/b', return '/a/b'
        """
        return token.replace(self.portal_path, '', 1)

    def tokenToUrl(self, token):
        return token.replace(self.portal_path, self.portal_url, 1)

    def search(self, query, relations=None, limit=50):
        """Copy from plone.formwidget.contenttree.source,
        to be able to use a modified version of parse_query.
        """
        catalog_query = self.selectable_filter.criteria.copy()

        for criterion in ('review_state', 'portal_type'):
            if criterion in catalog_query and (
                    not catalog_query[criterion] or catalog_query[criterion] == [None]):
                del catalog_query[criterion]

        catalog_query.update(parse_query(query, self.portal_path))

        if limit and 'sort_limit' not in catalog_query:
            catalog_query['sort_limit'] = limit

        if self.relations:
            # we apply limit after restriction on relations
            limit = catalog_query.pop('sort_limit', limit)

        try:
            if 'sort_limit' in catalog_query:  # must limit results because solr sends None for higher limit results
                results = (self.getTermByBrain(brain, real_value=False)
                           for brain in self.catalog(**catalog_query)[:catalog_query['sort_limit']])
            else:
                results = (self.getTermByBrain(brain, real_value=False)
                           for brain in self.catalog(**catalog_query))
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
            for relation, related_to_path in rels.items():
                source_object = aq_inner(api.content.get(related_to_path))
                if not source_object:
                    continue

                found_relations = catalog.findRelations(
                    dict(to_id=intids.getId(aq_inner(source_object)),
                         from_attribute=relation)
                )
                for rel in found_relations:
                    try:
                        obj = intids.queryObject(rel.from_id)
                        related_uids.add(IUUID(obj))
                    except KeyError:
                        logger.error("Related object is missing for relation to %s: %s",
                                     source_object, str(rel.__dict__))

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


class ContactSourceBinder(PathSourceBinder):

    def __init__(self, default=None, defaultFactory=None, **kw):
        self.selectable_filter = CustomFilter(**kw)
        self.default = default
        self.defaultFactory = defaultFactory

    def __call__(self, context):
        return ContactSource(
            context,
            selectable_filter=self.selectable_filter,
            default=self.default,
            defaultFactory=self.defaultFactory)
