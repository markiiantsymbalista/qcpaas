from full_flow.runtime_sdk.execution_backend import ExecutionBackend
class RuntimeWorkerBase:
    result: str
    _execution_backend: ExecutionBackend
    _backend_name: str
    _execution_options: dict[str, str]

    @property
    def execution_options(self):
        return self._execution_options
    
    @execution_options.setter
    def execution_options(self, value):
        self._execution_options = value
    
    @property
    def backend_name(self):
        return self._backend_name
    
    @backend_name.setter
    def backend_name(self, value:str):
        self._backend_name = value
    
    @property
    def execution_backend(self):
        return self._execution_backend
    
    @execution_backend.setter
    def execution_backend(self, value: ExecutionBackend):
        self._execution_backend = value
    
    def __init__(self):
        self.result = "Default result value"
        
    def execute(self, circuit, shots, **kwargs):
        
        return self.execution_backend.execute(circuit, shots, **kwargs)
    
    def run(self):
        raise NotImplementedError("Subclasses must implement the 'run' method")
    
    def get_result(self):
        return self.result
