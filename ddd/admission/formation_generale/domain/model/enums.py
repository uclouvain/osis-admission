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
from typing import Iterable

from django.utils.translation import gettext_lazy as _

from base.models.enums.got_diploma import GotDiploma
from base.models.utils.utils import ChoiceEnum


class ChoixStatutPropositionGenerale(ChoiceEnum):
    EN_BROUILLON = _('In draft form')
    FRAIS_DOSSIER_EN_ATTENTE = _('Pending application fee')
    CONFIRMEE = _('Application confirmed (by student)')
    ANNULEE = _('Cancelled application')
    A_COMPLETER_POUR_SIC = _('To be completed (by student) for the Enrolment Office (SIC)')
    COMPLETEE_POUR_SIC = _('Completed (by student) for SIC')

    TRAITEMENT_FAC = _('Processing by Fac')
    A_COMPLETER_POUR_FAC = _('To be completed (by student) for Fac')
    COMPLETEE_POUR_FAC = _('Completed (by student) for Fac')
    RETOUR_DE_FAC = _('Feedback from Fac')
    ATTENTE_VALIDATION_DIRECTION = _('Awaiting management approval')
    INSCRIPTION_AUTORISEE = _('Application accepted')
    INSCRIPTION_REFUSEE = _('Application denied')
    CLOTUREE = _('Closed')

    @classmethod
    def get_specific_values(cls, keys: Iterable[str]):
        return ', '.join([str(getattr(cls, key).value) for key in keys])


CHOIX_DIPLOME_OBTENU = {GotDiploma.YES.name, GotDiploma.THIS_YEAR.name}

STATUTS_PROPOSITION_GENERALE_NON_SOUMISE = {
    ChoixStatutPropositionGenerale.EN_BROUILLON.name,
    ChoixStatutPropositionGenerale.ANNULEE.name,
}

# Le gestionnaire FAC a la main
STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC = {
    ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC.name,
    ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name,
}

# Le gestionnaire FAC a la main ou attend une réponse du candidat
STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC_ETENDUS = STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC | {
    ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name,
}

# Le gestionnaire SIC a la main
STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC = {
    ChoixStatutPropositionGenerale.CONFIRMEE.name,
    ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name,
    ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC.name,
}

# Le gestionnaire SIC a la main ou attend une réponse du candidat
STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_ETENDUS = STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC | {
    ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
    ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name,
}

# Le candidat doit répondre à une demande du système ou d'un gestionnaire
STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_CANDIDAT = {
    ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
    ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name,
    ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name,
}

STATUTS_PROPOSITION_GENERALE_SOUMISE = (
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_ETENDUS
    | STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC_ETENDUS
    | {
        ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION.name,
        ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
        ChoixStatutPropositionGenerale.INSCRIPTION_REFUSEE.name,
        ChoixStatutPropositionGenerale.CLOTUREE.name,
    }
)


class ChoixStatutChecklist(ChoiceEnum):
    INITIAL_NON_CONCERNE = _("INITIAL_NON_CONCERNE")
    INITIAL_CANDIDAT = _("INITIAL_CANDIDAT")
    GEST_EN_COURS = _("GEST_EN_COURS")
    GEST_BLOCAGE = _("GEST_BLOCAGE")
    GEST_BLOCAGE_ULTERIEUR = _("GEST_BLOCAGE_ULTERIEUR")
    GEST_REUSSITE = _("GEST_REUSSITE")
    SYST_REUSSITE = _("SYST_REUSSITE")


class PoursuiteDeCycle(ChoiceEnum):
    TO_BE_DETERMINED = _("TO_BE_DETERMINED")
    YES = _("YES")
    NO = _("NO")
