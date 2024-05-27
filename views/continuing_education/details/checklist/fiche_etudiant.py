# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.views.generic import FormView

from admission.forms.admission.continuing_education.checklist import (
    StudentReportForm,
)
from admission.views.common.mixins import AdmissionFormMixin
from admission.views.continuing_education.details.checklist.base import CheckListDefaultContextMixin
from base.utils.htmx import HtmxPermissionRequiredMixin

__namespace__ = False

__all__ = [
    'FicheEtudiantFormView',
]


class FicheEtudiantFormView(CheckListDefaultContextMixin, AdmissionFormMixin, HtmxPermissionRequiredMixin, FormView):
    name = 'fiche-etudiant'
    urlpatterns = 'fiche-etudiant'
    template_name = 'admission/continuing_education/includes/checklist/fiche_etudiant_form.html'
    htmx_template_name = 'admission/continuing_education/includes/checklist/fiche_etudiant_form.html'
    permission_required = 'admission.change_checklist'
    form_class = StudentReportForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.admission
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
