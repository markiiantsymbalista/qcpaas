import qiskit
from full_flow.runtime_sdk.execution_backend import ExecutionBackend
from qiskit.providers import fake_provider
from qiskit_aer import AerSimulator
from qiskit import transpile
from qiskit import QuantumCircuit
from typing import List
class QiskitExecutionBackend(ExecutionBackend):    
    def __init__(self, backend_name):
        provider = getattr(fake_provider, backend_name)()
        self._backend = AerSimulator.from_backend(provider)
        self.n_qubits = 5 # hardcoded.
    
    def execute(self, circuit, shots, **kwargs):
        tranpiled_circuit = transpile(circuit, self.backend, optimization_level=3)
        run_res = self._backend.run(tranpiled_circuit, shots=shots)
        res = run_res.result()
        counts = res.get_counts(circuit)
        
        return counts.get("0"*self.n_qubits, 0)/shots
    
    def transpile_circuit(self, circuit):
        return transpile(circuit, self.backend, optimization_level=3)
    
    def get_executor(self, noise_model, shots, batch=False):
        def executor(circuit: QuantumCircuit) -> float:
            job = qiskit.execute(
                experiments=circuit,
                backend=self.backend,
                noise_model=noise_model,
                basis_gates=noise_model.basis_gates,
                optimization_level=0,# Important to preserve folded gates.
                shots=shots,
            )
            counts = job.result().get_counts()

            result = counts.get("0"*self.n_qubits, 0)/shots
            
            return result
        
        def batch_executor(circuits: List[QuantumCircuit]) -> List[float]:
            job = qiskit.execute(
                experiments=circuits,
                backend=self.backend,
                noise_model=noise_model,
                basis_gates=noise_model.basis_gates,
                optimization_level=0,# Important to preserve folded gates.
                shots=shots,
            )
            counts = job.result().get_counts()

            result: List[float] = []
            for count in counts:
                result.append(count.get("0"*self.n_qubits, 0)/shots)
            
            return result
        
        if(batch):
            return batch_executor
        else:
            return executor
        

        