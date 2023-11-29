# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import copy
from typing import Optional

from django.utils.translation import gettext_noop as _

from admission.ddd.admission.domain.model.formation import Formation
from admission.ddd.admission.domain.service.i_digit import IDigitService
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.dtos import IdentificationDTO
from admission.ddd.admission.enums import TypeSituationAssimilation, Onglets
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    StatutChecklist,
    StatutsChecklistGenerale,
)
from admission.ddd.admission.formation_generale.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from base.models.enums.education_group_types import TrainingType
from osis_common.ddd import interface

FINANCABILITE_FORMATIONS_NON_CONCERNEES = {
    TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
    TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE.name,
    TrainingType.CERTIFICATE_OF_SUCCESS.name,
    TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
    TrainingType.CERTIFICATE_OF_HOLDING_CREDITS.name,
    TrainingType.ACCESS_CONTEST.name,
    TrainingType.CERTIFICATE.name,
    TrainingType.RESEARCH_CERTIFICATE.name,
    TrainingType.ISOLATED_CLASS.name,
    TrainingType.LANGUAGE_CLASS.name,
    TrainingType.JUNIOR_YEAR.name,
    TrainingType.INTERNSHIP.name,
}


class Checklist(interface.DomainService):
    @classmethod
    def initialiser(
        cls,
        proposition: Proposition,
        formation: Formation,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        questions_specifiques_translator: 'IQuestionSpecifiqueTranslator',
        digit_service: 'IDigitService',
    ):
        checklist_initiale = cls.recuperer_checklist_initiale(
            proposition=proposition,
            formation=formation,
            profil_candidat_translator=profil_candidat_translator,
            questions_specifiques_translator=questions_specifiques_translator,
        )
        proposition.checklist_initiale = checklist_initiale
        proposition.checklist_actuelle = copy.deepcopy(checklist_initiale)

        identification_candidat = profil_candidat_translator.get_identification(proposition.matricule_candidat)
        proposition.reponse_digit = digit_service.rechercher_compte_existant(
            last_name=identification_candidat.nom,
            first_name=identification_candidat.prenom,
            birth_date=str(identification_candidat.date_naissance),
        )

    @classmethod
    def _get_specific_questions_number(
        cls,
        proposition: Proposition,
        identification_dto: IdentificationDTO,
        questions_specifiques_translator: IQuestionSpecifiqueTranslator,
    ) -> int:
        """
        Return the number of specific questions
        :param proposition: The proposition
        :param identification_dto: The identification related to the candidate
        :param questions_specifiques_translator: The translator for specific questions
        :return: The number of specific questions
        """

        # Static questions
        questions_number = 1  # Additional documents

        # Visa question
        if identification_dto.est_concerne_par_visa:
            questions_number += 1

        # Dynamic questions
        questions_number += len(
            questions_specifiques_translator.search_dto_by_proposition(
                proposition_uuid=proposition.entity_id.uuid,
                onglets=[Onglets.INFORMATIONS_ADDITIONNELLES.name],
            )
        )

        return questions_number

    @classmethod
    def recuperer_checklist_initiale(
        cls,
        proposition: Proposition,
        formation: Formation,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        questions_specifiques_translator: 'IQuestionSpecifiqueTranslator',
    ) -> Optional[StatutsChecklistGenerale]:
        identification_dto = profil_candidat_translator.get_identification(proposition.matricule_candidat)

        nombre_questions = cls._get_specific_questions_number(
            proposition=proposition,
            identification_dto=identification_dto,
            questions_specifiques_translator=questions_specifiques_translator,
        )

        return StatutsChecklistGenerale(
            donnees_personnelles=StatutChecklist(
                libelle=_("To be processed"),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
            assimilation=StatutChecklist(
                libelle=_("Not concerned")
                if identification_dto.pays_nationalite_europeen
                else _("Declared not assimilated")
                if not proposition.comptabilite.type_situation_assimilation
                or proposition.comptabilite.type_situation_assimilation == TypeSituationAssimilation.AUCUNE_ASSIMILATION
                else _("Declared assimilated"),
                statut=ChoixStatutChecklist.INITIAL_NON_CONCERNE
                if identification_dto.pays_nationalite_europeen
                else ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
            parcours_anterieur=StatutChecklist(
                libelle=_("To be processed"),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
                enfants=[],
            ),
            financabilite=StatutChecklist(
                libelle=_("Not concerned"),
                statut=ChoixStatutChecklist.INITIAL_NON_CONCERNE,
            )
            if formation.type.name in FINANCABILITE_FORMATIONS_NON_CONCERNEES
            else StatutChecklist(
                libelle=_("To be processed"),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
            specificites_formation=StatutChecklist(
                libelle=_("Not concerned"),
                statut=ChoixStatutChecklist.INITIAL_NON_CONCERNE,
            )
            if nombre_questions < 2
            else StatutChecklist(
                libelle=_("To be processed"),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
            choix_formation=StatutChecklist(
                libelle=_("To be processed"),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
            frais_dossier=StatutChecklist(
                libelle=_('Must pay'),
                statut=ChoixStatutChecklist.GEST_BLOCAGE,
                extra={'initial': '1'},
            )
            if proposition.statut == ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE
            else StatutChecklist(
                libelle=_('Not concerned'),
                statut=ChoixStatutChecklist.INITIAL_NON_CONCERNE,
            ),
            decision_facultaire=StatutChecklist(
                libelle=_('To be processed'),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
        )
