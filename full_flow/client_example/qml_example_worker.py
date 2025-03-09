from full_flow.runtime_sdk.runtime_worker_base import RuntimeWorkerBase

import sys
from functools import partial
import numpy as np
import itertools
import qiskit
import qiskit.circuit.library as qiskit_library
from qiskit.algorithms import optimizers
from qiskit import transpile

number_of_shots = 2**13
n_qubits = 5

class Loss:
    def __init__(
            self,
            n_qubits,
            circut, 
            executor,
            base_name, 
            teacher, 
            student,
            patience=1000,
            min_diff=0.01,
        ):
        self.executor = executor
        self.shots = 2**13
        self.n_qubits = n_qubits
        self.circut = circut

        self.base_name = base_name
        self.teacher = teacher
        self.student = student

        self.n_evals = itertools.count()
        self.best_loss = sys.maxsize
        self.best_w = None

        self.patience = patience
        self.min_diff = min_diff
        self.no_improvement_counter = 0

    def __call__(self, x):
        n_evals = next(self.n_evals)

        circut = self.circut.bind_parameters(x)
        
        #examples shows passing arbitratry params for illustration purposes.
        res = self.executor.execute(circut, self.shots, example_param="example_value")
       
        loss = 1 - res

        if self.best_loss - loss >= self.min_diff:
            self.best_loss = loss
            self.best_w = x
            self.no_improvement_counter = 0
        else:
            self.no_improvement_counter += 1

        if n_evals % 10 == 0:
            print(n_evals, "loss", self.best_loss)

        if self.no_improvement_counter >= self.patience:
            print(f"not improved for {self.patience} evals")
            raise StopIteration()

        return loss

class QmlExampleWorker(RuntimeWorkerBase):
    def __init__(self):
        # think of better way how to set it
        self.backend_name = "FakeKolkata"
        self.execution_options = ['DddMitigatedExecutionBackend', 'ZneMitigatedExecutionBackend', 'CustomPipelineStep'] 
        
    def slise(self, circ, s, e):
        slice_layer = qiskit.QuantumCircuit(circ.num_qubits)
        for i in range(len(circ.data)):
            if s <= i < e:
                slice_layer.append(circ.data[i][0], circ.data[i][1], circ.data[i][2])

        return slice_layer
    
    def get_train_layer_general(self, name, n_qubits, n_layers, entanglement):
        return qiskit_library.EfficientSU2(
            n_qubits, 
            reps=n_layers, 
            entanglement=entanglement, 
            name=name,
        )

    def get_wave(self, n_qubits):
        num_samples = 2**n_qubits
        t = np.linspace(0, 2*np.pi, num_samples)
        a = num_samples//7
        b = num_samples//4
        wave = np.sin(a*t) + np.sin(b*t)
        wave = wave / np.sqrt(np.sum(wave**2))
        return wave
    
    
    def run(self):
        print("Running worker class")
        
        wave = self.get_wave(n_qubits)
        teacher = qiskit.QuantumCircuit(n_qubits)
        teacher.append(qiskit_library.StatePreparation(wave), range(n_qubits))
        teacher.append(qiskit_library.QFT(n_qubits), range(n_qubits))
        teacher = transpile(
            teacher,
            basis_gates=["rx", "ry", "rz", "cx"]
        )

        get_train_layer = partial(
            self.get_train_layer_general,
            n_qubits=n_qubits,
            n_layers=4,
            entanglement="linear",
        )

        base_weights = None
        step = 100
        gate_start = 0
        while gate_start < len(teacher):
            s = gate_start
            e = gate_start + step
            model = qiskit.QuantumCircuit(n_qubits)
            if base_weights is not None:
                # print("Add base weights")
                base_layer = get_train_layer("base")
                model.append(base_layer, range(n_qubits))
                weights_dict = dict(zip(model.parameters, base_weights))
                model = model.bind_parameters(weights_dict)

            teacher_part = self.slise(teacher, s, e)
            model.append(teacher_part, range(n_qubits))
            train_layer = get_train_layer("train")
            model.append(train_layer.inverse(), range(n_qubits))
            model.measure_all()

            opt = optimizers.NFT(
                maxiter=9009999,
                maxfev =9999999,
            )

            print(f"model_{s}_{e}_depth", model.depth())

            loss_f = Loss(
                n_qubits=n_qubits,
                circut=model,
                executor=self,
                base_name=f"iter-{s:04d}-{e:04d}",
                teacher=self.slise(teacher, 0, e),
                student=train_layer,
                patience=400,
                min_diff=0.001,
            )

            x0 = 2 * np.pi * (np.random.rand(model.num_parameters) - 0.5)
            try:
                opt.minimize(fun=loss_f, x0=x0)
            except StopIteration as e:
                print("finished itreation training")

            base_weights = loss_f.best_w
            self.result = ', '.join(map(str, base_weights)) if base_weights is not None else "Array is None"
            print(f"Weights: {self.result}")
            gate_start += step