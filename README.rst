=========================
collective.contact.widget
=========================

This add-on is part of the ``collective.contact.*`` suite. For an overview and a demo of these suite, see `collective.contact.demo <https://github.com/collective/collective.contact.demo>`__.

This module provides a widget for contacts.

You can add contact fields to your schema, like this ::

	class IMyProject(Interface):

	    company = ContactChoice(
            title=_(u"Company"),
            source=ContactSourceBinder(portal_type=("organization",),
            )

		manager = ContactList(
	        title=_(u"Project Manager"),
	        source=ContactSourceBinder(portal_type=("held_position",),
	                                   relations={'position': '/contacts/ecreall'}),
	        )

Example code means that 'manager' is a multi-valued contact field which
vocabulary gets held_position objects of site.
The vocabulary is restricted to objects that have a 'position' relation to '/contacts/ecreall' object
(i.e. which are held_positions in ecreall company).

You can add another filtering option like this
	    company = ContactChoice(
            title=_(u"Company"),
            source=ContactSourceBinder(portal_type=("organization",),
            prefilter_vocabulary='vocabulary or source',
            prefilter_default_value='context aware method',
            )

The prefilter vocabulary is displayed in the widget. The user can select a specific directory by example.
Each term value contains a criteria, like u'{"path": "/Plone/directory1"}' (beware to use " in dict !).

If you run this javascript expression :

contactswidget.setup_relation_dependency('form.widgets.company', 'form.widgets.manager', 'position')
the vocabulary of 'manager' field will be restricted to the held_positions of selected company.


Translations
============

This product has been translated into

- Spanish.

- French.

You can contribute for any message missing or other new languages, join us at
`Plone Collective Team <https://www.transifex.com/plone/plone-collective/>`_
into *Transifex.net* service with all world Plone translators community.


Contribute
==========

Have an idea? Found a bug? Let us know by `opening a ticket`_.

- Issue Tracker: https://github.com/collective/collective.contact.widget/issues
- Source Code: https://github.com/collective/collective.contact.widgete
- Documentation: https://github.com/collective/collective.contact.demo/blob/master/README.md

.. _`opening a ticket`: https://github.com/collective/collective.contact.widget/issues


Tests
=====

This add-on is tested using Travis CI. The current status of the add-on is :

.. image:: https://img.shields.io/travis/collective/collective.contact.widget/master.svg
    :target: http://travis-ci.org/collective/collective.contact.widget

.. image:: http://img.shields.io/pypi/v/collective.contact.widget.svg
    :target: https://pypi.python.org/pypi/collective.contact.facetednav


License
=======

The project is licensed under the GPLv2.
