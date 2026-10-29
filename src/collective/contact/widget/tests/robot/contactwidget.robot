*** Settings ***
Documentation  collective.contact.widget keywords, built on the ui_plone${PLONE_MAJOR}.robot keywords.
...            Robot Framework 3.2 syntax (shared with the Plone 4.3 environment).
...            Fixture: collective.contact.core test_data profile and testtype (testing.IPrefiltering).
...            Selectors: this package's templates (contact_input.pt, radio/checkbox_input.pt, contact_display.pt).
Resource  ui_plone${PLONE_MAJOR}.robot


*** Variables ***
${DIRECTORY_URL}  ${PLONE_URL}/mydirectory
${CORPSB}  ${DIRECTORY_URL}/armeedeterre/corpsb
${SERGENT_LH}  ${DIRECTORY_URL}/armeedeterre/corpsa/divisionalpha/regimenth/brigadelh/sergent_lh
${SERGENT_PEPPER}  ${DIRECTORY_URL}/pepper/sergent_pepper
${RAMBO}  ${DIRECTORY_URL}/rambo
${DRAPER}  ${DIRECTORY_URL}/draper
# testtype fields (collective.contact.core testing.IPrefiltering), the second one prefilters on organizations
${CONTACT_LIST}  form-widgets-IPrefiltering-contact_list_no_default
${ORGANIZATION_LIST}  form-widgets-IPrefiltering-contact_list_with_contextual_default


*** Keywords ***
Open a manager browser
    Open test browser
    Set window size  1280  2000
    Enable autologin as  Manager

Save the form
    Click button  css=#form-buttons-save

Create a test type content
    [Documentation]  testtype content with Rambo and Draper in its contact list, Corps B in its organization list
    Go to  ${PLONE_URL}
    Add new  testtype
    Select in the contact widget  ${CONTACT_LIST}  Rambo
    Select in the contact widget  ${CONTACT_LIST}  Draper
    Select in the contact widget  ${ORGANIZATION_LIST}  Corps B
    Save the form
    Wait until page contains element  css=#${CONTACT_LIST}

Type in the contact widget
    [Arguments]  ${widget_id}  ${text}
    Input text  css=#${widget_id}-widgets-query  ${text}

Selected contact
    [Documentation]  Locator of the radio or checkbox of a contact (by url) in a contact widget
    [Arguments]  ${widget_id}  ${url}
    [Return]  xpath=//*[@id="${widget_id}-input-fields"]//label[.//a[contains(@class, "link-tooltip")][@href="${url}"]]/input

The contact is selected in the widget
    [Documentation]  The contact is checked in the widget, with a link to it
    [Arguments]  ${widget_id}  ${url}
    ${input}=  Selected contact  ${widget_id}  ${url}
    Wait until page contains element  ${input}
    Element attribute value should be  ${input}  checked  true

The contact is not selected in the widget
    [Arguments]  ${widget_id}  ${url}
    ${input}=  Selected contact  ${widget_id}  ${url}
    Element attribute value should be  ${input}  checked  ${None}

Unselect the contact in the widget
    [Arguments]  ${widget_id}  ${url}
    ${input}=  Selected contact  ${widget_id}  ${url}
    Click element  ${input}

The contact widget value contains
    [Arguments]  ${widget_id}  ${text}
    Wait until element contains  css=#${widget_id}-input-fields  ${text}

The contact widget display links to
    [Documentation]  Display mode of a contact widget (view of a content): link to the contact
    [Arguments]  ${widget_id}  ${url}  ${text}
    Element should contain  xpath=//*[@id="${widget_id}"]//a[contains(@class, "link-tooltip")][@href="${url}"]  ${text}

The contact widget display does not link to
    [Arguments]  ${widget_id}  ${url}
    Page should not contain element  xpath=//*[@id="${widget_id}"]//a[@href="${url}"]

The add new link of the contact widget is visible
    [Documentation]  "Create ..." link under a contact widget: shown once text is typed
    [Arguments]  ${widget_id}  ${expected}=${True}
    Run keyword if  ${expected}
    ...  Wait until element is visible  css=#${widget_id}-autocomplete .addnew-block a
    ...  ELSE  Wait until element is not visible  css=#${widget_id}-autocomplete .addnew-block a

Click the add new link of the contact widget
    [Documentation]  Opens the add form in a modal
    [Arguments]  ${widget_id}
    The add new link of the contact widget is visible  ${widget_id}
    Click link  css=#${widget_id}-autocomplete .addnew-block a
    The modal is open

The textfield value becomes
    [Documentation]  For values filled by javascript
    [Arguments]  ${locator}  ${value}
    Wait until keyword succeeds  10s  0.5s  Textfield value should be  ${locator}  ${value}
