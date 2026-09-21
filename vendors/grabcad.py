from vendor import Vendor
import os, sys
import adsk.core #  type: ignore[import-not-found]

lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)
    
import requests

class GrabCAD(Vendor):
    @property
    def name(self):
        return 'GrabCAD'
       
    # TODO: use kwargs/dict for anything after query 
    def search(self, query: str, filters: dict, app) -> list[dict] | int:
        allowed_types = [t.strip() for t in filters['allowed_types'].split(',')]
        url = f"https://grabcad.com/community/api/v1/models?query={query}&sort={filters['sort']}&softwares={','.join(allowed_types)}"
        headers = {
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:154.0) Gecko/20100101 Firefox/154.0'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            models = response.json()['models']
            out = [self.__reformat__(model, allowed_types) for model in models]
            return out
        
        else:
            return response.status_code
        
    def add_inputs(self, inputs: adsk.core.CommandCreatedEventArgs.command.commandInputs) -> dict:
        sort = inputs.addStringValueInput('sort'+self.name, 'Sort', 'recent')
        types = inputs.addStringValueInput('allowed_types'+self.name, 'Allowed Types', 'step-slash-iges') # type: ignore[attr-defined]
        sort.isVisible = False
        types.isVisible = False
        return {'sort': sort, 'allowed_types': types}
        
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