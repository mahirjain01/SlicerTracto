import importlib
import pkgutil
import inspect
import warnings

warnings.filterwarnings("ignore")

dipy_subpackages = ["io", "reconst", "segment", "tracking"]

def list_dipy_contents():
    dipy_structure = {}

    for subpackage_name in dipy_subpackages:
        full_subpackage_name = f"dipy.{subpackage_name}"
        try:
            subpackage_module = importlib.import_module(full_subpackage_name)
            dipy_structure[subpackage_name] = {}
        except ImportError:
            continue

        if hasattr(subpackage_module, "__path__"):
            for module_info in pkgutil.iter_modules(subpackage_module.__path__):
                module_name = module_info.name
                full_module_name = f"{full_subpackage_name}.{module_name}"
                
                try:
                    module = importlib.import_module(full_module_name)
                    dipy_structure[subpackage_name][module_name] = {"functions": [], "classes": {}}
                except ImportError:
                    continue

                for name, obj in inspect.getmembers(module, inspect.isfunction):
                    dipy_structure[subpackage_name][module_name]["functions"].append(name)

                for name, obj in inspect.getmembers(module, inspect.isclass):
                    class_methods = [func_name for func_name, func_obj in inspect.getmembers(obj, inspect.isfunction)]
                    dipy_structure[subpackage_name][module_name]["classes"][name] = class_methods

    return dipy_structure


# dipy_structure = list_dipy_contents()


# for subpackage, modules in dipy_structure.items():
#     print(f"\nSubpackage: {subpackage}")
#     for module, contents in modules.items():
#         print(f"  Module: {module}")
        
#         # List functions
#         if contents["functions"]:
#             print("    Functions:")
#             for func in contents["functions"]:
#                 print(f"      - {func}")
        
#         # List classes and their methods
#         if contents["classes"]:
#             print("    Classes:")
#             for cls, methods in contents["classes"].items():
#                 print(f"      - {cls}")
#                 for method in methods:
#                     print(f"        * {method}")
