class UnsupportedSpecificationSchemaError(ValueError):
    pass


class SpecificationHashCollisionError(RuntimeError):
    pass


class ArtifactIdentityConflictError(RuntimeError):
    pass


class ExecutionIdentityConflictError(RuntimeError):
    pass


class InvalidExecutionTransitionError(RuntimeError):
    pass


class InvalidLineageLinkError(ValueError):
    pass
