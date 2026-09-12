import importlib.util
import inspect
import os
import adsk.core

app = adsk.core.Application.get()

def load_vendors[T](folder_path, base_class: type[T]) -> dict[str, T]:
    """Scans folder_path for .py files, returns {name: instance} for each
    valid concrete subclass of base_class found."""
    vendors = {}

    for filename in os.listdir(folder_path):
       
        if not filename.endswith('.py') or filename.startswith('_'):
            continue
        
        module_name = os.path.splitext(filename)[0]
        filepath = os.path.join(folder_path, filename)

        spec = importlib.util.spec_from_file_location(module_name, filepath)
        module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            # Don't let one broken contributed file crash the whole add-in
            app.log(f"[YourAddin] Failed to load '{filename}': {e}")
            continue

        for _, obj in inspect.getmembers(module, inspect.isclass):
            
            if (
                issubclass(obj, base_class)
                and obj is not base_class
                and not inspect.isabstract(obj)
                and obj.__module__ == module_name  # skip re-imported classes
            ):
                app.log('wwwwww')
                try:
                    instance = obj()
                    vendors[instance.name] = instance
                    
                except Exception as e:
                    app.log(f"[YourAddin] Failed to instantiate {obj}: {e}")

    return vendors