import json
import adsk.core
import os, sys, traceback
from ...lib import fusionAddInUtils as futil
from ... import config

from .loader import load_vendors

import adsk.fusion
import zipfile
import tempfile
import shutil

import adsk

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

DEFERRED_IMPORT_EVENT_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_deferredImport'
deferred_import_handlers = []


def start():
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
    futil.add_handler(cmd_def.commandCreated, command_created)

    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
    control.isPromoted = IS_PROMOTED

    # Register the event used to safely defer model-modifying work
    # (importToTarget2) outside of the palette's HTML-callback context.
    try:
        custom_event = app.registerCustomEvent(DEFERRED_IMPORT_EVENT_ID)
    except Exception:
        # Already registered from a previous run that wasn't cleanly stopped.
        app.unregisterCustomEvent(DEFERRED_IMPORT_EVENT_ID)
        custom_event = app.registerCustomEvent(DEFERRED_IMPORT_EVENT_ID)

    on_deferred_import = DeferredImportHandler()
    custom_event.add(on_deferred_import)
    deferred_import_handlers.append(on_deferred_import)


# Executed when add-in is stopped.
def stop():
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    if command_control:
        command_control.deleteMe()
    if command_definition:
        command_definition.deleteMe()

    try:
        palette = ui.palettes.itemById(PALETTE_ID)
        if palette:
            palette.deleteMe()
    except Exception as e:
        app.log(f'{CMD_NAME}: Palette teardown warning: {type(e).__name__}: {e}')

    try:
        app.unregisterCustomEvent(DEFERRED_IMPORT_EVENT_ID)
    except Exception:
        pass

    global deferred_import_handlers
    deferred_import_handlers = []


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

    # Pre-create and show the results palette now, while the dialog is opening.
    # A Fusion palette's HTML loads asynchronously; if we wait until the first
    # search to create it, the very first sendInfoToHTML is fired before the
    # page registers fusionJavaScriptHandler and gets silently dropped.
    try:
        _get_palette()
    except Exception:
        app.log(f'{CMD_NAME}: Could not pre-create palette: {traceback.format_exc()}')

    # A BoolValueInput with isCheckBox=False is displayed as a push button.
    
    
    external = inputs.addBoolValueInput("external_flag", "External", True)
    inputs.addBoolValueInput('search', 'Search', False, '', False)
    
    # TODO: if external is true, show CloudFolderDialog
    
    #fusionHubFolderDialog = ui.createCloudFolderDialog()
    #fusionHubFolder = fusionHubFolderDialog.showDialog()
    
    on_input_changed = InputChangedHandler()
    args.command.inputChanged.add(on_input_changed)
    local_handlers.append(on_input_changed)

    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
        
    # TODO Connect to the events that are needed by this command.
    #futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    #futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    #futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    #futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    #futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')
    # Intentionally empty — the actual work (search) already happened in
    # InputChangedHandler before doExecute() was called. This just lets the
    # command terminate cleanly.


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


SUPPORTED_CAD_EXTENSIONS = {'.step', '.stp', '.iges', '.igs', '.sat', '.smt', '.f3d'}


def _download_file(url: str, filename: str) -> str:
    tmp_dir = None
    try:
        tmp_dir = tempfile.mkdtemp(prefix='fusion_cots_')
        headers = {
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:154.0) Gecko/20100101 Firefox/154.0'
        }

        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        download_path = os.path.join(tmp_dir, filename or 'part')
        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        cad_files = []

        # Check actual file content, not the (possibly wrong) filename/extension.
        if zipfile.is_zipfile(download_path):
            extract_dir = os.path.join(tmp_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(download_path, 'r') as zf:
                zf.extractall(extract_dir)
            for root, _, files in os.walk(extract_dir):
                for fn in files:
                    if os.path.splitext(fn)[1].lower() in SUPPORTED_CAD_EXTENSIONS:
                        cad_files.append(os.path.join(root, fn))
        else:
            if os.path.splitext(download_path)[1].lower() in SUPPORTED_CAD_EXTENSIONS:
                cad_files.append(download_path)

        if not cad_files:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return 'Downloaded, but no supported CAD file (STEP/IGES/SAT/SMT/F3D) was found inside.'

        app.fireCustomEvent(DEFERRED_IMPORT_EVENT_ID, json.dumps({
            'cad_files': cad_files,
            'tmp_dir': tmp_dir
        }))

        return f'Downloaded {filename}. Inserting into design...'

    except Exception as e:
        app.log(f'{CMD_NAME}: Download failed: {type(e).__name__}: {e}')
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        _open_in_browser(url)
        return f'Direct download blocked ({e}). Opened in browser - please log in to download.'


def _insert_cad_file(file_path: str, design: adsk.fusion.Design):
    import_mgr = app.importManager
    ext = os.path.splitext(file_path)[1].lower()

    if ext in ('.step', '.stp'):
        options = import_mgr.createSTEPImportOptions(file_path)
    elif ext in ('.iges', '.igs'):
        options = import_mgr.createIGESImportOptions(file_path)
    elif ext == '.sat':
        options = import_mgr.createSATImportOptions(file_path)
    elif ext == '.smt':
        options = import_mgr.createSMTImportOptions(file_path)
    elif ext == '.f3d':
        options = import_mgr.createFusionArchiveImportOptions(file_path)
    else:
        raise ValueError(f'Unsupported CAD file type: {ext}')

    import_mgr.importToTarget2(options, design.rootComponent)


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

        if changed_input.id == 'vendor':
            selected = changed_input.selectedItem.name
            for name, inps in _vendorCache[1].items():
                visible = (name == selected)
                for key, i in inps.items():
                    i.isVisible = visible

        if changed_input.id == 'search':
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
                app.log(traceback.format_exc())
                if palette:
                    palette.sendInfoToHTML('searchError', f'Search failed: {type(e).__name__}: {e}')
            finally:
                # Close the command dialog immediately after the search completes.
                # Downloads (importToTarget2) are only safe once no command is
                # active — keeping this dialog open indefinitely is what was
                # causing every download to run "within a command" and crash.
                try:
                    inputs.command.doExecute(False)
                except Exception as e:
                    app.log(f'{CMD_NAME}: Could not auto-close command: {e}')

class DeferredImportHandler(adsk.core.CustomEventHandler):
    def notify(self, args: adsk.core.CustomEventArgs):
        payload = {}
        try:
            payload = json.loads(args.additionalInfo)
            cad_files = payload['cad_files']

            design = adsk.fusion.Design.cast(app.activeProduct)
            if not design:
                _notify_palette_status('No active Fusion design to insert into. Open or create a design first.')
                return

            inserted, failed = [], []
            for cad_path in cad_files:
                try:
                    _insert_cad_file(cad_path, design)
                    inserted.append(os.path.basename(cad_path))
                except Exception as e:
                    app.log(f'{CMD_NAME}: Failed to insert {cad_path}: {type(e).__name__}: {e}')
                    failed.append(os.path.basename(cad_path))

            if inserted and not failed:
                msg = f'Inserted as new component: {", ".join(inserted)}'
            elif inserted and failed:
                msg = f'Inserted: {", ".join(inserted)}. Failed: {", ".join(failed)} (see Text Commands log).'
            else:
                msg = 'Failed to insert the CAD file(s) into the design. See Text Commands log for details.'

            _notify_palette_status(msg)

        except Exception:
            app.log(f'{CMD_NAME}: Deferred import failed: {traceback.format_exc()}')
            _notify_palette_status('Import failed unexpectedly. See Text Commands log for details.')
        finally:
            tmp_dir = payload.get('tmp_dir')
            if tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)


def _notify_palette_status(message: str):
    try:
        palette = ui.palettes.itemById(PALETTE_ID)
        if palette:
            palette.sendInfoToHTML('status', message)
    except Exception as e:
        app.log(f'{CMD_NAME}: Could not update palette status: {e}')