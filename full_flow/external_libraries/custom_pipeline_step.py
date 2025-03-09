from full_flow.runtime_sdk.enriched_execution_backend import EnrichedExecutionBackend

class CustomPipelineStep(EnrichedExecutionBackend):    
    def execute(self, circuit, shots, **kwargs):
        #part of pattern implementation. We could write a rule that ensures that for every plugin it gets executed.n
        self.execute_linked_plugin(circuit, shots, **kwargs)
        
        #we could basically do anything we desire here with a circuit and with results of previous runs. 
        # pipelien design implemented here allows to apply several complementary steps, combining results 
        # from previous steps and manipulate cicuit in any desired way.
        
        #showing example of how to work with custom parameters passed from a client
        print("Received keyword arguments:")
        for key, value in kwargs.items():
            print(f"{key}: {value}")
            
        #showing example of how to access shared state from previous runs and manipulating them in a custom way.
        # right now were just recording results of zne step in a raw form. 
        # of course data structure of the state could be adjusted as needed. right now it is done only for example purposes.
        for state_value in self.state:
             print(f"previous result state - {state_value}")
        
        #simply return value of zne of previous step.
        return self.state[-1]