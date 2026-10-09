*** Settings ***
Documentation  Plone 6 Classic UI keywords. Same keyword names and arguments as ui_plone4.robot.
...            Robot Framework 3.2 syntax: shared with the Plone 4.3 (Python 2) environment.
...            Modals: pat-plone-modal; contact widget: pat-livesearch (li.search-result).
Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot
Library  Remote  ${PLONE_URL}/RobotRemote


*** Variables ***
${MODAL}  css=.modal-dialog


*** Keywords ***
Open the add menu
    Click element  css=#plone-contentmenu-factories > a
    Wait until element is visible  css=#plone-contentmenu-factories ul

Add new
    [Documentation]  Add form of a content type, from the add menu of the current page
    [Arguments]  ${portal_type}
    Open the add menu
    Click link  css=#plone-contentmenu-factories a#${portal_type}
    Wait until page contains element  css=#form

Click the edit tab
    Click link  css=#contentview-edit a
    Wait until page contains element  css=#form

The modal is open
    [Documentation]  Overlay (Plone 4) or modal (Plone 6) showing a form
    Wait until element is visible  ${MODAL} form

Click the modal button
    [Documentation]  Button of the form shown in the modal, by name (e.g. form.buttons.save):
    ...              pat-plone-modal shows the form buttons in the modal footer
    [Arguments]  ${name}
    Click button  css=.modal-footer [name="${name}"]

The modal is closed
    Wait until page does not contain element  ${MODAL}

The status message contains
    [Arguments]  ${text}
    Wait until element contains  css=.portalMessage  ${text}

Select in the contact widget
    [Documentation]  Search a contact widget (by widget id) and select the first result containing the text
    [Arguments]  ${widget_id}  ${text}
    Input text  css=#${widget_id}-widgets-query  ${text}
    ${result}=  Set variable  xpath=(//*[@id="${widget_id}-autocomplete"]//li[contains(@class, "search-result")][contains(., "${text}")])[1]
    Wait until element is visible  ${result}
    Click element  ${result}

The contact widget results contain
    [Arguments]  ${widget_id}  ${text}
    Wait until element is visible  xpath=//*[@id="${widget_id}-autocomplete"]//li[contains(@class, "search-result")][contains(., "${text}")]
