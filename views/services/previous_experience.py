# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import contextlib
from types import SimpleNamespace
from typing import Optional

from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from admission.ddd.admission.commands import RechercherParcoursAnterieurQuery, RecupererEtudesSecondairesQuery
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import CurriculumAdmissionDTO
from admission.ddd.admission.dtos import EtudesSecondairesAdmissionDTO
from admission.templatetags.admission import format_matricule
from admission.utils import get_cached_general_education_admission_perm_obj
from base.models.person import Person
from base.models.person_merge_proposal import PersonMergeProposal
from base.utils.htmx import HtmxPermissionRequiredMixin
from ddd.logic.shared_kernel.profil.dtos.etudes_secondaires import DiplomeBelgeEtudesSecondairesDTO, \
    DiplomeEtrangerEtudesSecondairesDTO, AlternativeSecondairesDTO
from infrastructure.messages_bus import message_bus_instance
from osis_common.utils.htmx import HtmxMixin

__all__ = [
    "SearchPreviousExperienceView",
]

from osis_profile.models.enums.education import ForeignDiplomaTypes


class SearchPreviousExperienceView(HtmxMixin, HtmxPermissionRequiredMixin, TemplateView):
    name = "search_previous_experience"

    template_name = "admission/previous_experience.html"
    htmx_template_name = "admission/previous_experience.html"
    urlpatterns = {'previous-experience': 'previous-experience/<uuid:admission_uuid>'}
    permission_required = "admission.merge_candidate_with_known_person"

    @cached_property
    def candidate(self):
        # retrieve using DDD
        return Person.objects.values(
            'first_name', 'middle_name', 'last_name', 'email', 'gender', 'birth_date', 'civil_state',
            'birth_place', 'country_of_citizenship__name', 'national_number', 'id_card_number',
            'passport_number', 'last_registration_id', 'global_id',
        ).get(baseadmissions__uuid=self.kwargs['admission_uuid'])

    @cached_property
    def person_merge_proposal(self):
        # retrieve using DDD
        return PersonMergeProposal.objects.select_related('original_person').get(
            original_person__global_id=self.candidate['global_id']
        )

    @cached_property
    def curriculum_candidat(self) -> CurriculumAdmissionDTO:
        return message_bus_instance.invoke(
            RechercherParcoursAnterieurQuery(
                global_id=self.candidate['global_id'],
                uuid_proposition=self.request.GET.get('admission_uuid')
            )
        )

    @cached_property
    def etudes_secondaires_candidat(self) -> EtudesSecondairesAdmissionDTO:
        return message_bus_instance.invoke(
            RecupererEtudesSecondairesQuery(matricule_candidat=self.candidate['global_id'])
        )

    @property
    def matricule_personne_connue_selectionnee(self) -> Optional[str]:
        if self.request.GET.get('matricule'):
            return format_matricule(self.request.GET.get('matricule'))
        return None

    @cached_property
    def curriculum_personne_connue(self) -> Optional[CurriculumAdmissionDTO]:
        with contextlib.suppress(Person.DoesNotExist):
            if self.matricule_personne_connue_selectionnee:
                return message_bus_instance.invoke(
                    RechercherParcoursAnterieurQuery(
                        global_id=self.matricule_personne_connue_selectionnee,
                        uuid_proposition=self.kwargs['admission_uuid'],
                    )
                )
        return None

    @cached_property
    def etudes_secondaires_personne_connue(self) -> Optional[EtudesSecondairesAdmissionDTO]:
        with contextlib.suppress(Person.DoesNotExist):
            if self.matricule_personne_connue_selectionnee:
                return message_bus_instance.invoke(
                    RecupererEtudesSecondairesQuery(
                        matricule_candidat=self.matricule_personne_connue_selectionnee,
                    )
                )
        return None

    def get_context_data(self, **kwargs):
        context = {
            **super().get_context_data(**kwargs),
            'secondary_school_or_alternative_experiences': self.get_secondary_school_or_alternative_experiences(),
            'person_merge_proposal': self.person_merge_proposal,
            'educational_experiences': self.get_educational_experiences(),
            'professional_experiences': self.get_professional_experiences(),
            'mergeable_experiences_uuids': self.get_mergeable_experiences_uuids(),
        }
        return context

    def get_secondary_school_or_alternative_experiences(self):
        secondary_school_or_alternative_experiences = [
            SimpleNamespace(
                uuid=self.etudes_secondaires_candidat.uuid,
                annees=self.etudes_secondaires_candidat.annee_diplome_etudes_secondaires,
                nom_formation=self._get_nom_formation_etude_secondaire(self.etudes_secondaires_candidat),
                nom_institut=self._get_nom_institut_etude_secondaire(self.etudes_secondaires_candidat),
                est_experience_belge=isinstance(
                    self.etudes_secondaires_candidat.experience, DiplomeBelgeEtudesSecondairesDTO
                ),
                source='CANDIDAT',
            )
        ]
        if self.etudes_secondaires_personne_connue:
            secondary_school_or_alternative_experiences.append(
                SimpleNamespace(
                    uuid=self.etudes_secondaires_personne_connue.uuid,
                    annees=self.etudes_secondaires_personne_connue.annee_diplome_etudes_secondaires,
                    nom_formation=self._get_nom_formation_etude_secondaire(self.etudes_secondaires_personne_connue),
                    nom_institut=self._get_nom_institut_etude_secondaire(self.etudes_secondaires_personne_connue),
                    est_experience_belge=isinstance(
                        self.etudes_secondaires_candidat.experience, DiplomeBelgeEtudesSecondairesDTO
                    ),
                    source='PERSONNE_CONNUE',
                )
            )
        return secondary_school_or_alternative_experiences

    def _get_nom_formation_etude_secondaire(self, etude_secondaire: EtudesSecondairesAdmissionDTO):
        if self.etudes_secondaires_candidat.experience and isinstance(
                etude_secondaire.experience, DiplomeBelgeEtudesSecondairesDTO
        ):
            return "CESS"
        elif self.etudes_secondaires_candidat.experience and isinstance(
                etude_secondaire.experience, DiplomeEtrangerEtudesSecondairesDTO
        ):
            return ForeignDiplomaTypes[etude_secondaire.experience.type_diplome].value
        elif self.etudes_secondaires_candidat.experience and isinstance(
                etude_secondaire.experience, AlternativeSecondairesDTO
        ):
            return _("Bachelor's course entrance exam")
        elif etude_secondaire.annee_diplome_etudes_secondaires:
            return _("Secondary school")

    def _get_nom_institut_etude_secondaire(self, etude_secondaire: EtudesSecondairesAdmissionDTO):
        if isinstance(etude_secondaire.experience, DiplomeBelgeEtudesSecondairesDTO):
            return etude_secondaire.experience.nom_institut
        return getattr(etude_secondaire.experience, 'pays_nom', '')

    def get_professional_experiences(self):
        professional_experiences = self.curriculum_candidat.experiences_non_academiques
        if self.curriculum_personne_connue:
            professional_experiences += self.curriculum_personne_connue.experiences_non_academiques
        return sorted(professional_experiences, key=lambda exp: (exp.date_debut, exp.date_fin), reverse=True)

    def get_educational_experiences(self):
        educational_experiences = self.curriculum_candidat.experiences_academiques
        if self.curriculum_personne_connue:
            educational_experiences += self.curriculum_personne_connue.experiences_academiques
        return sorted(educational_experiences, key=lambda exp: exp.titre_formate, reverse=True)

    def get_mergeable_experiences_uuids(self):
        if self.curriculum_personne_connue:
            return [
                exp.uuid for exp in
                (
                    self.curriculum_personne_connue.experiences_non_academiques +
                    self.curriculum_personne_connue.experiences_academiques
                )
            ]
        return []

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['admission_uuid'])
