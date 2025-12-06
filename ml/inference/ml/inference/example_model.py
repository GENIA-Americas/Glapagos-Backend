"""
Example ML Model for Glápagos Backend
This is a template showing how to structure inference functions.
"""

class ExampleModel:
    def __init__(self):
        # Initialize model parameters or load a pre-trained model
        self.model_name = "ExampleModel"

    def preprocess(self, data):
        """
        Preprocess input data before inference.
        Args:
            data (any): raw input data
        Returns:
            processed_data (any)
        """
        # Placeholder: return data as-is
        return data

    def predict(self, data):
        """
        Make a prediction using the model.
        Args:
            data (any): preprocessed input data
        Returns:
            dict: prediction result
        """
        processed_data = self.preprocess(data)
        # Placeholder prediction
        return {"prediction": "example"}

    def postprocess(self, prediction):
        """
        Postprocess prediction result if needed.
        Args:
            prediction (dict): raw prediction output
        Returns:
            dict: postprocessed result
        """
        return prediction


# Example usage
if __name__ == "__main__":
    model = ExampleModel()
    sample_input = {"input": "test data"}
    result = model.predict(sample_input)
    print("Prediction:", result)
