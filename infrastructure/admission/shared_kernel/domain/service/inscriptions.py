# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.db.models import F, QuerySet

from admission.ddd.admission.shared_kernel.domain.service.i_annee_inscription_formation import (
    IAnneeInscriptionFormationTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_translator import (
    IInscriptionsTranslatorService,
)
from admission.ddd.admission.shared_kernel.dtos.inscription import InscriptionDTO
from base.models.enums.academic_type import AcademicTypes
from base.models.enums.education_group_types import TrainingType
from epc.models.enums.etat_inscription import EtatInscriptionFormation
from epc.models.enums.statut_inscription_programme_annuel import StatutInscriptionProgrammAnnuel
from epc.models.inscription_programme_annuel import InscriptionProgrammeAnnuel


class InscriptionsTranslatorService(IInscriptionsTranslatorService):
    @classmethod
    def enrolment_qs(
        cls,
        global_id: str,
        years: list[int] | None = None,
        sigle_formation: str = '',
    ) -> QuerySet[InscriptionProgrammeAnnuel]:
        qs = InscriptionProgrammeAnnuel.objects.filter(
            etat_inscription__in=[
                EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
                EtatInscriptionFormation.PROVISOIRE.name,
                EtatInscriptionFormation.CESSATION.name,
            ],
            programme__offer__academic_type__in=[
                AcademicTypes.ACADEMIC.name,
                AcademicTypes.NON_ACADEMIC_CREF.name,
            ],
            statut__in=[
                StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            ],
            programme_cycle__etudiant__person__global_id=global_id,
        )

        if years:
            qs = qs.filter(programme__offer__academic_year__year__in=years)

        if sigle_formation:
            qs = qs.filter(programme__offer__acronym=sigle_formation)

        return qs

    @classmethod
    def _get_dto_from_qs(cls, enrolment_qs: QuerySet[InscriptionProgrammeAnnuel]) -> list[InscriptionDTO]:
        enrolment_qs = enrolment_qs.annotate(
            sigle_formation=F('programme__offer__acronym'),
            annee_formation=F('programme__offer__academic_year__year'),
            noma=F('programme_cycle__etudiant__registration_id'),
        ).values(
            'sigle_formation',
            'annee_formation',
            'noma',
            'est_premiere_annee_bachelier',
        )

        return [
            InscriptionDTO(
                sigle=enrolment['sigle_formation'],
                annee=enrolment['annee_formation'],
                noma=enrolment['noma'],
                est_premiere_annee_bachelier=enrolment['est_premiere_annee_bachelier'],
            )
            for enrolment in enrolment_qs
        ]

    @classmethod
    def recuperer(
        cls,
        matricule_candidat: str,
        annees: list[int] | None = None,
    ) -> list[InscriptionDTO]:
        enrolment_qs = cls.enrolment_qs(global_id=matricule_candidat, years=annees)
        return cls._get_dto_from_qs(enrolment_qs=enrolment_qs)

    @classmethod
    def recuperer_inscriptions_deliberables(
        cls,
        matricule_candidat: str,
        annee: int,
    ) -> list[InscriptionDTO]:
        enrolment_qs = (
            cls.enrolment_qs(global_id=matricule_candidat, years=[annee])
            .exclude(
                etat_inscription=EtatInscriptionFormation.CESSATION.name,
            )
            .exclude(
                programme__offer__education_group_type__name__in=TrainingType.doctorate_types(),
            )
        )

        return cls._get_dto_from_qs(enrolment_qs=enrolment_qs)

    @classmethod
    def est_inscrit_recemment(
        cls,
        matricule_candidat: str,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> bool:
        administrative_year = annee_inscription_formation_translator.recuperer_calendrier_administratif_courant().annee
        return cls.enrolment_qs(
            global_id=matricule_candidat,
            years=[administrative_year, administrative_year - 1],
        ).exists()

    @classmethod
    def est_en_poursuite(
        cls,
        matricule_candidat: str,
        sigle_formation: str,
    ) -> bool:
        return cls.enrolment_qs(
            global_id=matricule_candidat,
            sigle_formation=sigle_formation,
        ).exists()

    @classmethod
    def est_en_poursuite_directe(
        cls,
        matricule_candidat: str,
        sigle_formation: str,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> bool:
        administrative_year = annee_inscription_formation_translator.recuperer_calendrier_administratif_courant().annee
        return cls.enrolment_qs(
            global_id=matricule_candidat,
            sigle_formation=sigle_formation,
            years=[administrative_year - 1],
        ).exists()
