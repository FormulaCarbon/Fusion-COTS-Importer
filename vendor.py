from abc import ABC, abstractmethod
import adsk.core # type: ignore[import-not-found]

class Vendor(ABC):
    # set True to keep a vendor in the tree but out of the add-in's vendor list
    hidden = False

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def search(self, query: str, **kwargs) -> list[dict]:
        """ 
        Search Function
        Should return a list of items with each item having {name, author, image, [{download link, name, type}]} 
        """
        pass
    
    @abstractmethod
    def add_inputs(self, inputs: adsk.core.CommandCreatedEventArgs.command.commandInputs) -> dict:
        """
        vendor-specific input objects
        """
        pass