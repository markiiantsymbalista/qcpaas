from fastapi import FastAPI
from pydantic import BaseModel
from full_flow.runtime_sdk.worker_metadata import WorkerMetadataRegister
from full_flow.runtime_sdk.http_provider import HTTPPostRequest

app = FastAPI()
class RequestBody(BaseModel):
    program: str
    required_packages: list
class RegisterWorkerRequestBody(BaseModel):
    url: str
    required_packages: list

worker_metadata_register = WorkerMetadataRegister()

@app.get("/")
def root():
    return {"message": "Hello World workflow manager"}

@app.post("/schedule_program")
async def execute_program(body: RequestBody):
    program = body.program
    required_packages = body.required_packages

    #look up for a worker that is able to fulfill program execution criteria
    worker_to_handle_execution = worker_metadata_register.get_worker_by_supported_packages(required_packages)
    if(worker_to_handle_execution == None):
        raise Exception("Runtime doesn't have worker to handle this kind of workload.")

    http_client = HTTPPostRequest(worker_to_handle_execution.url)
    params = {"program": program, "required_packages": required_packages } 
    response = http_client.post(params)

    return {"message": f"Program executed successfully. {response}",}

@app.post("/register-worker")
async def register_worker(body: RegisterWorkerRequestBody):
    worker_metadata_register.add_worker_metadata(body.url, body.required_packages)
    
    return {"message": "Worker registered successfully"}
 
 