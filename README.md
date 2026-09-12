# name in progress

a modular, inbuilt COTS browser for Fusion 360

## basic algorithm

vendors are implemented through as a child class. they take a query and a number of kwargs (or a dict) and return a json containing search results. vendor classes also have a function that adds any vendor-specific inputs to the dialog box.

user has a query and other info. Dialog triggers a pallete that renders the search results using HTML. user clicks on an item and it is downloaded.