from vendor import Vendor
import os, sys
import adsk.core

lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)

import requests


class GoBilda(Vendor):
    @property
    def name(self):
        return 'goBILDA'

    # TODO: use kwargs/dict for anything after query, once filters are added
    def search(self, query: str, filters: dict, app) -> list[dict] | int:

        url = (
            "https://searchserverapi.com/getresults"
            f"?api_key=4M8k1A2N6C&q={query}&maxResults=250"
        )

        app.log('goBILDA: requesting search results')
        response = requests.get(url)
        app.log('goBILDA: response got')

        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])[:15]  # TODO: make this an option
            app.log(str(len(items)))

            out = []
            for item in items:
                res = self.__reformat__(item, [], app)
                hasletter = any(c.isalpha() for c in res['author'])
                if res['files'] and not hasletter:  # filter out items with no files or non-numeric SKU
                    out.append(res)
            return out

        else:
            return response.status_code

    def add_inputs(self, inputs) -> dict:
            # hidden — gobilda search is keyword-driven via the search input
            allowed_types = inputs.addStringValueInput(
                f"allowed_types{self.name}", 'Allowed Types', 'step'
            )
            allowed_types.isVisible = False
            return {'allowed_types': allowed_types}

    def __reformat__(self, item: dict, allowed_types: list, app) -> dict:
        app.log('reformatting')

        sku = item.get('product_code', '')

        links = []
        if sku:
            links.append({
                'name': item.get('title', sku),
                'type': 'STEP',
                'download_url': f'https://www.gobilda.com/content/step_files/{sku}.zip'
            })

        out = {
            'name': item.get('title', ''),
            'author': sku,          # SKU stands in for "author" per goBILDA's flat catalog
            'image': item.get('image_link', ''),
            'files': links
        }

        return out