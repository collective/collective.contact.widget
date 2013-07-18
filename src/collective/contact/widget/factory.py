from plone.schemaeditor.fields import FieldFactory
from collective.contact.widget import schema
from collective.contact.widget import _
from plone.supermodel.exportimport import BaseHandler

ContactChoiceFactory = FieldFactory(schema.ContactChoice, _(u"Contact"))
ContactChoiceHandler = BaseHandler(schema.ContactChoice)
ContactListFactory = FieldFactory(schema.ContactList, _(u"Contact list"))
ContactListHandler = BaseHandler(schema.ContactList)