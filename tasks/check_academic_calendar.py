from admission.calendar.admission_calendar import *
from backoffice.celery import app as celery_app


@celery_app.task
def run() -> dict:
    DoctorateAdmissionCalendar.ensure_consistency_until_n_plus_6()
    GeneralEducationAdmissionCalendar.ensure_consistency_until_n_plus_6()
    ContinuingEducationAdmissionCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolExternalEnrollmentChangeCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolExternalReorientationCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolVipCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolHueUclPathwayChangeCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolInstituteChangeCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolUe5BelgianCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolUe5NonBelgianCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolHue5BelgiumResidencyCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolHue5ForeignResidencyCalendar.ensure_consistency_until_n_plus_6()
    AdmissionPoolNonResidentQuotaCalendar.ensure_consistency_until_n_plus_6()
    return {}
