from dataclasses import dataclass


@dataclass(eq=False)
class _Status:
    blocking = False
    status: str = ""
    message: str = ""

    def __eq__(self, __value: object) -> bool:
        return __value == self.status

    def __hash__(self) -> int:
        return hash(self.status)

    def __str__(self) -> str:
        return self.status

    def __repr__(self) -> str:
        return self.status


@dataclass(eq=False)
class NotStarted(_Status):
    """
    This status represents the initial state of the job.
    """
    blocking = False
    status: str = "not started"
    message: str = "The job has not started yet."


@dataclass(eq=False)
class Authenticaton(_Status):
    """
    This status represents the that the user is being authenticated to the predictor.
    """
    blocking = True
    status: str = "authentication"
    message: str = "The job is being authenticated."


@dataclass(eq=False)
class Waiting(_Status):
    """
    This status represents that the job is waiting
    in the predictor's queue (in case of POST-GET predictors), or that
    the job is waiting for the response (in case of POST predictors). 
    """
    blocking = True
    status: str = "waiting"
    message: str = "The job is waiting in predictor's queue."


@dataclass(eq=False)
class Processing(_Status):
    """
    This status represents that job has not been queued to the predictor yet,
    but the predictor is processing the payload. It's usually asocciated with
    predictors that require some middle step (e.g., multiple post requests)
    before the job is queued.
    """
    blocking = True
    status: str = "processing"
    message: str = "The job request is being currently processed."


@dataclass(eq=False)
class Finished(_Status):
    """
    This status represents that the job has finished successfully.
    """
    status: str = "finished"
    message: str = "The job has finished successfully."


@dataclass(eq=False)
class Failed(_Status):
    """
    This status represents that the job has failed for unknown (other) reasons.
    It is a good practice to pass the reason for the failure (exception) in the message.
    """
    status: str = "failed"
    message: str = "The job has failed for unknown reasons."


@dataclass(eq=False)
class ParsingFailed(_Status):
    """
    This status represents that the job has failed during data parsing.
    It can be HTML processing or data manipulation - Indexing, slicing, etc.
    It is a good practice to pass the reason for the failure (exception) in the message.
    """
    status: str = "parsing failed"
    message: str = "The job has failed during data parsing."


@dataclass(eq=False)
class ConnectionFailed(_Status):
    """
    This status represents that the job has failed during network communication with the predictor.
    This often means that the predictor is down, the network connection is unstable or that the predictor
    has moved to a different URL.
    """
    status: str = "connection failed"
    message: str = "The job has failed during connection."


@dataclass(eq=False)
class AuthenticationFailed(_Status):
    """
    This status represents failed attempts to authenticate to the predictor. 
    """
    status: str = "authentication failed"
    message: str = "The job has failed during authentication."


@dataclass(eq=False)
class PredictorNotAvailable(_Status):
    """
    This status represents that the predictor is not available.
    """
    status: str = "predictor not available"
    message: str = "The predictor is not available."


@dataclass(eq=False)
class Timeout(_Status):
    """
    This status represents that the job has timed out.
    """
    status: str = "timeout"
    message: str = "The job has timed out."
