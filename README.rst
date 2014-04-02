=========================
collective.contact.widget
=========================


class IMyProject(Interface):

	manager = ContactChoice(
        title=_(u"Project Manager"),
        source=ContactSourceBinder(portal_type=("held_position",),
                                   relations={'position': '/contacts/ecreall'}),
        )

Means that 'manager' is a multivalued contact field wich vocabulary
get held_position of site
restricted to ones wich have a 'position' relation to '/contacts/ecreall'
(i.e. wich are held_positions in ecreall company)