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
from typing import Iterable

from django.utils.translation import gettext_lazy as _

from admission.enum_utils import build_enum_from_choices
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
    ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION.name,
    ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
    ChoixStatutPropositionGenerale.INSCRIPTION_REFUSEE.name,
    ChoixStatutPropositionGenerale.CLOTUREE.name,
}

# Le gestionnaire SIC a la main ou attend le paiement
STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_OU_FRAIS_DOSSIER_EN_ATTENTE = (
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC
    | {
        ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
    }
)

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


class DecisionFacultaireEnum(ChoiceEnum):
    EN_DECISION = '1'
    HORS_DECISION = '0'


class RegleDeFinancement(ChoiceEnum):
    PREMIERE_INSCRIPTION_MEME_CYCLE = _('PREMIERE_INSCRIPTION_MEME_CYCLE')
    SECONDE_INSCRIPTION_MEME_CYCLE = _('SECONDE_INSCRIPTION_MEME_CYCLE')
    TROISIEME_INSCRIPTION_PREMIER_CYCLE_AVEC_REORIENTATION = _('TROISIEME_INSCRIPTION_PREMIER_CYCLE_AVEC_REORIENTATION')
    SUR_3_ANS_45_CREDITS_MEME_CYCLE = _('SUR_3_ANS_45_CREDITS_MEME_CYCLE')
    SUR_2_ANS_45_CREDITS_MEME_CYCLE = _('SUR_2_ANS_45_CREDITS_MEME_CYCLE')
    ACQUIS_75_POURCENTS_CREDITS = _('ACQUIS_75_POURCENTS_CREDITS')
    SUR_3_ANS_MOITIE_CREDITS = _('SUR_3_ANS_MOITIE_CREDITS')
    SUR_2_ANS_MOITIE_CREDITS = _('SUR_2_ANS_MOITIE_CREDITS')
    SUR_3_ANS_45_CREDITS_11BA = _('SUR_3_ANS_45_CREDITS_11BA')
    SUR_2_ANS_45_CREDITS_11BA = _('SUR_2_ANS_45_CREDITS_11BA')
    CENT_VINGT_CREDITS_NON_ENCORE_ACQUIS = _('CENT_VINGT_CREDITS_NON_ENCORE_ACQUIS')
    PREMIERE_REORIENTATION_SUR_5_ANS = _('PREMIERE_REORIENTATION_SUR_5_ANS')
    CINQ_G_1ERE_INSCRIPTION_MEME_CYCLE = _('CINQ_G_1ERE_INSCRIPTION_MEME_CYCLE')
    CINQ_G_2EME_INSCRIPTION_MEME_CYCLE = _('CINQ_G_2EME_INSCRIPTION_MEME_CYCLE')
    CINQ_G_2EME_INSCRIPTION_AVEC_REORIENTATION = _('CINQ_G_2EME_INSCRIPTION_AVEC_REORIENTATION')


class RegleCalculeResultat(ChoiceEnum):
    INDISPONIBLE = _('INDISPONIBLE')
    NON_CONCERNE = _('NON_CONCERNE')
    NON_FINANCABLE = _('NON_FINANCABLE')
    A_CLARIFIER = _('A_CLARIFIER')


RegleCalculeResultatAvecFinancable = build_enum_from_choices(
    'RegleCalculeResultatAvecFinancable',
    RegleDeFinancement.choices() + RegleCalculeResultat.choices(),
)


class BesoinDeDerogation(ChoiceEnum):
    NON_CONCERNE = _("NON_CONCERNE")
    AVIS_DIRECTION_DEMANDE = _("AVIS_DIRECTION_DEMANDE")
    BESOIN_DE_COMPLEMENT = _("BESOIN_DE_COMPLEMENT")
    REFUS_DIRECTION = _("REFUS_DIRECTION")
    ACCORD_DIRECTION = _("ACCORD_DIRECTION")


class DroitsInscriptionMontant(ChoiceEnum):
    INSCRIPTION_AU_ROLE = _("INSCRIPTION_AU_ROLE")
    INSCRIPTION_REGULIERE = _("INSCRIPTION_REGULIERE")
    DROITS_MAJORES = _("DROITS_MAJORES")
    NOUVEAUX_DROITS_MAJORES = _("NOUVEAUX_DROITS_MAJORES")
    AGREGATION = _("AGREGATION")
    MASTER_DE_SPECIALISATION_SANTE = _("MASTER_DE_SPECIALISATION_SANTE")
    CERTIFICAT_60_CREDITS = _("CERTIFICAT_60_CREDITS")
    PAS_DE_DROITS_D_INSCRIPTION = _("PAS_DE_DROITS_D_INSCRIPTION")
    AUTRE = _("AUTRE")


DROITS_INSCRIPTION_MONTANT_VALEURS = {
    DroitsInscriptionMontant.INSCRIPTION_AU_ROLE.name: 66,
    DroitsInscriptionMontant.INSCRIPTION_REGULIERE.name: 835,
    DroitsInscriptionMontant.DROITS_MAJORES.name: 4175,
    DroitsInscriptionMontant.NOUVEAUX_DROITS_MAJORES.name: 2505,
    DroitsInscriptionMontant.AGREGATION.name: 279,
    DroitsInscriptionMontant.MASTER_DE_SPECIALISATION_SANTE.name: 485,
    DroitsInscriptionMontant.CERTIFICAT_60_CREDITS.name: 1065,
    DroitsInscriptionMontant.PAS_DE_DROITS_D_INSCRIPTION.name: 0,
}


class DispenseOuDroitsMajores(ChoiceEnum):
    NON_CONCERNE = _("NON_CONCERNE")
    DROITS_MAJORES_DEMANDES = _("DROITS_MAJORES_DEMANDES")
    DISPENSE_LDC = _("DISPENSE_LDC")
    DISPENSE_REUSSITE = _("DISPENSE_REUSSITE")
    DISPENSE_BOURSE = _("DISPENSE_BOURSE")
    DISPENSE_VCRC = _("DISPENSE_VCRC")
    DISPENSE_OFFRE = _("DISPENSE_OFFRE")
    DISPENSE_UNIV = _("DISPENSE_UNIV")
    DISPENSE_DUREE = _("DISPENSE_DUREE")
    DISPENSE_CESS_FWB = _("DISPENSE_CESS_FWB")
    REDUCTION_VCRC = _("REDUCTION_VCRC")


class MobiliteNombreDeMois(ChoiceEnum):
    SIX = _("6")
    DOUZE = _("12")


class TypeDeRefus(ChoiceEnum):
    REFUS_EQUIVALENCE = _("REFUS_EQUIVALENCE")
    REFUS_BAC_HUE_ACADEMIQUE = _("REFUS_BAC_HUE_ACADEMIQUE")
    REFUS_ARTICLE_95_SIC_CONDITIONS_PUBLIESS = _("REFUS_ARTICLE_95_SIC_CONDITIONS_PUBLIESS")
    REFUS_ARTICLE_95_JURY = _("REFUS_ARTICLE_95_JURY")
    REFUS_AGREGATION = _("REFUS_AGREGATION")
    REFUS_ARTICLE_96_UE_HUE_ASSIMILES = _("REFUS_ARTICLE_96_UE_HUE_ASSIMILES")
    REFUS_ARTICLE_96_HUE_RAISON_ACADEMIQUE = _("REFUS_ARTICLE_96_HUE_RAISON_ACADEMIQUE")
    REFUS_DOSSIER_TARDIF = _("REFUS_DOSSIER_TARDIF")
    REFUS_COMPLEMENT_TARDIF = _("REFUS_COMPLEMENT_TARDIF")
    REFUS_ARTICLE_96_HUE_NON_PROGRESSION = _("REFUS_ARTICLE_96_HUE_NON_PROGRESSION")
