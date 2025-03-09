from full_flow.runtime_sdk.execution_backend import ExecutionBackend

class EnrichedExecutionBackend(ExecutionBackend):
    def __init__(self):
        self._execution_backend: ExecutionBackend
    
    def set_component(self, execution_backend: ExecutionBackend):
        self._execution_backend = execution_backend
    
    def execute(self, circuit, shots, **kwargs):
        self._execution_backend.execute(circuit, shots, **kwargs)
    
    def execute_linked_plugin(self, circuit, shots, **kwargs):
        # This call is part of pattern implementation. 
        # Each pipeline step should run execute first in order to implement linking of different plugins and getting their results.
        # results could be added to the array of results if we want to use all of them on the client, or maybe in subsuquent plugins.
        # It is normal practice in OOD. 
        if self.decorator_execution_backend is not None and isinstance(self.decorator_execution_backend, EnrichedExecutionBackend):
            self.set_state = self.decorator_execution_backend.execute(circuit, shots, **kwargs)
         
    @property
    def execution_backend(self) -> ExecutionBackend:
        exec_backend = self._execution_backend
        child_not_found = True
        while(child_not_found):
            if hasattr(exec_backend, '_execution_backend'):
                exec_backend = baz_value = getattr(exec_backend, '_execution_backend')
            else:   
                child_not_found = False
            
        return exec_backend
    
    @property
    def decorator_execution_backend(self) -> ExecutionBackend:
        return self._execution_backend
    
    @execution_backend.setter
    def execution_backend(self, val):
        self._execution_backend = val    
    