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
import copy
import itertools
from typing import Optional

from django.utils.translation import gettext_noop as _

from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import ChoixStatutChecklist
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition
from admission.ddd.admission.doctorat.preparation.domain.model.statut_checklist import (
    StatutsChecklistDoctorale,
    StatutChecklist,
)
from admission.ddd.admission.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.enums import TypeSituationAssimilation
from ddd.logic.financabilite.domain.model.enums.etat import EtatFinancabilite
from osis_common.ddd import interface


class Checklist(interface.DomainService):
    @classmethod
    def initialiser(
        cls,
        proposition: Proposition,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        annee_courante: int,
    ):
        checklist_initiale = cls.recuperer_checklist_initiale(
            proposition=proposition,
            profil_candidat_translator=profil_candidat_translator,
            annee_courante=annee_courante,
        )
        proposition.checklist_initiale = checklist_initiale
        proposition.checklist_actuelle = copy.deepcopy(checklist_initiale)

    @classmethod
    def recuperer_checklist_initiale(
        cls,
        proposition: Proposition,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        annee_courante: int = None,
    ) -> Optional[StatutsChecklistDoctorale]:
        identification_dto = profil_candidat_translator.get_identification(proposition.matricule_candidat)
        curriculum_dto = profil_candidat_translator.get_curriculum(
            proposition.matricule_candidat,
            annee_courante,
            proposition.entity_id.uuid,
        )

        return StatutsChecklistDoctorale(
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
                enfants=[
                    cls.initialiser_checklist_experience(experience.uuid)
                    for experience in itertools.chain(
                        curriculum_dto.experiences_academiques,
                        curriculum_dto.experiences_non_academiques,
                    )
                ],
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
            choix_formation=StatutChecklist(
                libelle=_("To be processed"),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
            projet_recherche=StatutChecklist(
                libelle=_("To be processed"),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
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
