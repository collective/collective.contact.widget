*** Settings ***
Documentation  Single contact field (ContactChoice): search, selection with a link to the contact, saved value.
...            Version-independent: Plone selectors are in ui_plone*.robot.
Resource  contactwidget.robot
Test Setup  Open a manager browser
Test Teardown  Close all browsers


*** Variables ***
# held position schema: organization or position
${POSITION}  form-widgets-position


*** Test Cases ***
Search contacts in a contact field
    Go to  ${SERGENT_PEPPER}/edit
    Type in the contact widget  ${POSITION}  Corps
    The contact widget results contain  ${POSITION}  Corps A
    The contact widget results contain  ${POSITION}  Corps B

Select a contact in a contact field
    Go to  ${SERGENT_PEPPER}/edit
    The contact is selected in the widget  ${POSITION}  ${SERGENT_LH}
    Select in the contact widget  ${POSITION}  Corps B
    The contact is selected in the widget  ${POSITION}  ${CORPSB}
    The contact is not selected in the widget  ${POSITION}  ${SERGENT_LH}
    Save the form
    The status message contains  Changes saved
    Go to  ${SERGENT_PEPPER}/edit
    The contact is selected in the widget  ${POSITION}  ${CORPSB}
