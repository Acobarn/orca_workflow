from pathlib import Path
import traceback
import importlib

here = Path(__file__).parent.resolve()

def load_nodes():
    shorted_errors = []
    full_error_messages = []
    function_class_mappings = {}

    for filename in (here / "function_wrappers").iterdir():
        
        module_name = filename.stem
        try:
            module = importlib.import_module(
                f".function_wrappers.{module_name}", package=__package__
            )
            function_class_mappings.update(getattr(module, "FUNCTION_CLASS_MAPPINGS"))

        except AttributeError:
            pass  # wip nodes
        except Exception:
            error_message = traceback.format_exc()
            full_error_messages.append(error_message)
            error_message = error_message.splitlines()[-1]
            shorted_errors.append(
                f"Failed to import module {module_name} because {error_message}"
            )
    
    if len(shorted_errors) > 0:
        full_err_log = '\n\n'.join(full_error_messages)
        print(f"\n\nFull error log from example_function: \n{full_err_log}\n\n")
    return function_class_mappings

EXAMPLE_FUNCTION_MAPPINGS = load_nodes()

FUNCTION_CLASS_MAPPINGS = {
    **EXAMPLE_FUNCTION_MAPPINGS,
}

