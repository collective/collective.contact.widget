=========================
collective.contact.widget
=========================

You can add a contact field to your schema, like this ::

	class IMyProject(Interface):

		manager = ContactChoice(
	        title=_(u"Project Manager"),
	        source=ContactSourceBinder(portal_type=("held_position",),
	                                   relations={'position': '/contacts/ecreall'}),
	        )

Example code means that 'manager' is a multivalued contact field wich vocabulary
get held_position of site restricted to ones wich have a 'position' relation to '/contacts/ecreall'
(i.e. wich are held_positions in ecreall company).
portal_type is required as source attribute, and relations is not.