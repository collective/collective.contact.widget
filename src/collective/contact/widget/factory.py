from Acquisition import aq_get
from zope import component
from zope.component.hooks import getSite
from zope import interface
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from zope.schema.interfaces import IVocabularyFactory
from zope.interface.declarations import implements
from zope.i18n import translate

from Products.CMFCore.utils import getToolByName
from plone.schemaeditor.fields import FieldFactory
from plone.supermodel.exportimport import BaseHandler
from plone.schemaeditor.interfaces import IFieldEditFormSchema

from collective.contact.widget.interfaces import (
        IContactChoice, IContactList,
        IContactChoiceField)
from collective.contact.widget import schema
from collective.contact.widget import _


class ContactHandler(BaseHandler):

    filteredAttributes = BaseHandler.filteredAttributes.copy()
    filteredAttributes.update({'vocabulary': 'w', 'values': 'w', 'source': 'w',
                               'vocabularyName': 'rw'})

    def read(self, element):
        """Update source binder considering the new source_types value
        """
        field_instance = super(ContactHandler, self).read(element)
        field_instance.update_source()
        return field_instance


ContactChoiceFactory = FieldFactory(schema.ContactChoice, _(u"Contact"))
ContactChoiceHandler = ContactHandler(schema.ContactChoice)
ContactListFactory = FieldFactory(schema.ContactList, _(u"Contact list"))
ContactListHandler = ContactHandler(schema.ContactList)


@interface.implementer(IFieldEditFormSchema)
@component.adapter(IContactChoice)
def getContactChoiceFieldSchema(field):
    return IContactChoiceField


class ContactChoiceField(object):
    interface.implements(IContactChoiceField)
    component.adapts(IContactChoice)

    def __init__(self, field):
        self.__dict__['field'] = field


@interface.implementer(IFieldEditFormSchema)
@component.adapter(IContactList)
def getContactListChoiceFieldSchema(field):
    return IContactChoiceField


class ContactListChoiceField(object):
    interface.implements(IContactChoiceField)
    component.adapts(IContactList)

    def __init__(self, field):
        self.__dict__['field'] = field


class ContactTypesVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        contact_types = ('held_position', 'organization',
                         'person', 'position') # @TODO: make it more extensible

        site = getSite()
        ttool = getToolByName(site, 'portal_types')
        request = aq_get(site, 'REQUEST', None)
        return SimpleVocabulary([SimpleTerm(contact_type,
                           token=contact_type,
                           title=translate(ttool[contact_type].Title(), context=request))
                for contact_type in contact_types])
