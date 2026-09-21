# name in progress
<img width="800" height="450" alt="demo_v0 1" src="https://github.com/user-attachments/assets/4fabe75e-8e74-4edf-bdc4-a2a554436cec" />

a modular, inbuilt COTS browser for Fusion 360

## basic algorithm

vendors are implemented through as a child class. they take a query and a number of kwargs (or a dict) and return a json containing search results. vendor classes also have a function that adds any vendor-specific inputs to the dialog box.

user has a query and other info. Dialog triggers a pallete that renders the search results using HTML. user clicks on an item and it is downloaded.

Current functionality:
Search for parts, browse, and download
currently only supports GoBilda, GrabCAD in progress
Can add part as internal component

Upcoming functionality:
Search filters
Ability to add part as external component using `createCloudFolderDialog()`
Fix auth issues with GrabCAD
more vendors

## installation
download as zip (or clone) and add through fusion plugin manager
 
in fusion, go to utilities toolbar, click on "Scripts and Add-Ins", then the +, then "script or add-in from device" and select the folder.
