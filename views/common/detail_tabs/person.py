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
from django.utils.translation.trans_real import get_languages
from django.views.generic import TemplateView

from admission.views.common.mixins import LoadDossierViewMixin

__all__ = ['AdmissionPersonDetailView']

from base.models.person_merge_proposal import PersonMergeProposal
from osis_common.utils.models import get_object_or_none


class AdmissionPersonDetailView(LoadDossierViewMixin, TemplateView):
    permission_required = 'admission.view_admission_person'
    template_name = 'admission/details/person_backoffice.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['person'] = self.admission.candidate
        context['contact_language'] = get_languages().get(self.admission.candidate.language)
        if self.is_doctorate and 'dossier' in context:
            context['profil_candidat'] = context['dossier'].profil_soumis_candidat
        elif self.is_general:
            context['profil_candidat'] = context['admission'].profil_soumis_candidat
        return context
