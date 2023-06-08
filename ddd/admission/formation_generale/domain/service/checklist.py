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
from typing import Optional

from django.utils.translation import gettext_noop as _

from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    StatutChecklist,
    StatutsChecklistGenerale,
)
from osis_common.ddd import interface


class Checklist(interface.DomainService):
    @classmethod
    def initialiser(
        cls,
        proposition: Proposition,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        a_paye_frais_dossier: bool,
    ):
        checklist_initiale = cls.recuperer_checklist_initiale(
            proposition=proposition,
            profil_candidat_translator=profil_candidat_translator,
            a_paye_frais_dossier=a_paye_frais_dossier,
        )
        proposition.checklist_initiale = checklist_initiale
        proposition.checklist_actuelle = checklist_initiale

    @classmethod
    def recuperer_checklist_initiale(
        cls,
        proposition: Proposition,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        a_paye_frais_dossier: bool,
    ) -> Optional[StatutsChecklistGenerale]:
        if proposition.statut != ChoixStatutPropositionGenerale.CONFIRMEE:
            return

        pays_nationalite_europeen = profil_candidat_translator.get_identification(
            proposition.matricule_candidat
        ).pays_nationalite_europeen

        return StatutsChecklistGenerale(
            donnees_personnelles=StatutChecklist(
                libelle=_("To be processed"),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
            assimilation=StatutChecklist(
                libelle=_("Not concerned")
                if pays_nationalite_europeen
                else _("Declared not assimilated")
                if not proposition.comptabilite.type_situation_assimilation
                else _("Declared assimilated"),
                statut=ChoixStatutChecklist.INITIAL_NON_CONCERNE
                if pays_nationalite_europeen
                else ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
            parcours_anterieur=StatutChecklist(
                libelle=_("Previous experience"),
                enfants=[
                    StatutChecklist(
                        libelle=cls._format_exeperience(exp),
                        statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
                    )
                    for exp in []  # TODO profil_candidat_translator.get_curriculum() ?
                ],
            ),
            financabilite=StatutChecklist(
                libelle=_("To be processed"),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
            specificites_formation=StatutChecklist(
                libelle=_("To be processed"),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
            choix_formation=StatutChecklist(
                libelle=_("To be processed"),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
            # L'initialisation de la checklist nécessite le paiement des frais de dossier s'ils sont requis
            frais_dossier=StatutChecklist(
                libelle=_('Payed'),
                statut=ChoixStatutChecklist.SYST_REUSSITE,
            )
            if a_paye_frais_dossier
            else StatutChecklist(
                libelle=_('Not concerned'),
                statut=ChoixStatutChecklist.INITIAL_NON_CONCERNE,
            ),
        )
