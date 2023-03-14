# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################

try:
    from .doctorate import DoctorateAdmission, ConfirmationPaper
    from .actor import SupervisionActor
    from admission.ddd.admission.enums.type_demande import TypeDemande
    from .entity_proxy import EntityProxy
    from .cdd_mail_template import CddMailTemplate
    from .task import AdmissionTask
    from .accounting import Accounting
    from .scholarship import Scholarship
    from .continuing_education import ContinuingEducationAdmission, ContinuingEducationAdmissionProxy
    from .general_education import GeneralEducationAdmission, GeneralEducationAdmissionProxy
    from .form_item import AdmissionFormItemInstantiation, AdmissionFormItem
    from .base import AdmissionViewer

    __all__ = [
        "DoctorateAdmission",
        "TypeDemande",
        "SupervisionActor",
        "EntityProxy",
        "CddMailTemplate",
        "ConfirmationPaper",
        "AdmissionTask",
        "Accounting",
        "Scholarship",
        "ContinuingEducationAdmission",
        "ContinuingEducationAdmissionProxy",
        "GeneralEducationAdmission",
        "GeneralEducationAdmissionProxy",
        "AdmissionFormItem",
        "AdmissionFormItemInstantiation",
        "AdmissionViewer",
    ]

except RuntimeError as e:  # pragma: no cover
    # There's a weird bug when running tests, the test runner seeing a models
    # package tries to import it directly, failing to do so
    import sys

    if 'test' not in sys.argv:
        raise e
