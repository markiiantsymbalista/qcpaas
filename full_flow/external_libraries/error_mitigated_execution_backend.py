from full_flow.runtime_sdk.enriched_execution_backend import EnrichedExecutionBackend
from mitiq import zne, ddd
from mitiq.interface.mitiq_qiskit.qiskit_utils import initialized_depolarizing_noise

class ErrorMitigatedExecutionBackend(EnrichedExecutionBackend):
    def __init__(self):
        self.noise_level=0.0000001
    
    def execute(self, circuit, shots, **kwargs):
        noise_model = initialized_depolarizing_noise(noise_level=self.noise_level)
        executor = self.execution_backend.get_executor(noise_model, shots)
        
        return self.ddd_combined_with_zne(circuit, executor)
    
    def ddd_combined_with_zne(self, circuit, executor) -> float:
        transpiled_circuit = self.execution_backend.transpile_circuit(circuit)
        scale_factors = [1.0, 3.0, 5.0]
        noise_scaled_circuits = [zne.scaling.fold_gates_at_random(transpiled_circuit, s) for s in scale_factors]

        #start ddd
        rule = ddd.rules.yy
        ddd_mitigated_values = [ddd.execute_with_ddd(circuit=c, executor=executor, rule=rule) for c in noise_scaled_circuits]
        #end ddd

        #assuming an infinite noise limit of 0.5
        fac = zne.inference.ExpFactory(scale_factors, asymptote=0.5)
        for s, e in zip(scale_factors, ddd_mitigated_values):
            fac.push({"scale_factor": s}, e)
        reduced_result = fac.reduce()
        #error mitigation end
        
        return reduced_result