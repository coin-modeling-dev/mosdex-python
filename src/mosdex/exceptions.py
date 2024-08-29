class MosdexError(Exception):
    """A base class for exceptions in this module."""

class MosdexInvalidFileError(MosdexError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.invalid_items = kwargs.get("invalid_items")
        self.filename = kwargs.get("filename")


class MosdexInvalidClassKindPairError(MosdexError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.invalid_class = kwargs.get("invalid_class")
        self.name = kwargs.get("name")
        self.kind = kwargs.get("kind")

class MosdexInvalidTableKindPairError(MosdexError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.name = kwargs.get("name")
        self.kind = kwargs.get("kind")
        self.keys = kwargs.get("keys")

class MosdexTableSchemaNotFoundError(MosdexError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.name = kwargs.get("name")
