from collective.contact.widget import _
from collective.contact.widget.interfaces import IContactAutocompleteMultiSelectionWidget
from collective.contact.widget.interfaces import IContactAutocompleteSelectionWidget
from collective.contact.widget.interfaces import IContactAutocompleteWidget
from collective.contact.widget.interfaces import IContactWidgetSettings
from plone import api
from plone.app.layout.viewlets import common as base
from plone.formwidget.autocomplete.widget import AutocompleteMultiSelectionWidget
from plone.formwidget.autocomplete.widget import AutocompleteSearch as BaseAutocompleteSearch
from plone.formwidget.autocomplete.widget import AutocompleteSelectionWidget
from Products.CMFPlone.utils import base_hasattr
from Products.CMFPlone.utils import safe_unicode
from z3c.form.interfaces import IFieldWidget
from z3c.form.widget import FieldWidget
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility
from zope.interface import implementer
from zope.interface.interfaces import ComponentLookupError
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.interfaces import IVocabulary
from zope.schema.interfaces import IVocabularyFactory

import html
import json
import z3c.form.interfaces


try:
    from plone.formwidget.masterselect.interfaces import IMasterSelectWidget
    from plone.formwidget.masterselect.widget import MasterSelect as BaseMasterSelect

    @implementer(IMasterSelectWidget)
    class MasterSelect(BaseMasterSelect):
        def getSlaves(self):
            for slave in self.field.slave_fields:
                yield slave.copy()
except ImportError:
    class MasterSelect(object):
        pass


class TermViewlet(base.ViewletBase):

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
        return html.escape(title)

    @property
    def portal_type(self):
        return self.context.portal_type

    @property
    def url(self):
        return self.context.absolute_url()

    def render(self):
        return u"""<input type="hidden" name="objpath" value="%s" />""" % (
            '|'.join([self.token, self.title, self.portal_type, self.url]))


@implementer(IContactAutocompleteWidget)
class ContactBaseWidget(object):
    noValueLabel = _(u'(nothing)')
    autoFill = False
    maxResults = 50
    close_on_click = True
    display_template = ViewPageTemplateFile('templates/contact_display.pt')
    input_template = ViewPageTemplateFile('templates/contact_input.pt')
    hidden_template = ViewPageTemplateFile('templates/contact_hidden.pt')
    rtf_template = ViewPageTemplateFile('templates/contact_rtf.pt')

    # JavaScript template
    js_template = """\
    (function($) {
        $().ready(function() {
            $('#%(id)s-input-fields').data('klass','%(klass)s').data('title','%(title)s').data('input_type','%(input_type)s').data('multiple', %(multiple)s);
            $('#%(id)s-buttons-search').remove();
            $('#%(id)s-widgets-query').autocomplete('%(url)s', {
                autoFill: %(autoFill)s,
                minChars: %(minChars)d,
                max: %(maxResults)d,
                mustMatch: %(mustMatch)s,
                matchContains: %(matchContains)s,
                matchSubset: false,
                formatItem: %(formatItem)s,
                formatResult: %(formatResult)s,
                parse: %(parseFunction)s,
                extraParams: {'prefilter': function() {return $('#formfield-%(id)s .prefilter-select').val() || '';}}
            }).result(%(js_callback)s);
            %(js_extra)s
        });
    })(jQuery);
    """

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

    # replace the jquery autocomplete by pat-livesearch (see contact_input.pt)
    livesearch = False
    livesearch_min_chars = 3

    def livesearch_url(self):
        return "%s/++widget++%s/@@livesearch-search" % (
            self.request.getURL(), self.name)

    def addnew_modal_options(self):
        """Value of data-pat-plone-modal of the add links (livesearch only):
        close the modal without reloading the page and select the created
        content in the widget (ccwAddNewSuccess, see LIVESEARCH_JS_TEMPLATE).
        """
        if not self.livesearch:
            return None
        return json.dumps({'actionOptions': {
            'onSuccess': 'ccwAddNewSuccess',
            'displayInModal': False,
            'reloadWindowOnClose': False,
        }})

    def livesearch_options(self):
        """Value of data-pat-livesearch, None if livesearch is not used."""
        if not self.livesearch:
            return None
        return json.dumps({
            'ajaxUrl': self.livesearch_url(),
            'minimumInputLength': self.livesearch_min_chars,
            'perPage': self.maxResults,
            'itemTemplate': LIVESEARCH_ITEM_TEMPLATE,
        })
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
        for key, value in list(attributes.items()):
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
                closeselector = action.get(
                    'closeselector', '[name="form.buttons.cancel"]')
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

    def prefilter_terms(self):
        if isinstance(self.field.prefilter_vocabulary, str):
            vocabulary = getUtility(IVocabularyFactory, name=self.field.prefilter_vocabulary)
            return vocabulary(self.context)
        elif IVocabulary.providedBy(self.field.prefilter_vocabulary):
            return self.field.prefilter_vocabulary
        elif IContextSourceBinder.providedBy(self.field.prefilter_vocabulary):
            source = self.field.prefilter_vocabulary
            return source(self.context)
        else:
            return []

    def prefilter_default_value(self):
        if callable(self.field.prefilter_default_value):
            return self.field.prefilter_default_value(self.context)
        else:
            return None


# pat-livesearch (mockup) item: it only navigates to `url`, so the selection is
# done by the widget javascript (see LIVESEARCH_JS_TEMPLATE) from the data-*
LIVESEARCH_ITEM_TEMPLATE = (
    '<li class="search-result list-group-item list-group-item-action"'
    ' data-token="<%- token %>" data-title="<%- title %>"'
    ' data-contact-url="<%- contact_url %>">'
    '<img src="<%- icon %>" /> <%- title %></li>')

LIVESEARCH_JS_TEMPLATE = r"""
    (function($) {
        // Shared by all the widgets of the page.
        if (!window.ccw_new_value) {
            // Select a value in a widget (widget_id is the id of the widget)
            // and return the input of this value. It is a copy of
            // formwidget_autocomplete_new_value (plone.formwidget.autocomplete),
            // whose javascript is not loaded anymore, which does not guess
            // the widget from the search input.
            window.ccw_new_value = function(widget_id, value, label, url) {
                var widget_base = $('#' + widget_id + '-input-fields');
                var options = widget_base.find('input:radio, input:checkbox');
                // clear the query box (this hides the add link) and uncheck any radio boxes
                $('#' + widget_id + '-widgets-query').val('').trigger('input');
                widget_base.find('input:radio').prop('checked', false);
                // if a radio/check box for this value already exists, check it
                var existing = options.filter(function() { return this.value === value; });
                if (existing.length) {
                    existing.prop('checked', true);
                    return existing.first();
                }
                var idx = options.length;
                while ($('#' + widget_id + '-' + idx).length) { idx++; }
                var option_id = widget_id + '-' + idx;
                var input = $('<input/>')
                    .attr({'type': widget_base.data('input_type'),
                           'id': option_id,
                           'name': widget_base.attr('data-widget-name') + (widget_base.data('multiple') ? ':list' : ''),
                           'title': widget_base.data('title'),
                           'checked': 'checked'})
                    .val(value)
                    .addClass(widget_base.data('klass'));
                // the link is the one of ccw.add_contact_preview: forms.js
                // (collective.contact.core) reads the title of the selected
                // contact in it
                var label_content = url ?
                    $('<a target="_new" class="link-tooltip"/>').attr({'href': url, 'data-base_url': url}).text(label) :
                    document.createTextNode(label);
                $('<span class="option"/>').attr('id', option_id + '-wrapper')
                    .append($('<label/>').attr('for', option_id)
                        .append(input)
                        .append(' ')
                        .append($('<span class="label"/>').append(label_content)))
                    .appendTo(widget_base);
                // tooltipster is initialized once on the existing links
                if (url && window.tooltipster_helper) {
                    tooltipster_helper('#' + option_id + '-wrapper .link-tooltip', '', '#content');
                }
                return input;
            };
            // onSuccess of the pat-plone-modal opened by an add link: the
            // response is the page of the created content, where the
            // term-contact viewlet gives "path|title|portal_type|url".
            // Select it in the widget of the link (data-widget-id). Cancel
            // gives no such viewlet: do nothing.
            window.ccwAddNewSuccess = function(modal, response) {
                var link = $(modal.$el);
                var widget_id = link.attr('data-widget-id');
                var infos = $('<div>').append($.parseHTML(response)).find('input[name=objpath]').first().val();
                if (!infos) { return; }
                if (!widget_id) {
                    console.warn('ccwAddNewSuccess: the modal was not opened by an add link of a contact widget');
                    return;
                }
                // the title may contain '|': token is first, url is last
                var parts = infos.split('|');
                var title = $('<span>').html(parts.slice(1, -2).join('|')).text();
                window.ccw_new_value(widget_id, parts[0], title, parts[parts.length - 1]).trigger('change');
            };
        }
        // Other scripts (collective.contact.core forms) still call the jquery
        // autocomplete API on the search input: map it on pat-livesearch.
        // extraParams become hidden fields of the livesearch fieldset, so
        // they are sent with the query.
        if (!$.fn.setOptions || !$.fn.setOptions.livesearch) {
            var original_setOptions = $.fn.setOptions;
            var original_flushCache = $.fn.flushCache;
            $.fn.setOptions = function(options) {
                var rest = $();
                this.each(function() {
                    var fieldset = $(this).closest('.pat-livesearch');
                    if (!fieldset.length) { rest = rest.add(this); return; }
                    if ('extraParams' in options) {
                        // like the jquery autocomplete: they replace the previous ones
                        fieldset.find('input.livesearch-extra').filter(function() {
                            return !(this.name in options.extraParams);
                        }).remove();
                    }
                    $.each(options.extraParams || {}, function(name, value) {
                        var hidden = fieldset.find('input.livesearch-extra').filter(function() { return this.name === name; });
                        if (!hidden.length) {
                            hidden = $('<input type="hidden" class="livesearch-extra" form="livesearch-no-form" />').attr('name', name).appendTo(fieldset);
                        }
                        hidden.val(typeof value === 'function' ? value() : value);
                    });
                    if ('minChars' in options) {
                        var pattern = fieldset[0]['pattern-livesearch'] || fieldset.data('pattern-livesearch');
                        if (pattern && pattern.options) {
                            pattern.options.minimumInputLength = options.minChars;
                        } else {
                            console.warn('setOptions: minChars is not supported by this pat-livesearch');
                        }
                    }
                });
                if (original_setOptions && rest.length) { original_setOptions.call(rest, options); }
                return this;
            };
            $.fn.setOptions.livesearch = true;
            $.fn.flushCache = function() {
                var rest = this.filter(function() { return !$(this).closest('.pat-livesearch').length; });
                if (original_flushCache && rest.length) { original_flushCache.call(rest); }
                return this;
            };
        }
        $(function() {
            $('#%(id)s-input-fields').data('klass','%(klass)s').data('title','%(title)s').data('input_type','%(input_type)s').data('multiple', %(multiple)s);
            $('#%(id)s-buttons-search').remove();
            var container = $('#%(id)s-autocomplete');
            // tooltips of the selected contacts rendered by the server (those
            // added by javascript are initialized by ccw_new_value); skip the
            // links already initialized by a global call (collective.contact.core)
            if (window.tooltipster_helper) {
                tooltipster_helper('#%(id)s-autocomplete .link-tooltip:not(.tooltipstered)', '', '#content');
            }
            var input_box = $('#%(id)s-widgets-query');
            // the livesearch form only serializes its own fields
            var prefilter = container.find('.prefilter-select');
            var prefilter_hidden = container.find('.livesearch-prefilter');
            prefilter.on('change', function() {
                prefilter_hidden.val($(this).val() || '');
            }).trigger('change');
            function select_item(item) {
                window.ccw_new_value('%(id)s', item.attr('data-token'), item.attr('data-title'), item.attr('data-contact-url')).trigger('change');
                container.find('.livesearch-results').addClass('d-none');
            }
            container.on('click', '.livesearch-results li.search-result', function(e) {
                e.preventDefault();
                select_item($(this));
            });
            input_box.on('keydown', function(e) {
                if (e.which === 13) {
                    // do not submit the main form, select the highlighted result
                    e.preventDefault();
                    var active = container.find('.livesearch-results li.search-result.active');
                    if (active.length) { select_item(active.first()); }
                }
            });
            %(js_extra)s
        });
    })(jQuery);
    """


@implementer(IContactAutocompleteSelectionWidget)
class ContactAutocompleteSelectionWidget(ContactBaseWidget, AutocompleteSelectionWidget, MasterSelect):
    display_template = ViewPageTemplateFile('templates/contact_display_single.pt')
    livesearch = True
    js_template = LIVESEARCH_JS_TEMPLATE


@implementer(IContactAutocompleteMultiSelectionWidget)
class ContactAutocompleteMultiSelectionWidget(ContactBaseWidget, AutocompleteMultiSelectionWidget):
    """
    """
    livesearch = True
    js_template = LIVESEARCH_JS_TEMPLATE


@implementer(IFieldWidget)
def ContactAutocompleteFieldWidget(field, request):
    widget = ContactAutocompleteSelectionWidget(request)
    return FieldWidget(field, widget)


@implementer(IFieldWidget)
def ContactAutocompleteMultiFieldWidget(field, request):
    widget = ContactAutocompleteMultiSelectionWidget(request)
    return FieldWidget(field, widget)


class AutocompleteSearch(BaseAutocompleteSearch):

    def get_query(self):
        return self.request.get('q', None)

    def get_terms(self):
        # We want to check that the user was indeed allowed to access the
        # form for this widget. We can only this now, since security isn't
        # applied yet during traversal.
        self.validate_access()

        query = self.get_query()
        path = self.request.get('path', None)
        if not query:
            if path is None:
                return ()
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
            prefilter = {}
            try:
                prefilter_param = json.loads(self.request.get('prefilter'))
                if isinstance(prefilter_param, dict) and len(prefilter_param) > 0:
                    prefilter = prefilter_param
            except (ValueError, TypeError):
                pass

            terms = source.search(query, relations=relations, prefilter=prefilter)

        else:
            terms = ()

        if getattr(source, 'do_post_sort', True):
            terms = sorted(set(terms), key=lambda t: t.title)
        return terms

    def __call__(self):
        terms = self.get_terms()
        response = self.request.response
        response.setHeader('Content-type', 'text/plain')

        return u'\n'.join([u"|".join((t.token, t.title or t.token, t.portal_type, t.url, t.extra))
                          for t in terms])


class LivesearchSearch(AutocompleteSearch):
    """Same search as AutocompleteSearch, answering the json expected by
    pat-livesearch. The query comes from the livesearch form serialization,
    i.e. the name of the subform text input."""

    def get_query(self):
        return (self.request.get('q') or
                self.request.get('%s.widgets.query' % self.context.name))

    def __call__(self):
        terms = list(self.get_terms())[:self.context.maxResults]
        portal_url = api.portal.get().absolute_url()
        items = [{
            # pat-livesearch goes to `url` on Enter: stay on the page
            'url': '#livesearch-select',
            'error': True,  # pat-livesearch does not navigate on click
            'title': t.title or t.token,
            'token': t.token,
            'contact_url': t.url,
            'icon': '%s/@@iconresolver/contenttype/%s' % (portal_url, t.portal_type),
        } for t in terms]
        response = self.request.response
        response.setHeader('Content-type', 'application/json')
        return json.dumps({'items': items, 'total': len(items)})
