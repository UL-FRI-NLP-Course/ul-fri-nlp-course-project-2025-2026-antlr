from transformers import pipeline, logging

# logging.set_verbosity_debug() # uncomment to make transformers more verbose

# model superclass (each model should implement this)
class LLModel:
    def __init__(self, params):
        self.params = params
    
    # abstract method
    def get_response(self, message):
        raise NotImplementedError

# gams
class GaMS(LLModel):
    def __init__(self):
        super().__init__(GaMSParams())
        print("init GaMS model")
        # init pipeline
        self.pline = pipeline(
            "text-generation",
            model=self.params.model_id,
            device_map=self.params.torch_device
        )
    
    def get_response(self, messages):
        response = self.pline(messages, max_new_tokens=self.params.max_new_tokens)
        return response

# gams params
class GaMSParams:
    def __init__(self):
        self.model_id = "GaMS-Beta/GaMS-9B-Instruct-Nemotron"
        self.torch_device = "cuda" # "cpu" # <- cpu takes forever
        self.max_new_tokens=512



