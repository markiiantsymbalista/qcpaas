# runtime end to end flow.

Code for the runtime is located in the folder full_flow. Also, there are docker configurations that reside in the parent directory.
Platform allows to execute arbitrary workloads with maximum flexibility. 
prototype_chunks are files with separate different tries of creating QML cases and cases with mitiq.

# debugging
To run test we need to start app 3 apps separately. 
Order of run:
1. worflow-manager (debug choosing Docker: workflow-manager configuration from vs code dropdown)
2. worker (debug choosing Docker: worker configuration from vs code dropdown)
3. usage_example (debug choosing Python: Current File configuration from vs code dropdown) - this is a test script that uses qml_example_worker and runtime_sdk to run workload.

requirements:
-Docker should be installed locally and daemon run.
-VS code should be installed.

Code is developed in VS code, so all debug launch configurations are provided for you in .vscode folder.
Every service can be debugged seperately either in docker mode or without it.


# runtime_sdk
is used by client app of a user that wants to execute a payload. contains http client that interacts with workflow_manager on the conceptually remote runtime. contains RuntimeWorkerBase which is a base class that all workloads should inherit from as it provides generic run() method that runtime uses to execute worklaods. RuntimeProvider when used from the client (client provides class name with a logic inherited from RuntimeWorkerBase), converts python class to a string and retrieves all required modules. Sents this data to workflow manager which decides whether there is a worker that could satisfy workload.

# runtime_server module
has two fastapi services inside (they basically constitute runtime itself/not considering programming model):

# 1. workflow_manager
responsible for receiving a program input, looking for a worker from the pool that could satisfy required libraries to execute request and pass it to worker within a separate container with a fastapi app that will execute it. 

# 2. worker 
service that is running in a container that has qiskit, and other required libraries installed. when worker starts it registers itself with workflow_manager providing info about supported libraries/frameworks. 

# client_example 
has QmlExampleWorker class which we want to execute remotely. it uses runtime_sdk to pass workload to remote server.

# notice
code is created without adhering to style guidelines with hardcoded string and poor structuring as for the prototype purposes. don't pay much attention, it will be refactored on further stages. what is more important are components and their interections. 


# done 

Implemented Plugin architecture around ExecutionBackend class. QiskitBackend inherits from it (wraps logic for accessing hardware provider). EnrichedExecutionBackend also inherits from ExecutionBacked and also aggregates it. It is a core pillar as it allows to create pre or post processing logic around circuit execution backend, pretty much arbitrary. As an example to test it in action, ErrorMitigatedExecutionBackend is created that uses mitiq to implement custom EM strategy DDD+ZNE. So, by default runtime executes circuits in regular manner, but if user passes an option "em_type":"" during initialization of QMLExampleWorker class (line 73), runtime discovers "custom_zne_ddd" which is a name of EM plugin that wraps QiskitBackend inside of it.

This plugin structure design enables our main use case for implementing hidden/proprietory logic outside user code. It could be anything like custom optimization, em, mostly all scenarios that we planned. Also, it allows combining different plugings together in a customizable pipeline that could be configured from options. 

# next steps

In the end we want the following flow:
1. As a runtime host, I want to add proprietary optimization/em to improve quality of computations.
2. Based on core image for let's say qiskit as in our case (it could also be pennylane or other SDKs) runtime host creates new images based on it with it's custom code. Container/Worker with this code get's deployed. There are specific rules how to expose and use additional functionality. (not implemented yet)
3. Runtime discovers pluging functionality as it self registers. 
4. User pulls dsicovery endpoint to get metadata about vitamin functionality. 
5. User passes an option to use.
6. Runtime sees the option that registers particular plugin for execution. (not implemented yet.)

So, based on the flow above next steps for runtime enhacements are described below:
1. Implement endpoint that allows to get plugin options using SDK.
2. Move EM adapter in some separate library (move out of SDK) in a separate library. Create container image based on that library. BYOC.
4. Adapter should register itself upon startup to share option type and other metadata.
5. Runtime dynamically attaches adapter to general execution flow based on provided options.

# Notes:
@Vlad, I still believe that passing classical+quantum code is better, because it doesn't limit us in options what we could do with it. Take as an example even our QML case. We can't pass classical code via QASM, it doesn't make sense. We want to pass it together and do optimization on GPU with CUDe for example and run quantum code on hardware as part of one runtime cycle. We don't want to do optimization on client and running quantum on runtime, aren't we? More over complex cases of hybrid algortihms require proximity. That is why we need to pass all the code not only quantum. 

Interfaces for using functionality could be adjusted. It is not core priority. 

# Update 
1. Dynamic plugin auto resolver implementation. Allows anyone to bring library, custom container and deploy it as a pipeline step that will be auto resolved based on a name of a plugin. - Done.
2. Batch implementation. - Done. It boils down to implementation in qiskit back-end. Mitiq adjusts to batch process if executor is present. batch=True is passed in zne pipeline for example. It simplified form of course that doesn't consider scheduling and capacity features.
3. Passing arguments. - Done. It is done from qml example worker by directly passing kwargs that could be retrieved from particular decorate. CustomPipelineStep shows to retrieve params in plugin.
4. How to communicate data between modules. - Done. CustomPipelineStep shows example. Each pipeline step could record both results and arbitrary state that is shared between all pipeline steps. 
5. Change interface in stead of sequential use combination explicit. It doesn’t make sense because we want to hide implementation details. If we will allow directly to manipulate classes creation it will mean, that we could get into the implementation details, so we should hide it anyway. So, based on that it wasn't implemented. Approach ['DddMitigatedExecutionBackend', 'ZneMitigatedExecutionBackend', 'CustomPipelineStep']  is left.
6. Show indépendance of elements. zne + ddd - Done. The questions is whether how we want to use it. Somehow approximate results of both in CustomPipelineStep and return result based on that?
7. Two execution pipelines together. - Done. ddd and after zne.

Not implemented. Unfortunetaly lacked time in this iteration to do it.
8. Sockey logging. Intermediate results.  Json not raw strong.
9. Error handling pipeline how to propagate error. - Add EH on the plugin level. Propagate error through shared state. 


