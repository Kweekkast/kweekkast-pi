class Reading:
    def __init__(self, message: str = "", valid: bool = False):
        self.message = message
        self.valid = valid

    def __repr__(self) -> str:
        return f"Reading(message={self.message!r}, valid={self.valid})"
