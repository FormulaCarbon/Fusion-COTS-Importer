vendor template - write necessary function defs and add to `vendors` folder. look at `vendors/grabcad.py` for an example

```py
from vendor import Vendor

import os, sys

lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
print(lib_path, len(lib_path))
if lib_path not in sys.path:
    sys.path.append(lib_path)
    
import requests

class YourVendor(Vendor):
    @property
    def name(self):
        return 'YourVendorName' # What shows up in dropdown
        
    def search(self, query: str, ... ) -> list[dict] | int:
        """ 
        Search Function
        Should return a list of items with each item having {name, author, image, [{download link, name, type}]} 
        """
        
        # if it fails return an error code

    def add_inputs(self, inputs: adsk.core.CommandCreatedEventArgs.command.commandInputs) -> dict:
        """
        vendor-specific command dialog input objects
        ensure that the id for each object is unique. it is recommended to append self.name to the end of the id.
        """
        return {'name': inputobj}
```