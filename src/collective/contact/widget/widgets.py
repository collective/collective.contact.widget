from z3c.form.interfaces import IFieldWidget
import z3c.form.interfaces
from z3c.form.widget import FieldWidget
from zope.component import getUtility
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

from . import _
from .interfaces import (
    IContactAutocompleteWidget,
    IContactAutocompleteSelectionWidget,
    IContactAutocompleteMultiSelectionWidget,
    IContactContent,
    IContactWidgetSettings,
    )

class PatchLoadInsideOverlay(grok.Viewlet):
    grok.context(Interface)
    grok.viewletmanager(IHtmlHeadLinks)

    def render(self):
        return """<script type="text/javascript">
var ccw = {};
$(document).ready(function() {
  $(document).bind('formOverlayLoadSuccess', function(e, req, myform, api, pb, ajax_parent) {
    ajax_parent.find('div').slice(0, 1).prepend(ajax_parent.find('.portalMessage').detach());
  });
  $(document).bind('loadInsideOverlay', function(e, el, responseText, errorText, api) {
    var el = $(el);
    var o = el.closest('.overlay-ajax');
    var pbo = o.data('pbo');
    var overlay_counter = parseInt(pbo.nt.substring(3, pbo.nt.length));
    o.css({zIndex: 9998+overlay_counter});
  });
  ccw.fill_autocomplete = function (el, pbo, noform) {
    var objpath = el.find('input[name=objpath]');
    if (objpath.length) {
        data = objpath.val().split('|');
        var input_box = pbo.source.siblings('div').find('.querySelectSearch input');
        formwidget_autocomplete_new_value(input_box, data[0], data[1]);
        input_box.flushCache();
        // trigger change event on newly added input element
        var input = input_box.parents('.querySelectSearch').parent('div').siblings('.autocompleteInputWidget').find('input').last();
        var url = data[3];
        ccw.add_contact_preview(input, url);
        input.trigger('change');
    }
    return noform;
  };

  var pendingCall = {timeStamp: null, procID: null};
  ccw.add_contact_preview = function (input, url) {
    if (url) {
        input.siblings('.label')
            .wrapInner('<a href="'+url+'" target="_new" class="link-tooltip">');
    }
  };

  $(document).delegate('.link-tooltip', 'mouseleave', function() {
    if (pendingCall.procID) {
      clearTimeout(pendingCall.procID);
      pendingCall.procID = null;
    }
  });
  $(document).delegate('.link-tooltip', 'mouseenter', function() {
    var trigger = $(this);
    // don't open tooltip in tooltip
    if (trigger.closest('.tooltip').length) {
        return;
    }
    if (!trigger.data('tooltip')) {
      if (pendingCall.procID) {
        clearTimeout(pendingCall.procID);
      }
      var timeStamp = new Date();
      var tooltipCall = function() {
          var tip = $('<div class="tooltip pb-ajax" style="display:none">%s</div>')
                .insertAfter(trigger);
          trigger.tooltip({relative: true, position: "center right"});
          var tooltip = trigger.tooltip();
          tooltip.show();
          var url = trigger.attr('href');
          $.get(url, {ajax_load: new Date().getTime()}, function(data) {
            tooltip.hide();
            tooltip.getTip().html($('<div />').append(
                    data.replace(/<script(.|\s)*?\/script>/gi, ""))
                .find(common_content_filter));
            if (pendingCall.timeStamp == timeStamp) {
                tooltip.show();
            }
            pendingCall.procID = null;
          });
      }
      pendingCall = {timeStamp: timeStamp,
                     procID: setTimeout(tooltipCall, 500)};
    }
  });
});
</script>
<style type="text/css">
.tooltip {
  overflow: hidden;
}
.tooltip, #calroot {
  z-index: 99999;
}
</style>
""" % translate(_(u"please wait"), context=self.request)


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

OVERLAY_TEMPLATE = """
$('#%(id)s-autocomplete').find('.%(klass)s'
    ).prepOverlay({
  subtype: 'ajax',
  filter: common_content_filter+',#viewlet-below-content>*',
  formselector: '%(formselector)s',
  cssclass: 'overlay-contact-addnew',
  closeselector: '%(closeselector)s',
  noform: function(el, pbo) {return ccw.fill_autocomplete(el, pbo, 'close');},
  config: {
      closeOnClick: %(closeOnClick)s,
      closeOnEsc: %(closeOnClick)s
  }
});
"""

class ContactBaseWidget(object):
    implements(IContactAutocompleteWidget)
    noValueLabel = _(u'(nothing)')
    autoFill = False
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
                content += OVERLAY_TEMPLATE % dict(
                        id=self.id,
                        klass=action['klass'],
                        formselector=formselector,
                        closeselector=closeselector,
                        closeOnClick=self.close_on_click and 'true' or 'false')

        if include_default:
            content += OVERLAY_TEMPLATE % dict(
                    id=self.id,
                    klass='addnew',
                    formselector='#form',
                    closeselector='[name="form.buttons.cancel"]',
                    closeOnClick=self.close_on_click and 'true' or 'false')

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

        # Update the widget before accessing the source.
        # The source was only bound without security applied
        # during traversal before.
        self.context.update()
        source = self.context.bound_source

        if path is not None:
            query = "path:%s %s" % (source.tokenToPath(path), query)

        if query:
            terms = source.search(query)
        else:
            terms = ()

        if getattr(source, 'do_post_sort', True):
            terms = sorted(set(terms), key=lambda t: t.title)

        return u'\n'.join([u"|".join((t.token, t.title or t.token, t.portal_type, t.url, t.extra))
                            for t in terms])
