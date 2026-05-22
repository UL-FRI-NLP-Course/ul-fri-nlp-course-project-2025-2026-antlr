import math

from transformers import logging, pipeline


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
            device_map=self.params.torch_device,
        )

    def get_response(self, messages, temperature=None):
        temp = self.params.temperature
        lowest_temp = 0.001
        if temperature is not None:
            temp = temperature  # use different temperature
            if temperature > 1.0:
                print(
                    "[warn] GaMS.get_response: temperature value larger than 1.0, using 1.0."
                )
                temp = 1.0
            if math.isclose(temperature, 0.0) or temperature < 0.0:
                print(
                    "[warn] GaMS.get_response: temperature value smaller than 0.0 or equal to 0.0, using lowest_temp value (%.3f)."
                    % lowest_temp
                )
                temp = lowest_temp

        response = self.pline(
            messages,
            max_new_tokens=self.params.max_new_tokens,
            do_sample=True,
            temperature=temp,
        )
        return response


# gams params
class GaMSParams:
    def __init__(self):
        self.model_id = "GaMS-Beta/GaMS-9B-Instruct-Nemotron"
        self.torch_device = "cuda"
        self.max_new_tokens = 512
        self.temperature = 0.1
