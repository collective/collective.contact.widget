from zope import component
from zope import interface

from plone.schemaeditor.fields import FieldFactory
from collective.contact.widget import schema
from collective.contact.widget import _
from plone.supermodel.exportimport import BaseHandler
from plone.schemaeditor.interfaces import IFieldEditFormSchema
from collective.contact.widget.interfaces import IContactChoice, IContactList
from collective.contact.widget.interfaces import IContactTypeChoiceField

class ContactHandler(BaseHandler):

    filteredAttributes = BaseHandler.filteredAttributes.copy()
    filteredAttributes.update({'vocabulary': 'w', 'values': 'w', 'source': 'w',
                               'vocabularyName': 'rw'})


ContactChoiceFactory = FieldFactory(schema.ContactChoice, _(u"Contact"))
ContactChoiceHandler = ContactHandler(schema.ContactChoice)
ContactListFactory = FieldFactory(schema.ContactList, _(u"Contact list"))
ContactListHandler = ContactHandler(schema.ContactList)


@interface.implementer(IFieldEditFormSchema)
@component.adapter(IContactChoice)
def getContactTypeChoiceFieldSchema(field):
    return IContactTypeChoiceField


class ContactTypeChoiceField(object):
    interface.implements(IContactTypeChoiceField)
    component.adapts(IContactChoice)


@interface.implementer(IFieldEditFormSchema)
@component.adapter(IContactList)
def getContactListTypeChoiceFieldSchema(field):
    return IContactTypeChoiceField


class ContactListTypeChoiceField(object):
    interface.implements(IContactTypeChoiceField)
    component.adapts(IContactList)
