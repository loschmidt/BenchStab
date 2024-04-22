class _BaseError(Exception):
    def __init__(
            self, *args: object, **kwargs: object
    ) -> None:
        self.permissive = kwargs.pop('permissive', False)
        super().__init__(*args)


class HTMLParserError(_BaseError):
    pass


class PreprocessorError(_BaseError):
    pass


class PredictorError(_BaseError):
    pass


class DatasetError(_BaseError):
    pass


class BenchStabError(_BaseError):
    pass
