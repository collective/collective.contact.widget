*** Settings ***
Documentation  Plone 4.3 keywords. Same keyword names and arguments as ui_plone6.robot.
...            Robot Framework 3.2 syntax (Python 2 environment).
...            Overlays: plone.app.jquerytools; contact widget: jQuery autocomplete (.ac_results).
Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot
Library  Remote  ${PLONE_URL}/RobotRemote


*** Variables ***
${MODAL}  css=div.overlay-ajax


*** Keywords ***
Open the add menu
    Click element  css=#plone-contentmenu-factories dt.actionMenuHeader a
    Wait until element is visible  css=#plone-contentmenu-factories dd.actionMenuContent

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
    [Documentation]  Overlay (Plone 4) or modal (Plone 6) showing a form.
    ...              The loaded overlay focuses its first input: typing in an autocomplete before would be blurred
    Wait until element is visible  ${MODAL} form
    Wait for condition  return jQuery(document.activeElement).closest('div.overlay').length > 0

Click the modal button
    [Documentation]  Button of the form shown in the modal, by name (e.g. form.buttons.save).
    ...              Retried: the overlay content moves while fields are shown ('slow' animation)
    [Arguments]  ${name}
    Wait until keyword succeeds  10s  1s  Click button  ${MODAL} [name="${name}"]

The modal is closed
    Wait until element is not visible  ${MODAL}

The status message contains
    [Arguments]  ${text}
    [Documentation]  Plone 4: the first .portalMessage is the hidden #kssPortalMessage template
    Wait until element contains  css=.portalMessage:not(#kssPortalMessage)  ${text}

Select in the contact widget
    [Documentation]  Search a contact widget (by widget id) and select the first result containing the text
    [Arguments]  ${widget_id}  ${text}
    Input text  css=#${widget_id}-widgets-query  ${text}
    Wait until element is visible  jquery=.ac_results:visible li:contains("${text}")
    Click element  jquery=.ac_results:visible li:contains("${text}"):first

The contact widget results contain
    [Arguments]  ${widget_id}  ${text}
    Wait until element is visible  jquery=.ac_results:visible li:contains("${text}")
