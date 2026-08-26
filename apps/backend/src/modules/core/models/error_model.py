class UnsupportedSpecificationSchemaError(ValueError):
    pass


class SpecificationHashCollisionError(RuntimeError):
    pass


class ArtifactIdentityConflictError(RuntimeError):
    pass
