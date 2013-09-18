Changelog
=========


1.0 (2013-09-18)
----------------

- Check do_post_sort attribute on source to be able to disable the sorting.

- Declare dependencies on z3c.relationfield and plone.formwidget.contenttree.

- Remove ploneform-render-widget view for content provider, this is now
  in plone.app.z3cform since 0.7.3.


1.0rc1 (2013-03-27)
-------------------

- Added hidden and rtf mode templates.
  [vincentfretin]

- Don't open tooltip in tooltip.
  [vincentfretin]


0.12 (2013-03-12)
-----------------

- Decode title, returning unicode, to standardize term attributes
  [sgeulette]


0.11 (2013-03-11)
-----------------

- Fixed UnicodeDecodeError in @@autocomplete-search
  [vincentfretin]

- Internationalized two messages.
  [vincentfretin]

- Don't show tooltip if the mouse left the link.
  [vincentfretin]

- Don't call tokenToUrl if value is --NOVALUE--.
  [vincentfretin]


0.10 (2013-03-07)
-----------------

- Nothing changed yet.


0.9 (2013-03-07)
----------------

- Initial release.
  [vincentfretin]

