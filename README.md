# name in progress
<img width="800" height="450" alt="demo_v0 1" src="https://github.com/user-attachments/assets/4fabe75e-8e74-4edf-bdc4-a2a554436cec" />

a modular, inbuilt COTS browser for Fusion 360

## basic algorithm

vendors are implemented through as a child class. they take a query and a number of kwargs (or a dict) and return a json containing search results. vendor classes also have a function that adds any vendor-specific inputs to the dialog box.

user has a query and other info. Dialog triggers a pallete that renders the search results using HTML. user clicks on an item and it is downloaded.

Current functionality:
- Search for parts, browse, and download
- currently only supports goBILDA and Thrifty Bot, GrabCAD is hidden until auth is sorted
Can add part as internal component
- macos currently doesnt fully support importing properly and instead imports into a new tab

Upcoming functionality:
- Search filters
- Ability to add part as external component using `createCloudFolderDialog()`
- Fix auth issues with GrabCAD
- more vendors
- proper macos importing


## vendors

| vendor | search source | notes |
| --- | --- | --- |
| goBILDA | `searchserverapi.com` search API | all step file zips |
| Thrifty Bot | shopify search JSON (`search/suggest.json`) | Google Drive share links inside the product description, links are extracted from the description markup |
| GrabCAD | API | hidden for now, downloads need auth so we need a way to let the user auth |

shopify search caps results at 10 per query, so thrifty bot returns at most 10 hits and drops any that don't have a CAD file.

## installation

### from a build

```bash
python3 build.py
```

this writes `dist/VendorSearch.bundle`, a zip containing a `VendorSearch.bundle` folder. unpack it into fusion's plugin directory and restart fusion:

- macOS: `~/Library/Application Support/Autodesk/ApplicationPlugins`
- Windows: `%APPDATA%\Autodesk\ApplicationPlugins`

The add-in starts with fusion. It also shows up under Utilities > Scripts and Add-Ins if you want to stop or start it manually.

### for development

Clone the repo and copy it into the Add-Ins directory as a folder named
`VendorSearch`, so the folder, `.py` and `.manifest` names all match:

- macOS: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/VendorSearch`
- Windows: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\VendorSearch`

Or in Fusion, go to the Utilities tab, click "Scripts and Add-Ins", then the +, then "script or add-in from device" and select the folder.
