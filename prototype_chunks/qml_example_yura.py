import sys
import math
from functools import partial
import numpy as np
import itertools
import qiskit
from qiskit.providers import fake_provider
import qiskit.circuit.library as qiskit_library
from qiskit.algorithms import optimizers
from qiskit_aer import AerSimulator
from qiskit import transpile

import matplotlib.pyplot as plt



def plot(name, y_arr, names):
    colors = "bgryk"
    fig, ax = plt.subplots()
    x = range(len(y_arr[0]))
    for i in range(len(y_arr)):
        ax.plot(x, y_arr[i], label=names[i], markersize=2, color=colors[i])
    ax.legend()
    # plt.close()
    plt.savefig(f"{name}.png")


def slise(circ, s, e):
    slice_layer = qiskit.QuantumCircuit(circ.num_qubits)
    for i in range(len(circ.data)):
        if s <= i < e:
            slice_layer.append(circ.data[i][0], circ.data[i][1], circ.data[i][2])

    return slice_layer


def get_probs(circut, simulator=None):
    circut = circut.copy()
    circut.measure_all()
    shots = 2**13
    n_qubits = circut.num_qubits

    if simulator is None:
        simulator = AerSimulator()

    circut = transpile(circut, simulator, optimization_level=3)
    res = simulator.run(circut, shots=shots).result()
    counts = res.get_counts(circut)

    probs = [
        counts.get(format(x, f'0{n_qubits}b'), 0)/shots
        for x in range(2**n_qubits)
    ]

    return probs


class Loss:
    def __init__(
            self,
            n_qubits,
            circut, 
            simulator,
            base_name, 
            teacher, 
            student,
            patience=1000,
            min_diff=0.01,
        ):
        self.simulator = simulator
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



    def log_figure(self, i, x0):
        y_true_ideal = get_probs(self.teacher)
        y_true_noise = get_probs(self.teacher, simulator = self.simulator)
        bind_student = self.student.bind_parameters(x0)
        y_pred_noise = get_probs(bind_student, simulator = self.simulator)

        plot(
            f"{self.base_name}_probs_iter_{i:05d}",
            (y_true_ideal, y_true_noise, y_pred_noise),
            ("Ideal teacher", "Noisy teacher", "Predictions")
        )


    def __call__(self, x):
        n_evals = next(self.n_evals)

        circut = self.circut.bind_parameters(x)

        res = self.simulator.run(circut, shots=self.shots).result()
        counts = res.get_counts(circut)
        zero_prob = counts.get("0"*self.n_qubits, 0)/self.shots
        loss = 1 - zero_prob

        if self.best_loss - loss >= self.min_diff:
            self.best_loss = loss
            self.best_w = x
            self.no_improvement_counter = 0
        else:
            self.no_improvement_counter += 1

        if n_evals % 10 == 0:
            print(n_evals, "loss", self.best_loss)

        if n_evals % 100 == 0:
            self.log_figure(n_evals, self.best_w)

        if self.no_improvement_counter >= self.patience:
            print(f"not improved for {self.patience} evals")
            self.log_figure(n_evals, self.best_w)
            raise StopIteration()

        return loss



def get_train_layer_general(name, n_qubits, n_layers, entanglement):
    return qiskit_library.EfficientSU2(
        n_qubits, 
        reps=n_layers, 
        entanglement=entanglement, 
        name=name,
    )

def get_wave(n_qubits):
    num_samples = 2**n_qubits
    t = np.linspace(0, 2*np.pi, num_samples)
    a = num_samples//7
    b = num_samples//4
    wave = np.sin(a*t) + np.sin(b*t)
    wave = wave / np.sqrt(np.sum(wave**2))
    return wave

if __name__ == "__main__":
    backend = getattr(fake_provider, "FakeKolkata")()
    simulator = AerSimulator.from_backend(backend)


    n_qubits = 5
    wave = get_wave(n_qubits)
    teacher = qiskit.QuantumCircuit(n_qubits)
    teacher.append(qiskit_library.StatePreparation(wave), range(n_qubits))
    teacher.append(qiskit_library.QFT(n_qubits), range(n_qubits))
    teacher = transpile(
        teacher,
        basis_gates=["rx", "ry", "rz", "cx"]
    )

    get_train_layer = partial(
        get_train_layer_general,
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

        teacher_part = slise(teacher, s, e)
        model.append(teacher_part, range(n_qubits))
        train_layer = get_train_layer("train")
        model.append(train_layer.inverse(), range(n_qubits))
        model.measure_all()

        model = transpile(model, simulator, optimization_level=3)

        opt = optimizers.NFT(
            maxiter=9009999,
            maxfev =9999999,
        )

        print(f"model_{s}_{e}_depth", model.depth())

        loss_f = Loss(
            n_qubits=n_qubits,
            circut=model,
            simulator=simulator,
            base_name=f"iter-{s:04d}-{e:04d}",
            teacher=slise(teacher, 0, e),
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
        gate_start += step

