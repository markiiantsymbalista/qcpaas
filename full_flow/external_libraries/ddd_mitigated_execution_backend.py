from full_flow.runtime_sdk.enriched_execution_backend import EnrichedExecutionBackend
from mitiq import ddd
from mitiq.interface.mitiq_qiskit.qiskit_utils import initialized_depolarizing_noise

class DddMitigatedExecutionBackend(EnrichedExecutionBackend):
    def __init__(self):
        self.noise_level=0.0000001
    
    def execute(self, circuit, shots, **kwargs):
        #part of pattern implementation. We could write a rule that ensures that for every plugin it gets executed.n
        self.execute_linked_plugin(circuit, shots, **kwargs)
        
        transpiled_circuit = self.execution_backend.transpile_circuit(circuit)
        
        noise_model = initialized_depolarizing_noise(noise_level=self.noise_level)
        executor = self.execution_backend.get_executor(noise_model, shots)
        
        rule = ddd.rules.yy
        return ddd.execute_with_ddd(circuit=transpiled_circuit, executor=executor, rule=rule)