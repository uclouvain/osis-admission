# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

__all__ = [
    "OutilDeComparaisonEtFusionView",
    "RefuserPropositionFusionHtmxView",
    "ParcoursAnterieurHtmxView",
]

from django.urls import reverse

from admission.utils import get_cached_general_education_admission_perm_obj
from gestion_des_comptes.views.outil_de_comparaison_et_fusion import \
    RefuserPropositionFusionHtmxView as RefuserPropositionFusionHtmxMixinView, \
    OutilDeComparaisonEtFusionView as OutilDeComparaisonEtFusionMixinView, \
    ParcoursAnterieurHtmxView as ParcoursAnterieurHtmxMixinView


class OutilDeComparaisonEtFusionView(OutilDeComparaisonEtFusionMixinView):
    urlpatterns = {
        'outil-comparaison-et-fusion': 'outil_comparaison_et_fusion/<uuid:uuid>'
    }
    permission_required = "admission.merge_candidate_with_known_person"

    @property
    def matricule(self) -> str:
        return self.get_permission_object().candidate.global_id

    def get_parcours_anterieur_subtab_url(self) -> str:
        return reverse('admission:services:gestion-des-comptes:parcours-anterieur', kwargs=self.kwargs)

    def get_refuser_fusion_url(self) -> str:
        return reverse(
            'admission:services:gestion-des-comptes:refuser-proposition-fusion',
            kwargs=self.kwargs,
        )

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])


class ParcoursAnterieurHtmxView(ParcoursAnterieurHtmxMixinView):
    urlpatterns = {
        'parcours-anterieur': 'parcours_anterieur/<uuid:uuid>'
    }
    permission_required = "admission.merge_candidate_with_known_person"

    @property
    def matricule(self) -> str:
        return self.get_permission_object().candidate.global_id

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])


class RefuserPropositionFusionHtmxView(RefuserPropositionFusionHtmxMixinView):
    urlpatterns = {
        'refuser-proposition-fusion': 'refuser_proposition_fusion/<uuid:uuid>'
    }
    permission_required = "admission.merge_candidate_with_known_person"

    @property
    def matricule(self) -> str:
        return self.get_permission_object().candidate.global_id

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])
