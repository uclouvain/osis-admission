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
import copy
from typing import Optional

from django.utils.translation import gettext_noop as _

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
from admission.ddd.admission.shared_kernel.domain.model.assimilation import Assimilation
from admission.ddd.admission.shared_kernel.domain.model.formation import Formation
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.shared_kernel.domain.service.profil_candidat import ProfilCandidat
from admission.ddd.admission.shared_kernel.dtos import IdentificationDTO
from admission.ddd.admission.shared_kernel.enums import Onglets, TypeSituationAssimilation
from ddd.logic.financabilite.domain.model.enums.etat import EtatFinancabilite
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import ExperienceAcademiqueDTO
from osis_common.ddd import interface
from osis_profile.models.enums.experience_validation import EtatAuthentificationParcours


class Checklist(interface.DomainService):
    @classmethod
    def initialiser(
        cls,
        proposition: Proposition,
        formation: Formation,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        questions_specifiques_translator: 'IQuestionSpecifiqueTranslator',
        candidat_est_en_poursuite_directe: bool,
        candidat_est_inscrit_recemment_ucl: bool,
        experiences_academiques: list[ExperienceAcademiqueDTO],
        assimilation_passee: Assimilation | None,
    ):
        checklist_initiale = cls.recuperer_checklist_initiale(
            proposition=proposition,
            formation=formation,
            profil_candidat_translator=profil_candidat_translator,
            questions_specifiques_translator=questions_specifiques_translator,
            candidat_est_en_poursuite_directe=candidat_est_en_poursuite_directe,
            assimilation_passee=assimilation_passee,
            candidat_est_inscrit_recemment_ucl=candidat_est_inscrit_recemment_ucl,
            experiences_academiques=experiences_academiques,
        )
        proposition.checklist_initiale = checklist_initiale
        proposition.checklist_actuelle = copy.deepcopy(checklist_initiale)

    @classmethod
    def _recuperer_statut_checklist_initial_specificites_formation(
        cls,
        proposition: Proposition,
        identification_dto: IdentificationDTO,
        questions_specifiques_translator: IQuestionSpecifiqueTranslator,
        experiences_academiques: list[ExperienceAcademiqueDTO],
        formation: Formation,
        candidat_est_inscrit_recemment_ucl: bool,
    ) -> StatutChecklist:
        return (
            StatutChecklist(
                libelle=_("To be processed"),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            )
            if (
                proposition.documents_additionnels
                or (not candidat_est_inscrit_recemment_ucl and identification_dto.est_concerne_par_visa)
                or (
                    not candidat_est_inscrit_recemment_ucl
                    and ProfilCandidat.est_potentiellement_concerne_par_le_bama_15(
                        uuid_proposition=proposition.entity_id.uuid,
                        formation=formation,
                        experiences_academiques=experiences_academiques,
                        statut_proposition=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
                        annee_formation=proposition.annee_calculee or proposition.formation_id.annee,
                    )
                )
                or any(
                    question.requis or question.valeur
                    for question in questions_specifiques_translator.search_dto_by_proposition(
                        proposition_uuid=proposition.entity_id.uuid,
                        onglets=[Onglets.INFORMATIONS_ADDITIONNELLES.name],
                    )
                )
            )
            else StatutChecklist(
                libelle=_('Sufficient'),
                statut=ChoixStatutChecklist.GEST_REUSSITE,
            )
        )

    @classmethod
    def _recuperer_statut_checklist_initial_assimilation(
        cls,
        proposition: Proposition,
        identification_dto: IdentificationDTO,
        candidat_est_en_poursuite_directe: bool,
        assimilation_passee: Assimilation | None,
    ) -> StatutChecklist:
        if identification_dto.pays_nationalite_europeen:
            return StatutChecklist(
                statut=ChoixStatutChecklist.INITIAL_NON_CONCERNE,
                libelle=_('Not concerned'),
            )

        if candidat_est_en_poursuite_directe:
            if assimilation_passee:
                if assimilation_passee.source == Assimilation.Source.OSIS:
                    return StatutChecklist(
                        statut=ChoixStatutChecklist.GEST_REUSSITE,
                        libelle=_('Validated'),
                    )
                else:
                    return StatutChecklist(
                        statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
                        libelle=_('Declared assimilated'),
                    )
            else:
                if (
                    proposition.comptabilite.type_situation_assimilation
                    == TypeSituationAssimilation.AUCUNE_ASSIMILATION
                ):
                    return StatutChecklist(
                        statut=ChoixStatutChecklist.GEST_REUSSITE,
                        libelle=_('Validated'),
                    )
                elif proposition.comptabilite.type_situation_assimilation:
                    return StatutChecklist(
                        statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
                        libelle=_('Declared assimilated'),
                    )
                else:
                    return StatutChecklist(
                        statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
                        libelle=_('Declared not assimilated'),
                    )

        if (
            not proposition.comptabilite.type_situation_assimilation
            or proposition.comptabilite.type_situation_assimilation == TypeSituationAssimilation.AUCUNE_ASSIMILATION
        ):
            return StatutChecklist(
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
                libelle=_('Declared not assimilated'),
            )
        else:
            return StatutChecklist(
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
                libelle=_('Declared assimilated'),
            )

    @classmethod
    def recuperer_checklist_initiale(
        cls,
        proposition: Proposition,
        formation: Formation,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        questions_specifiques_translator: 'IQuestionSpecifiqueTranslator',
        candidat_est_en_poursuite_directe: bool,
        candidat_est_inscrit_recemment_ucl: bool,
        assimilation_passee: Assimilation | None,
        experiences_academiques: list[ExperienceAcademiqueDTO],
    ) -> Optional[StatutsChecklistGenerale]:
        identification_dto = profil_candidat_translator.get_identification(proposition.matricule_candidat)

        statut_specificites_formation = cls._recuperer_statut_checklist_initial_specificites_formation(
            proposition=proposition,
            identification_dto=identification_dto,
            questions_specifiques_translator=questions_specifiques_translator,
            candidat_est_inscrit_recemment_ucl=candidat_est_inscrit_recemment_ucl,
            experiences_academiques=experiences_academiques,
            formation=formation,
        )

        statut_assimilation = cls._recuperer_statut_checklist_initial_assimilation(
            proposition=proposition,
            identification_dto=identification_dto,
            candidat_est_en_poursuite_directe=candidat_est_en_poursuite_directe,
            assimilation_passee=assimilation_passee,
        )

        return StatutsChecklistGenerale(
            assimilation=statut_assimilation,
            parcours_anterieur=StatutChecklist(
                libelle=_("To be processed"),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
            financabilite=StatutChecklist(
                libelle=_("Not concerned"),
                statut=ChoixStatutChecklist.INITIAL_NON_CONCERNE,
            )
            if proposition.financabilite_regle_calcule == EtatFinancabilite.NON_CONCERNE
            else StatutChecklist(
                libelle=_("To be processed"),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
            specificites_formation=statut_specificites_formation,
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
            decision_sic=StatutChecklist(
                libelle=_('To be processed'),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
        )

    @classmethod
    def initialiser_checklist_experience(cls, experience_uuid):
        return StatutChecklist(
            libelle=_('To be processed'),
            statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            extra={
                'identifiant': experience_uuid,
                'etat_authentification': EtatAuthentificationParcours.NON_CONCERNE.name,
            },
        )
