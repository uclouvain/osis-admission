# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from django.db import transaction
from django.utils.functional import cached_property

from admission.models import EPCInjection as AdmissionEPCInjection
from admission.models.epc_injection import (
    EPCInjectionStatus as AdmissionEPCInjectionStatus,
)
from admission.models.epc_injection import EPCInjectionType
from admission.models.exam import AdmissionExam
from admission.views.common.mixins import AdmissionFormMixin, LoadDossierViewMixin
from osis_profile.models import Exam, ExamType
from osis_profile.models.epc_injection import EPCInjection as CurriculumEPCInjection
from osis_profile.models.epc_injection import (
    EPCInjectionStatus as CurriculumEPCInjectionStatus,
)
from osis_profile.models.epc_injection import ExperienceType
from osis_profile.views.edit_examen import EditExamenView

__all__ = [
    'ExamFormView',
]



class ExamFormView(AdmissionFormMixin, LoadDossierViewMixin, EditExamenView):
    urlpatterns = 'exam'
    template_name = 'admission/forms/exams.html'
    permission_required = 'admission.change_admission_exam'


    def traitement_specifique(self):
        pass

    def has_permission(self):
        return super().has_permission() and self.can_be_updated

    def get_success_url(self):
        return self.next_url or self.request.get_full_path()

    @property
    def can_be_updated(self):
        admission_injections = AdmissionEPCInjection.objects.filter(
            admission__candidate_id=self.admission.candidate.pk,
            type=EPCInjectionType.DEMANDE.name,
            status__in=AdmissionEPCInjectionStatus.blocking_statuses_for_experience(),
        )
        cv_injections = CurriculumEPCInjection.objects.filter(
            person_id=self.admission.candidate.pk,
            type_experience=ExperienceType.HIGH_SCHOOL.name,
            status__in=CurriculumEPCInjectionStatus.blocking_statuses_for_experience(),
        )

        return not (self.exam_type is None or cv_injections.exists() or admission_injections.exists())

    @cached_property
    def exam_type(self):
        return ExamType.objects.filter(education_group_years=self.admission.training).first()

    @cached_property
    def exam(self):
        return Exam.objects.filter(admissions__admission=self.admission).first()

    @property
    def person(self):
        return self.admission.candidate

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        exam = form.instance
        AdmissionExam.objects.get_or_create(
            admission=self.admission,
            exam=exam,
        )
        return response
