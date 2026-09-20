from vendor import Vendor
import os, sys
import adsk.core

lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
print(lib_path, len(lib_path))
if lib_path not in sys.path:
    sys.path.append(lib_path)
    
import requests

class GrabCAD(Vendor):
    @property
    def name(self):
        return 'GrabCAD'
       
    # TODO: use kwargs/dict for anything after query 
    def search(self, query: str, filters: dict, app) -> list[dict] | int:
        
        url = f"https://grabcad.com/community/api/v1/models?query={query}&sort={filters['sort']}&softwares={','.join(filters['allowed_types'])}"
        headers = {
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:154.0) Gecko/20100101 Firefox/154.0'
        }
        
        response = requests.get(url, headers=headers)
        app.log('asdasdasd')
        if response.status_code == 200:
            models = response.json()['models']
            out = [self.__reformat__(model, filters['allowed_types']) for model in models]
            return out
        
        else:
            return response.status_code
        
    def add_inputs(self, inputs: adsk.core.CommandCreatedEventArgs.command.commandInputs) -> dict:
        sort = inputs.addStringValueInput('sort'+self.name, 'Sort', 'gabcad')
        filter = inputs.addStringValueInput('filter'+self.name, 'Filter', 'gabcad')
        sort.isVisible = False
        filter.isVisible = False
        return {'sort': sort, 'filter': filter}
        
    def __reformat__(self, item: dict, allowed_types: list) -> dict:
        types = ['STEP / IGES' if t == 'step-slash-iges' else t for t in allowed_types]
        files_url = f"https://grabcad.com/community/api/v1/models/{item['cached_slug']}/files"
        headers = {
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:154.0) Gecko/20100101 Firefox/154.0'
        }
        
        links = []
        
        for file in requests.get(files_url, headers=headers).json()['files']:
            if file['system'] not in types:
                continue
            links.append({  
                'name': file['name'],
                'type': file['extension'],
                'download_url': file['download_url']
            })
                
        out = {
            'name': item['name'],
            'author': item['author']['name'],
            'image': item['preview_image'],
            'files': links
        }
        
        return out