from admission.calendar.admission_calendar import (
    DoctorateAdmissionCalendar,
    GeneralEducationAdmissionCalendar,
    ContinuingEducationAdmissionCalendar,
)
from backoffice.celery import app as celery_app


@celery_app.task
def run() -> dict:
    DoctorateAdmissionCalendar.ensure_consistency_until_n_plus_6()
    GeneralEducationAdmissionCalendar.ensure_consistency_until_n_plus_6()
    ContinuingEducationAdmissionCalendar.ensure_consistency_until_n_plus_6()
    return {}
