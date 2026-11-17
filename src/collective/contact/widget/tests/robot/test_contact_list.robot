*** Settings ***
Documentation  Contact list field (ContactList): several selections, unselection, display mode links.
...            Version-independent: Plone selectors are in ui_plone*.robot.
Resource  contactwidget.robot
Test Setup  Open a manager browser
Test Teardown  Close all browsers


*** Test Cases ***
Select several contacts in a contact list
    Go to  ${PLONE_URL}
    Add new  testtype
    Select in the contact widget  ${CONTACT_LIST}  Rambo
    Select in the contact widget  ${CONTACT_LIST}  Draper
    The contact is selected in the widget  ${CONTACT_LIST}  ${RAMBO}
    The contact is selected in the widget  ${CONTACT_LIST}  ${DRAPER}
    Select in the contact widget  ${ORGANIZATION_LIST}  Corps B
    Save the form
    The contact widget display links to  ${CONTACT_LIST}  ${RAMBO}  John Rambo
    The contact widget display links to  ${CONTACT_LIST}  ${DRAPER}  John Draper
    The contact widget display links to  ${ORGANIZATION_LIST}  ${CORPSB}  Corps B

Unselect a contact of a contact list
    Create a test type content
    Click the edit tab
    The contact is selected in the widget  ${CONTACT_LIST}  ${RAMBO}
    The contact is selected in the widget  ${CONTACT_LIST}  ${DRAPER}
    Unselect the contact in the widget  ${CONTACT_LIST}  ${DRAPER}
    Save the form
    The status message contains  Changes saved
    The contact widget display links to  ${CONTACT_LIST}  ${RAMBO}  John Rambo
    The contact widget display does not link to  ${CONTACT_LIST}  ${DRAPER}
