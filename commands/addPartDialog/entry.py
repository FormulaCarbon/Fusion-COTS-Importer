import json
import adsk.core
import os, sys
from ...lib import fusionAddInUtils as futil
from ... import config

from .loader import load_vendors

app = adsk.core.Application.get()
ui = app.userInterface


ADDIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
if ADDIN_ROOT not in sys.path:
    sys.path.insert(0, ADDIN_ROOT)
from vendor import Vendor

LIB_PATH = os.path.join(ADDIN_ROOT, 'lib')
if LIB_PATH not in sys.path:
    sys.path.insert(0, LIB_PATH)
import requests

VENDOR_FOLDER = os.path.join(ADDIN_ROOT, 'vendors')

PALETTE_ID = config.sample_palette_id
PALETTE_URL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'html', 'index.html').replace('\\', '/')
PALETTE_DOCKING = adsk.core.PaletteDockingStates.PaletteDockStateRight
DOWNLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'Downloads', 'Fusion-COTS-Parts')
# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
palette_handlers = []

# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_addPartDialog'
CMD_NAME = 'Vendor Part Search'
CMD_Description = 'A Fusion Add-in Command with a dialog'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the 
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    # TODO Define the dialog for your command by adding different inputs to the command.

    # Create a simple text box input.
    inputs.addStringValueInput('query', 'Query', 'Enter some text.')
    
    vendors = load_vendors(VENDOR_FOLDER, Vendor)
    
    vendorDropdown = inputs.addDropDownCommandInput("vendor", "Vendor", adsk.core.DropDownStyles.TextListDropDownStyle) # type: ignore
    vendorList = vendorDropdown.listItems
    vendorList.add('Select Vendor', True)
    vendorInputs = {}
    for index, name in enumerate(vendors.keys()):
        vendorList.add(name, index == 0)
        vendorInputs[name] = vendors[name].add_inputs(inputs)
    global _vendorCache
    
    _vendorCache = (vendors, vendorInputs)
    
    inputs.addSeparatorCommandInput('sep1')

    # A BoolValueInput with isCheckBox=False is displayed as a push button.
    
    
    external = inputs.addBoolValueInput("external_flag", "External", True)
    inputs.addBoolValueInput('search', 'Search', False, '', False)
    
    # TODO: if external is true, show CloudFolderDialog
    
    #fusionHubFolderDialog = ui.createCloudFolderDialog()
    #fusionHubFolder = fusionHubFolderDialog.showDialog()
    
    on_input_changed = InputChangedHandler()
    args.command.inputChanged.add(on_input_changed)
    local_handlers.append(on_input_changed)
        
    # TODO Connect to the events that are needed by this command.
    #futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    #futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    #futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    #futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    #futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

    # TODO ******************************** Your code here ********************************

    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs
    text_box: adsk.core.TextBoxCommandInput = inputs.itemById('text_box')
    value_input: adsk.core.ValueCommandInput = inputs.itemById('value_input')

    # Do something interesting
    text = text_box.text
    expression = value_input.expression
    msg = f'Your text: {text}<br>Your value: {expression}'
    ui.messageBox(msg)


# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    # General logging for debug.
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Validate Input Event')

    inputs = args.inputs
    
    # Verify the validity of the input values. This controls if the OK button is enabled or not.
    valueInput = inputs.itemById('value_input')
    if valueInput.value >= 0:
        args.areInputsValid = True
    else:
        args.areInputsValid = False
        

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []
    
def _get_palette():
    """Gets or creates the results palette."""
    palette = ui.palettes.itemById(PALETTE_ID)
    if palette is None:
        palette = ui.palettes.add(
            id=PALETTE_ID,
            name='Vendor Part Search',
            htmlFileURL=PALETTE_URL,
            isVisible=True,
            showCloseButton=True,
            isResizable=True,
            width=650,
            height=600,
            useNewWebBrowser=True
        )
        futil.add_handler(palette.closed, _palette_closed, local_handlers=palette_handlers)
        futil.add_handler(palette.navigatingURL, _palette_navigating, local_handlers=palette_handlers)
        futil.add_handler(palette.incomingFromHTML, _palette_incoming, local_handlers=palette_handlers)
        app.log(f'{CMD_NAME}: Created a new palette: ID = {palette.id}')

    if palette.dockingState == adsk.core.PaletteDockingStates.PaletteDockStateFloating:
        palette.dockingState = PALETTE_DOCKING

    palette.isVisible = True
    return palette


def _palette_closed(args: adsk.core.UserInterfaceGeneralEventArgs):
    app.log(f'{CMD_NAME}: Palette was closed.')


def _palette_navigating(args: adsk.core.NavigationEventArgs):
    if args.navigationURL.startswith('http'):
        args.launchExternally = True


def _palette_incoming(html_args: adsk.core.HTMLEventArgs):
    message_data: dict = json.loads(html_args.data)
    message_action = html_args.action
    app.log(f'{CMD_NAME}: Palette event "{message_action}": {message_data}')

    if message_action == 'downloadFile':
        url = message_data.get('url', '')
        filename = message_data.get('filename', 'part')
        result = _download_file(url, filename)
        html_args.returnData = result

    else:
        html_args.returnData = f'OK - {message_action}'


def _download_file(url: str, filename: str) -> str:
    """Downloads the file to the local Downloads folder, or opens it in the
    browser if GrabCAD requires authentication."""
    try:
        os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
        save_path = os.path.join(DOWNLOAD_FOLDER, filename or 'part')
        headers = {
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:154.0) Gecko/20100101 Firefox/154.0'
        }
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return f'Downloaded to {save_path}'
    except Exception as e:
        app.log(f'{CMD_NAME}: Download failed: {type(e).__name__}: {e}')
        _open_in_browser(url)
        return f'Direct download blocked by GrabCAD ({e}). Opened in browser - please log in to download.'


def _open_in_browser(url: str):
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception as e:
        app.log(f'{CMD_NAME}: Could not open browser: {e}')


class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        changed_input = args.input
        inputs = args.inputs
        app.log('change!!')
        
        if changed_input.id == 'vendor':
            selected = changed_input.selectedItem.name
            app.log('vendor chanee')
            app.log(selected)
            
            for name, inps in _vendorCache[1].items():
                app.log(name)
                if name == selected:
                    for key, i in inps.items():
                        i.isVisible = True
                else:
                    for key, i in inps.items():
                        i.isVisible = False

        if changed_input.id == 'search':
            app.log('search')
            palette = None
            try:
                selected_vendor = inputs.itemById('vendor').selectedItem.name
                vendor = _vendorCache[0][selected_vendor]
                filters = {
                    key: vendor_input.value
                    for key, vendor_input in _vendorCache[1][selected_vendor].items()
                }
                palette = _get_palette()
                palette.sendInfoToHTML('status', f'Searching for "{inputs.itemById("query").value}" on {selected_vendor}...')
                results = vendor.search(inputs.itemById('query').value, filters, app)
                app.log(f'SEARCH RESULTS ({selected_vendor}): {results}')
                app.log(f'RESULT COUNT: {len(results)}')
                if isinstance(results, int):
                    palette.sendInfoToHTML('searchError', f'Search failed with status code {results}')
                else:
                    palette.sendInfoToHTML('searchResults', json.dumps({
                        'vendor': selected_vendor,
                        'query': inputs.itemById('query').value,
                        'results': results
                    }))
            except Exception as e:
                app.log(f'SEARCH FAILED: {type(e).__name__}: {e}')
                import traceback
                app.log(traceback.format_exc())
                if palette:
                    palette.sendInfoToHTML('searchError', f'Search failed: {type(e).__name__}: {e}')