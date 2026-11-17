*** Settings ***
Documentation  Add new link of a contact widget: shown once text is typed, opens the add form (overlay / modal)
...            prefilled with the typed text, the created contact is selected in the widget.
...            Version-independent: Plone selectors are in ui_plone*.robot.
Resource  contactwidget.robot
Test Setup  Open a manager browser
Test Teardown  Close all browsers


*** Variables ***
# @@add-held-position form of collective.contact.core: person field, add link to ++add++person
${PERSON}  oform-widgets-person


*** Test Cases ***
Create a contact from the contact widget
    Go to  ${DIRECTORY_URL}/@@add-held-position
    The add new link of the contact widget is visible  ${PERSON}  ${False}
    Type in the contact widget  ${PERSON}  Chuck Norris
    The add new link of the contact widget is visible  ${PERSON}
    Click the add new link of the contact widget  ${PERSON}
    The textfield value becomes  css=#form-widgets-firstname  Chuck
    The textfield value becomes  css=#form-widgets-lastname  Norris
    Click element  css=#form-widgets-gender-0
    Click the modal button  form.buttons.save
    The modal is closed
    The contact widget value contains  ${PERSON}  Chuck Norris
    The contact is selected in the widget  ${PERSON}  ${DIRECTORY_URL}/mr-chuck-norris
