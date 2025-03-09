import inspect
import ast
import os
from full_flow.runtime_sdk.http_provider import HTTPPostRequest

class RuntimeProvider():
    def __init__(self):
        pass
    
    def schedule(self, module_name: str):
        
        #we don't even need OpenQASM here as agreed previously, 
        # as we don't care what framework is under the hood. We could execute any quantum framework,
        # as long at there is a worker on runtime that could execute it.
        module_in_string : str = self.module_to_string(module_name)
        
        # that is how runtime allows to handle workloads of absolutely different kinds, so we are not tied to qiskit with 
        # qiskit-runtime or to pennylane catalyst or even to open-source dell-runtime with is also based on qiskit. 
        required_packages = self.get_required_packages(module_in_string)
        
        workflow_manager_url = "http://127.0.0.1:8000/schedule_program"
        http_client = HTTPPostRequest(workflow_manager_url)
        params = {"program": module_in_string, "required_packages": list(required_packages)}
        
        response = http_client.post(params)
        return response
        
          
    def module_to_string(self, module_name) -> str:
        try:
            module = __import__(module_name)
            source_code = inspect.getsource(module)
            return source_code
        except ImportError:
            print(f"Module '{module_name}' not found.")
            return "None"
        
    def get_required_packages(self, program_string):
        required_modules = set()
        tree = ast.parse(program_string)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    required_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                required_modules.add(node.module)
        #quite limited approach. More robust version should be created.
        required_packages = set([imp.split('.')[0] for imp in required_modules])

        stdlib_modules = self.get_stdlib_module_names()

        filtered_required_packages = required_packages - stdlib_modules
        
        #Refactor
        return filtered_required_packages
    
    def get_stdlib_module_names(self):
        stdlib_path = os.path.dirname(os.__file__)
        stdlib_modules = {name.split('.')[0] for name in os.listdir(stdlib_path) if not name.startswith('_')}
        # Additional hardcoded standard libraries not found in the os.listdir call
        hardcoded_stdlibs = {'sys', 'math', 'os', 'io', 'time', 're', 'threading', 'functools', 'collections', 'itertools', 'datetime', 'argparse'}
        stdlib_modules.update(hardcoded_stdlibs)
        
        return stdlib_modules
  
#  Alternatively required packages could be retrieved from requirements.txt directly.   
#      def read_requirements(file_path):
#         with open(file_path, 'r') as file:
#             lines = file.readlines()
#             # Extract package names without version specifiers
#             packages = [line.split('==')[0].strip() for line in lines if line.strip() and not line.startswith('#')]
#         return packages

# # Example usage
# file_path = 'requirements.txt'  # Path to your requirements.txt file
# packages = read_requirements(file_path)
# print(packages)