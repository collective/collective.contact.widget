Changelog
=========

1.2.2 (2014-09-25)
------------------

- Add review_state parameter on ContactList and ContactChoice widgets.
  [cedricmessiant]

1.2.1 (2014-09-10)
------------------

- UI : improve prefill of add new contact overlay form.
  [thomasdesvenain]


1.2 (2014-06-02)
----------------

- We can give as source param a 'relations' value to filter on contents
  related to an other content.
  [thomasdesvenain]


1.1 (2014-03-11)
----------------

- Don't include closeOnClick: true in javascript, so it defaults to
  global configuration.
  [vincentfretin]

- UI improvements :
  - Add contact link is displayed after user has filled a search.
  - We have and explicit help message next to contact link.
  - Contact creation form title is pre-filled with user search.
  - The search input has a placeholder.
  [thomasdesvenain]

- Execute prepOverlay only if it hasn't been done yet, this avoid to have a
  pbo undefined error when you have recursive overlays.
  [vincentfretin]

- The jqueryui autocomplete plugin conflicts with the jquery autocomplete
  plugin used by plone.formwidget.autocomplete, disable the jqueryui one.
  [cedricmessiant]

- Do not break dexterity content type when we don't have a REQUEST
  (in async context).
  [thomasdesvenain]

- We can add contact and contact list fields TTW on dexterity content types.
  [thomasdesvenain]


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

