from fastapi import FastAPI
from pydantic import BaseModel
from full_flow.runtime_sdk.http_provider import HTTPPostRequest
from full_flow.external_libraries.qiskit_execution_backend import QiskitExecutionBackend
from full_flow.runtime_sdk.runtime_plugin_resolver import RuntimePluginResolver

class ExecuteRequestBody(BaseModel):
    program: str
    required_packages: list

app = FastAPI()

@app.on_event("startup")
async def startup_logic():
    startup_handler()

@app.get("/")
def root():
    return {"message": "Hello World worker"}

@app.post("/execute_program")
async def execute_program(body: ExecuteRequestBody):
    program = body.program
    
    globals_dict = {}
    
    try:
        exec(program, globals_dict)
               
        first_descendant_name = find_first_descendant('RuntimeWorkerBase', globals_dict)
        RuntimeWorkerBase = globals_dict[first_descendant_name]
        instance = RuntimeWorkerBase()
        
        #only qiskit is supported right now, but we could add support for pennylane etc.
        qiskit_execution_backend = QiskitExecutionBackend(instance.backend_name)
        if("qiskit" not in body.required_packages):
            raise NotImplementedError("Only qiskit SDK is supported right now.")

        resolver = RuntimePluginResolver()
        resolver.resolve(instance.execution_options, qiskit_execution_backend, instance)
            
        instance.run()
        result = instance.get_result()
    except Exception as error:
        print(f"Error happened when executing program: {error}")
        
    return {"result": f"{result}"} 

# function that each worker should have in order to register itself with workflow manager, 
# providing info about supported versions on frameworks, libraries Qiskit, Pennylane mitiq.
def startup_handler():
    print("Running startup logic...")
    
    # this URL will be retrieved from an orchestrator like Kubernetes in the future. 
    # for debugging without docker, worker & workflow-manager should be replace with localhost
    self_worker_service_url = "http://worker:8001/execute_program"
    
    workflow_manager_register_url = "http://workflow-manager:8000/register-worker"
    http_client = HTTPPostRequest(workflow_manager_register_url)
    
    params = {"url": self_worker_service_url, "required_packages": get_env_libraries_metadata()} 
    response = http_client.post(params)
    
def get_env_libraries_metadata() -> list:
    # this will be logic that discovers libraries in the container image.
    return ['numpy', 'full_flow', 'qiskit_aer', 'qiskit', 'mitiq']

def find_first_descendant(base_class_name, globals_dict):
    base_class = globals_dict.get(base_class_name)
    if not base_class:
        return None 
    for name, obj in globals_dict.items():
        if isinstance(obj, type) and issubclass(obj, base_class) and obj is not base_class:
            return name  
    return None  
    