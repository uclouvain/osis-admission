# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.contrib import messages
from django.db import transaction
from django.forms import Form
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url, redirect
from django.utils.translation import gettext
from django.views import View
from django.views.generic import FormView

from admission.models.base import BaseAdmission
from admission.models.exam import AdmissionExam
from admission.views.common.mixins import LoadDossierViewMixin, AdmissionViewMixin, AdmissionFormMixin
from ddd.logic.shared_kernel.profil.domain.enums import TypeExperience
from osis_profile.models import ExamType, Exam
from osis_profile.models.education import HighSchoolDiploma


__all__ = [
    'InitializeExperienceView',
]

class InitializeExperienceView(AdmissionViewMixin, View):
    """Initialize the experience if it doesn't yet exist."""
    urlpatterns = {
        'initialize-experience': 'initialize-experience/<str:experience_type>'
    }
    permission_required = 'admission.change_checklist'
    template_name = 'admission/empty_template.html'

    def post(self, request, *args, **kwargs):
        admission: BaseAdmission = self.admission
        created_experience: HighSchoolDiploma | Exam | None = None

        if self.kwargs['experience_type'] == TypeExperience.ETUDES_SECONDAIRES.name:
            if not hasattr(admission.candidate, 'highschooldiploma'):
                created_experience = HighSchoolDiploma.objects.create(person=admission.candidate)

        elif self.kwargs['experience_type'] == TypeExperience.EXAMEN.name:
            if not hasattr(admission, 'exam'):
                exam_type = ExamType.objects.filter(education_group_years=admission.training).first()
                if exam_type:
                    with transaction.atomic():
                        created_experience = Exam.objects.create(person=admission.candidate, type=exam_type)
                        AdmissionExam.objects.create(exam=created_experience, admission=admission)

        if created_experience:
            messages.success(self.request, gettext('The experience has been initialized'))
            url_suffix = f'#parcours_anterieur__{created_experience.uuid}'
        else:
            url_suffix = "#parcours_anterieur"

        return HttpResponseRedirect(
            resolve_url(f'{self.base_namespace}:checklist', uuid=self.admission_uuid) + url_suffix,
        )