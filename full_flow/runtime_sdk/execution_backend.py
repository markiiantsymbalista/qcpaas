class ExecutionBackend:
    _state = []
    
    def __init__(self):
        self._backend = None
    
    @property
    def state(self):
        return self._state
    
    @state.setter
    def set_state(self, val):
        self._state.append(val)
    
    @property
    def backend(self):
        return self._backend
    
    @backend.setter
    def backend_name(self, val):
        self._backend = val
    
    def execute(self, circuit, shots, **kwargs):
        raise NotImplementedError("Subclasses must implement the 'execute' method")
    
    def get_executor(self, noise_model, shots, batch=False):
        raise NotImplementedError("Subclasses must implement the 'get_executor' method")
    
    def transpile_circuit(self, circuit):
        raise NotImplementedError("Subclasses must implement the 'transpile_circuit' method")

    