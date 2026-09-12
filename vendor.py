from abc import ABC, abstractmethod
import adsk.core

class Vendor(ABC):
    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def search(self, query: str) -> list[dict]:
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