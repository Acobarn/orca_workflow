import os
import sys
import importlib
# copied from ComfyUI
class Executor():

    FUNCTION_CLASS_MAPPINGS:dict = {}

    def __init__(self) -> None:
        pass

    def load_plugins_class(self,plugins_path):
        module_name = os.path.basename(plugins_path)
        if os.path.isfile(plugins_path):
            sp = os.path.splitext(plugins_path)
            module_name = sp[0]
        try:
            if os.path.isfile(plugins_path):
                module_spec = importlib.util.spec_from_file_location(module_name, plugins_path)
            else:
                module_spec = importlib.util.spec_from_file_location(module_name, os.path.join(plugins_path, "__init__.py"))

            module = importlib.util.module_from_spec(module_spec)
            sys.modules[module_name] = module
            module_spec.loader.exec_module(module)

            if hasattr(module, "FUNCTION_CLASS_MAPPINGS") and getattr(module, "FUNCTION_CLASS_MAPPINGS") is not None:
                for name in module.FUNCTION_CLASS_MAPPINGS:
                    print(f"Loading {name} function from {plugins_path}.")
                    self.FUNCTION_CLASS_MAPPINGS[name] = module.FUNCTION_CLASS_MAPPINGS[name]
                return True
            else:
                print(f"Skip {plugins_path} module for custom plugins due to the lack of FUNCTION_CLASS_MAPPINGS.")
                return False
        except Exception as e:
            print(f"Cannot import {plugins_path} module for custom plugins:", e)
            return False

    def load_functions(self) -> None:

        base_path = os.path.dirname(os.path.realpath(__file__))
        function_paths = os.path.join(base_path, "function_plugins")
        plugins_paths = os.listdir(os.path.realpath(function_paths))
        if "__pycache__" in plugins_paths:
            plugins_paths.remove("__pycache__")

        for plugins in plugins_paths:
            plugins_path = os.path.join(function_paths,plugins)
            if os.path.isfile(plugins_path) and os.path.splitext(plugins_path)[1] != ".py": continue
            self.load_plugins_class(plugins_path)
        

    def execute_function(self,inputs:dict,function_name:str) -> dict:
        obj_class = self.FUNCTION_CLASS_MAPPINGS[function_name]()
        class_inputs = obj_class.INPUT_TYPES()
        required_inputs = class_inputs['required']
        input_data_all = {} 
        for x in required_inputs:
            if x not in inputs:
                error = {
                "type": "required_input_missing",
                "message": "Required input is missing",
                "details": f"{x}",
                "extra_info": {
                    "input_name": x
                    }
                }
                print(error)
                continue
            input_data_all[x] = inputs[x]
        result = getattr(obj_class,obj_class.FUNCTION)(**input_data_all)
        return result