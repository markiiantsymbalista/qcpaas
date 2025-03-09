import inspect
import importlib
import os
import glob
from full_flow.runtime_sdk.enriched_execution_backend import EnrichedExecutionBackend
from full_flow.runtime_sdk.runtime_worker_base import RuntimeWorkerBase
from full_flow.runtime_sdk.execution_backend import ExecutionBackend

class RuntimePluginResolver:
    def resolve(self, execution_options, core_execution_backend: ExecutionBackend, worker: RuntimeWorkerBase):
        descendants = self._get_descendants_of_class(EnrichedExecutionBackend)
        is_first_iteration = True
        decorators_not_found = True
        exec_backend: EnrichedExecutionBackend
        for option in execution_options:
            if option in descendants:
                instance = descendants[option]
                if is_first_iteration:
                    instance.set_component(core_execution_backend)
                    is_first_iteration = False  
                else:
                    instance.set_component(exec_backend)
                exec_backend = instance
                decorators_not_found = False
            
        if decorators_not_found:
            worker.execution_backend = core_execution_backend
        else:
            worker.execution_backend = exec_backend
    
    def _get_descendants_of_class(self, target_class):
        descendants = {}

        # List of directories to search for Python files
        directories = ["full_flow/external_libraries"]  # Add more directories as needed
        
        try:
            # Iterate over each directory
            for directory in directories:
                # Search for Python files in the directory
                jopined = os.path.join(directory, "*.py")
                python_files = glob.glob(jopined)
                
                # Iterate over each Python file
                for python_file in python_files:
                    # Extract module name from file path
                    module_name = os.path.splitext(os.path.basename(python_file))[0]
                    
                    module_name = f"full_flow.external_libraries.{module_name}"
                    # Import the module dynamically
                    module = importlib.import_module(module_name)
                    
                    # Collect the descendants
                    module_descendants = []
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, target_class):
                            module_descendants.append((name, obj))
                    
                    # Instantiate the collected subclasses
                    for name, obj in module_descendants:
                        instance = obj()
                        descendants[name] = instance
        except Exception as e:
            print(f"An error occurred: {e}")
        
        return descendants

