from collective.contact.widget.testing import COLLECTIVE_CONTACT_WIDGET_INTEGRATION
from plone import api

import unittest


class TestSetup(unittest.TestCase):
    """Test that collective.contact.widget is properly installed."""

    layer = COLLECTIVE_CONTACT_WIDGET_INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]

    def test_profile(self):
        setup_tool = api.portal.get_tool("portal_setup")
        profile_ids = [p["id"] for p in setup_tool.listProfileInfo()]
        self.assertIn("collective.contact.widget:default", profile_ids)
        # the dependency of the profile is installed
        self.assertTrue(setup_tool.getLastVersionForProfile("collective.js.tooltipster:default"))
