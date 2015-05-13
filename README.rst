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

		manager = ContactChoice(
	        title=_(u"Project Manager"),
	        source=ContactSourceBinder(portal_type=("held_position",),
	                                   relations={'position': '/contacts/ecreall'}),
	        )

Example code means that 'manager' is a multi-valued contact field which
vocabulary gets held_position objects of site.
The vocabulary is restricted to objects that have a 'position' relation to '/contacts/ecreall' object
(i.e. which are held_positions in ecreall company).

If you run this javascript expression :

contactswidget.setup_relation_dependency('form.widgets.company', 'form.widgets.manager', 'position')
the vocabulary of 'manager' field will be restricted to the held_positions of selected company.

