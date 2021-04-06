try:
    from .doctorate import AdmissionDoctorate
    from .enums.admission_type import AdmissionType

    __all__ = [
        "AdmissionDoctorate", "AdmissionType"
    ]

except RuntimeError as e:  # pragma: no cover
    # There's a weird bug when running tests, the test runner seeing a models
    # package tries to import it directly, failing to do so
    import sys

    if 'test' not in sys.argv:
        raise e
