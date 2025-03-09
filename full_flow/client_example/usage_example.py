from full_flow.runtime_sdk.runtime_provider import RuntimeProvider
from full_flow.runtime_sdk.runtime_plugin_resolver import RuntimePluginResolver
from qml_example_worker import QmlExampleWorker
from full_flow.external_libraries.qiskit_execution_backend import QiskitExecutionBackend

if __name__ == "__main__":
    
    #docker example run
    runtime_provider = RuntimeProvider() 
    try:
        result = runtime_provider.schedule("qml_example_worker")
        print(result)
    except Exception as error:
        print(f"Error happened when executing program: {error}")

    #local example run without containers.
    # example_worker = QmlExampleWorker()
    # qiskit_execution_backend = QiskitExecutionBackend(example_worker.backend_name)
    # execution_options = ['DddMitigatedExecutionBackend', 'ZneMitigatedExecutionBackend', 'CustomPipelineStep'] 
    # resolver = RuntimePluginResolver()
    # resolver.resolve(execution_options, qiskit_execution_backend, example_worker)
    # example_worker.run()