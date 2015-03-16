from z3c.form.interfaces import IFieldWidget
import z3c.form.interfaces
from z3c.form.widget import FieldWidget
from zope.component import getUtility
from zope.component.interfaces import ComponentLookupError
from zope.i18n import translate
from zope.interface import implementer, implements, Interface
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from five import grok

from Products.CMFPlone.utils import base_hasattr, safe_unicode
from plone.app.layout.viewlets.interfaces import IBelowContent
from plone.app.layout.viewlets.interfaces import IHtmlHeadLinks
from plone.formwidget.autocomplete.widget import (
    AutocompleteMultiSelectionWidget,
    AutocompleteSelectionWidget)
from plone.formwidget.autocomplete.widget import AutocompleteSearch as BaseAutocompleteSearch

from collective.contact.widget import _
from collective.contact.widget.interfaces import (
    IContactAutocompleteWidget,
    IContactAutocompleteSelectionWidget,
    IContactAutocompleteMultiSelectionWidget,
    IContactContent,
    IContactWidgetSettings,
    )


class PatchLoadInsideOverlay(grok.Viewlet):
    grok.context(Interface)
    grok.viewletmanager(IHtmlHeadLinks)
    wait_msg = _(u"please wait")
    tooltip_template = ViewPageTemplateFile('js/widget.js.pt')

    def render(self):
        return self.tooltip_template() % {
                'wait_msg': translate(self.wait_msg, context=self.request)}


class TermViewlet(grok.Viewlet):
    grok.name('term-contact')
    grok.context(IContactContent)
    grok.viewletmanager(IBelowContent)

    @property
    def token(self):
        return '/'.join(self.context.getPhysicalPath())

    @property
    def title(self):
        if base_hasattr(self.context, 'get_full_title'):
            title = self.context.get_full_title()
        else:
            title = self.context.Title()
        title = title and safe_unicode(title) or u""
        return title

    @property
    def portal_type(self):
        return self.context.portal_type

    @property
    def url(self):
        return self.context.absolute_url()

    def render(self):
        return u"""<input type="hidden" name="objpath" value="%s" />""" % (
                    '|'.join([self.token, self.title, self.portal_type, self.url]))


class ContactBaseWidget(object):
    implements(IContactAutocompleteWidget)
    noValueLabel = _(u'(nothing)')
    autoFill = False
    maxResults = 50
    close_on_click = True
    display_template = ViewPageTemplateFile('templates/contact_display.pt')
    input_template = ViewPageTemplateFile('templates/contact_input.pt')
    hidden_template = ViewPageTemplateFile('templates/contact_hidden.pt')
    rtf_template = ViewPageTemplateFile('templates/contact_rtf.pt')
    js_callback_template = """
function (event, data, formatted) {
    (function($) {
        var input_box = $(event.target);
        formwidget_autocomplete_new_value(input_box,data[0],data[1]);
        // trigger change event on newly added input element
        var input = input_box.parents('.querySelectSearch').parent('div').siblings('.autocompleteInputWidget').find('input').last();
        var url = data[3];
        ccw.add_contact_preview(input, url);
        input.trigger('change');
    }(jQuery));
}
"""
    overlay_template = ViewPageTemplateFile('js/overlay.js.pt')
    placeholder = _(u"Fill your search here...")

    @property
    def bound_source(self):
        try:
            return super(ContactBaseWidget, self).bound_source
        except ComponentLookupError:
            return []

    def tokenToUrl(self, token):
        if token == "--NOVALUE--":
            return ""
        return self.bound_source.tokenToUrl(token)

    def render(self):
        settings = getUtility(IContactWidgetSettings)
        attributes = settings.add_contact_infos(self)
        for key, value in attributes.items():
            setattr(self, key, value)
        if self.mode == z3c.form.interfaces.DISPLAY_MODE:
            return self.display_template(self)
        elif self.mode == z3c.form.interfaces.HIDDEN_MODE:
            return self.hidden_template(self)
        elif self.mode == "rtf":
            return self.rtf_template(self)
        else:
            return self.input_template(self)

    def js_extra(self):
        content = ""
        include_default = False
        for action in self.actions:
            formselector = action.get('formselector', None)
            if formselector is None:
                include_default = True
            else:
                closeselector = action.get('closeselector',
                        '[name="form.buttons.cancel"]')
                content += self.overlay_template(**dict(
                        klass=action['klass'],
                        formselector=formselector,
                        closeselector=closeselector,
                        closeOnClick=self.close_on_click and 'true' or 'false'))

        if include_default:
            content += self.overlay_template(**dict(
                    klass='addnew',
                    formselector='#form',
                    closeselector='[name="form.buttons.cancel"]',
                    closeOnClick=self.close_on_click and 'true' or 'false'))

        return content

class ContactAutocompleteSelectionWidget(ContactBaseWidget, AutocompleteSelectionWidget):
    implements(IContactAutocompleteSelectionWidget)


class ContactAutocompleteMultiSelectionWidget(ContactBaseWidget, AutocompleteMultiSelectionWidget):
    implements(IContactAutocompleteMultiSelectionWidget)


@implementer(IFieldWidget)
def ContactAutocompleteFieldWidget(field, request):
    widget = ContactAutocompleteSelectionWidget(request)
    return FieldWidget(field, widget)


@implementer(IFieldWidget)
def ContactAutocompleteMultiFieldWidget(field, request):
    widget = ContactAutocompleteMultiSelectionWidget(request)
    return FieldWidget(field, widget)


class AutocompleteSearch(BaseAutocompleteSearch):
    def __call__(self):
        # We want to check that the user was indeed allowed to access the
        # form for this widget. We can only this now, since security isn't
        # applied yet during traversal.
        self.validate_access()

        query = self.request.get('q', None)
        path = self.request.get('path', None)
        if not query:
            if path is None:
                return ''
            else:
                query = ''

        relations = self.request.get('relations', None)
        # Update the widget before accessing the source.
        # The source was only bound without security applied
        # during traversal before.
        self.context.update()
        source = self.context.bound_source
        if path is not None:
            query = "path:%s %s" % (source.tokenToPath(path), query)

        if query or relations:
            terms = source.search(query, relations=relations)
        else:
            terms = ()

        if getattr(source, 'do_post_sort', True):
            terms = sorted(set(terms), key=lambda t: t.title)

        return u'\n'.join([u"|".join((t.token, t.title or t.token, t.portal_type, t.url, t.extra))
                            for t in terms])
