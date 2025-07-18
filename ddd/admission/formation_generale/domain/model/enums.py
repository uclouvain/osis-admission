# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from base.models.utils.utils import ChoiceEnum


class ChoixStatutPropositionGenerale(ChoiceEnum):
    EN_BROUILLON = _('In draft form')
    FRAIS_DOSSIER_EN_ATTENTE = _('Pending application fee')
    CONFIRMEE = _('Application confirmed')
    ANNULEE = _('Cancelled application')
    A_COMPLETER_POUR_SIC = _('To be completed for the Enrolment Office (SIC)')
    COMPLETEE_POUR_SIC = _('Completed for SIC')

    TRAITEMENT_FAC = _('Processing by Fac')
    A_COMPLETER_POUR_FAC = _('To be completed for Fac')
    COMPLETEE_POUR_FAC = _('Completed for Fac')
    RETOUR_DE_FAC = _('Feedback from Fac')
    ATTENTE_VALIDATION_DIRECTION = _('Awaiting management approval')
    INSCRIPTION_AUTORISEE = _('Application accepted')
    INSCRIPTION_REFUSEE = _('Application denied')
    CLOTUREE = _('Closed')

    @classmethod
    def get_specific_values(cls, keys: Iterable[str]):
        return ', '.join([str(getattr(cls, key).value) for key in keys])

    @classmethod
    def get_status_priorities(cls):
        return {
            cls.INSCRIPTION_AUTORISEE.name: 5,
            cls.ATTENTE_VALIDATION_DIRECTION.name: 4,
            cls.RETOUR_DE_FAC: 3,
            cls.COMPLETEE_POUR_FAC: 2,
            cls.A_COMPLETER_POUR_FAC: 2,
            cls.TRAITEMENT_FAC: 2,
            cls.COMPLETEE_POUR_SIC: 2,
            cls.A_COMPLETER_POUR_SIC: 2,
            cls.CONFIRMEE: 1,
            cls.INSCRIPTION_REFUSEE: 1,
            cls.CLOTUREE: 1,
        }


STATUTS_PROPOSITION_GENERALE_NON_SOUMISE = {
    ChoixStatutPropositionGenerale.EN_BROUILLON.name,
    ChoixStatutPropositionGenerale.ANNULEE.name,
}

STATUTS_PROPOSITION_GENERALE_NON_SOUMISE_OU_FRAIS_DOSSIER_EN_ATTENTE = STATUTS_PROPOSITION_GENERALE_NON_SOUMISE | {
    ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name
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

# Le gestionnaire SIC a la main et peut envoyer le dossier à la faculté pour que celle-ci donne sa décision
STATUTS_PROPOSITION_GENERALE_ENVOYABLE_EN_FAC_POUR_DECISION = {
    ChoixStatutPropositionGenerale.CONFIRMEE.name,
    ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name,
    ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC.name,
}

# Le gestionnaire SIC a la main ou attend le paiement
STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC_OU_FRAIS_DOSSIER_EN_ATTENTE = (
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC
    | {
        ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
    }
)

# Le gestionnaire SIC a la main et peut demander le paiement des frais de dossier au candidat
STATUTS_PROPOSITION_GENERALE_GESTIONNAIRE_PEUT_DEMANDER_PAIEMENT = {
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

STATUTS_PROPOSITION_GENERALE_SOUMISE_HORS_FRAIS_DOSSIER = (
    set(ChoixStatutPropositionGenerale.get_names())
    - STATUTS_PROPOSITION_GENERALE_NON_SOUMISE_OU_FRAIS_DOSSIER_EN_ATTENTE
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


class DerogationFinancement(ChoiceEnum):
    NON_CONCERNE = _('NON_CONCERNE')
    CANDIDAT_NOTIFIE = _('CANDIDAT_NOTIFIE')
    ABANDON_DU_CANDIDAT = _('ABANDON_DU_CANDIDAT')
    REFUS_DE_DEROGATION_FACULTAIRE = _('REFUS_DE_DEROGATION_FACULTAIRE')
    ACCORD_DE_DEROGATION_FACULTAIRE = _('ACCORD_DE_DEROGATION_FACULTAIRE')


class BesoinDeDerogation(ChoiceEnum):
    NON_CONCERNE = _("NON_CONCERNE")
    AVIS_DIRECTION_DEMANDE = _("AVIS_DIRECTION_DEMANDE")
    BESOIN_DE_COMPLEMENT = _("BESOIN_DE_COMPLEMENT")
    REFUS_DIRECTION = _("REFUS_DIRECTION")
    ACCORD_DIRECTION = _("ACCORD_DIRECTION")


class BesoinDeDerogationDelegueVrae(ChoiceEnum):
    DEROGATION_DELEGUE = _("DEROGATION_DELEGUE")
    DEROGATION_VRAE = _("DEROGATION_VRAE")
    PAS_DE_DEROGATION = _("PAS_DE_DEROGATION")


class DroitsInscriptionMontant(ChoiceEnum):
    INSCRIPTION_AU_ROLE = _("INSCRIPTION_AU_ROLE")
    INSCRIPTION_REGULIERE = _("INSCRIPTION_REGULIERE")
    NOUVEAUX_DROITS_MAJORES = _("NOUVEAUX_DROITS_MAJORES")
    ANCIENS_DROITS_MAJORES_2505 = _("ANCIENS_DROITS_MAJORES_2505")
    ANCIENS_DROITS_MAJORES_4175 = _("ANCIENS_DROITS_MAJORES_4175")
    AGREGATION = _("AGREGATION")
    MASTER_DE_SPECIALISATION_SANTE = _("MASTER_DE_SPECIALISATION_SANTE")
    CERTIFICAT_60_CREDITS = _("CERTIFICAT_60_CREDITS")
    PAS_DE_DROITS_D_INSCRIPTION = _("PAS_DE_DROITS_D_INSCRIPTION")
    AUTRE = _("AUTRE")


DROITS_INSCRIPTION_MONTANT_VALEURS = {
    DroitsInscriptionMontant.INSCRIPTION_AU_ROLE.name: 66,
    DroitsInscriptionMontant.INSCRIPTION_REGULIERE.name: 835,
    DroitsInscriptionMontant.NOUVEAUX_DROITS_MAJORES.name: 5010,
    DroitsInscriptionMontant.ANCIENS_DROITS_MAJORES_2505.name: 2505,
    DroitsInscriptionMontant.ANCIENS_DROITS_MAJORES_4175.name: 4175,
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
    REFUS_ARTICLE_95_SIC_CONDITIONS_PUBLIEES_MASTER = _("REFUS_ARTICLE_95_SIC_CONDITIONS_PUBLIEES_MASTER")
    REFUS_ARTICLE_95_SIC_CONDITIONS_PUBLIEES_MASTER_SPECIALISATION = _(
        "REFUS_ARTICLE_95_SIC_CONDITIONS_PUBLIEES_MASTER_SPECIALISATION"
    )
    REFUS_ARTICLE_95_CERTIFICAT = _("REFUS_ARTICLE_95_CERTIFICAT")
    REFUS_ARTICLE_95_ACCES_S4 = _("REFUS_ARTICLE_95_ACCES_S4")
    REFUS_ARTICLE_95_ACCES_S5 = _("REFUS_ARTICLE_95_ACCES_S5")
    REFUS_ARTICLE_95_ACCES_MS_ENSEIGNEMENT = _("REFUS_ARTICLE_95_ACCES_MS_ENSEIGNEMENT")
    REFUS_ARTICLE_95_JURY = _("REFUS_ARTICLE_95_JURY")
    REFUS_ARTICLE_95_GENERIQUE_IRRECEVABILITE = _("REFUS_ARTICLE_95_GENERIQUE_IRRECEVABILITE")
    REFUS_AGREGATION = _("REFUS_AGREGATION")
    REFUS_ARTICLE_96_UE_HUE_ASSIMILES = _("REFUS_ARTICLE_96_UE_HUE_ASSIMILES")
    REFUS_ARTICLE_96_HUE_RAISON_ACADEMIQUE = _("REFUS_ARTICLE_96_HUE_RAISON_ACADEMIQUE")
    REFUS_DOSSIER_TARDIF = _("REFUS_DOSSIER_TARDIF")
    REFUS_COMPLEMENT_TARDIF = _("REFUS_COMPLEMENT_TARDIF")
    REFUS_ARTICLE_96_HUE_NON_PROGRESSION = _("REFUS_ARTICLE_96_HUE_NON_PROGRESSION")
    REFUS_LIBRE = _("REFUS_LIBRE")


class OngletsChecklist(ChoiceEnum):
    donnees_personnelles = _('Personal data')
    assimilation = _('Belgian student status')
    frais_dossier = _('Application fee')
    parcours_anterieur = _('Previous experience')
    experiences_parcours_anterieur = _('Previous experiences')
    financabilite = _('Financeability')
    choix_formation = _('Course choice')
    specificites_formation = _('Training specificities')
    decision_facultaire = _('Decision of the faculty')
    decision_sic = _('Decision of SIC')
