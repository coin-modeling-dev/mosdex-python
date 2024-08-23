class MosdexError(Exception):
    """A base class for exceptions in this module."""

class MosdexInvalidFileError(MosdexError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.invalid_items = kwargs.get("invalid_items")
        self.filename = kwargs.get("filename")