import pkgutil
import importlib
import inspect

# Import all classes from all modules in this package
for _, module_name, _ in pkgutil.iter_modules(__path__):
    module = importlib.import_module(f".{module_name}", package=__name__)
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ == module.__name__:
            globals()[name] = obj

# Optional: define __all__ for 'from my_package import *'
__all__ = [name for name, obj in globals().items() if inspect.isclass(obj)] # type: ignore