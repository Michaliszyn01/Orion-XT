class Observation:
    def __init__(self, success: bool, result: str):
        self.success = success
        self.result = result

    def to_dict(self):
        return {
            "success": self.success,
            "result": self.result
        }