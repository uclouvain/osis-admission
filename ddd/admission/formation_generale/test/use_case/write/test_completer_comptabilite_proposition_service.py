# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest import TestCase

from admission.ddd.admission.formation_generale.commands import (
    CompleterComptabilitePropositionCommand,
)
from admission.ddd.admission.enums import (
    ChoixAffiliationSport,
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    ChoixTypeCompteBancaire,
    LienParente,
    TypeSituationAssimilation,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestCompleterComptabilitePropositionService(TestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()

        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = CompleterComptabilitePropositionCommand(
            uuid_proposition='uuid-MASTER-SCI',
            # Absence de dettes
            attestation_absence_dette_etablissement=['attestation_absence_dette_etablissement.pdf'],
            # Réduction des droits d'inscription
            demande_allocation_d_etudes_communaute_francaise_belgique=True,
            enfant_personnel=True,
            attestation_enfant_personnel=['attestation_enfant_personnel.pdf2'],
            # Assimilation
            type_situation_assimilation=TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
            # Assimilation 1
            sous_type_situation_assimilation_1=ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER.name,
            carte_resident_longue_duree=['carte_resident_longue_duree.pdf'],
            carte_cire_sejour_illimite_etranger=['carte_cire_sejour_illimite_etranger.pdf'],
            carte_sejour_membre_ue=['carte_sejour_membre_ue.pdf'],
            carte_sejour_permanent_membre_ue=['carte_sejour_permanent_membre_ue.pdf'],
            # Assimilation 2
            sous_type_situation_assimilation_2=ChoixAssimilation2.REFUGIE.name,
            carte_a_b_refugie=['carte_a_b_refugie.pdf'],
            annexe_25_26_refugies_apatrides=['annexe_25_26_refugies_apatrides.pdf'],
            attestation_immatriculation=['attestation_immatriculation.pdf'],
            carte_a_b=['carte_a_b.pdf'],
            decision_protection_subsidiaire=['decision_protection_subsidiaire.pdf'],
            decision_protection_temporaire=['decision_protection_temporaire.pdf'],
            # Assimilation 3
            sous_type_situation_assimilation_3=ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT.name,
            titre_sejour_3_mois_professionel=['titre_sejour_3_mois_professionel.pdf'],
            fiches_remuneration=['fiches_remuneration.pdf'],
            titre_sejour_3_mois_remplacement=['titre_sejour_3_mois_remplacement.pdf'],
            preuve_allocations_chomage_pension_indemnite=['preuve_allocations_chomage_pension_indemnite.pdf'],
            # Assimilation 4
            attestation_cpas=['attestation_cpas.pdf'],
            # Assimilation 5
            relation_parente=LienParente.COHABITANT_LEGAL.name,
            sous_type_situation_assimilation_5=ChoixAssimilation5.A_NATIONALITE_UE.name,
            composition_menage_acte_naissance=['composition_menage_acte_naissance.pdf'],
            acte_tutelle=['acte_tutelle.pdf'],
            composition_menage_acte_mariage=['composition_menage_acte_mariage.pdf'],
            attestation_cohabitation_legale=['attestation_cohabitation_legale.pdf'],
            carte_identite_parent=['carte_identite_parent.pdf'],
            titre_sejour_longue_duree_parent=['titre_sejour_longue_duree_parent.pdf'],
            annexe_25_26_refugies_apatrides_decision_protection_parent=[
                'annexe_25_26_refugies_apatrides_decision_protection_parent.pdf'
            ],
            titre_sejour_3_mois_parent=['titre_sejour_3_mois_parent.pdf'],
            fiches_remuneration_parent=['fiches_remuneration_parent.pdf'],
            attestation_cpas_parent=['attestation_cpas_parent.pdf'],
            # Assimilation 6
            sous_type_situation_assimilation_6=ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT.name,
            decision_bourse_cfwb=['decision_bourse_cfwb.pdf'],
            attestation_boursier=['attestation_boursier.pdf'],
            # Assimilation 7
            titre_identite_sejour_longue_duree_ue=['titre_identite_sejour_longue_duree_ue.pdf'],
            titre_sejour_belgique=['titre_sejour_belgique.pdf'],
            # Affiliations
            affiliation_sport=ChoixAffiliationSport.TOURNAI_UCL.name,
            etudiant_solidaire=True,
            # Compte bancaire
            type_numero_compte=ChoixTypeCompteBancaire.IBAN.name,
            numero_compte_iban='BARC20658244971655GB87',
            iban_valide=True,
            numero_compte_autre_format='123456',
            code_bic_swift_banque='GEBABEBB',
            prenom_titulaire_compte='Jane',
            nom_titulaire_compte='Poe',
        )

    def test_should_completer(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        proposition = self.proposition_repository.get(proposition_id)  # type: Proposition
        self.assertEqual(proposition_id, proposition.entity_id)
        self.assertEqual(
            proposition.comptabilite.attestation_absence_dette_etablissement,
            self.cmd.attestation_absence_dette_etablissement,
        )
        self.assertEqual(
            proposition.comptabilite.demande_allocation_d_etudes_communaute_francaise_belgique,
            self.cmd.demande_allocation_d_etudes_communaute_francaise_belgique,
        )
        self.assertEqual(proposition.comptabilite.enfant_personnel, self.cmd.enfant_personnel)
        self.assertEqual(proposition.comptabilite.attestation_enfant_personnel, self.cmd.attestation_enfant_personnel)
        self.assertEqual(
            proposition.comptabilite.type_situation_assimilation,
            TypeSituationAssimilation[self.cmd.type_situation_assimilation],
        )
        self.assertEqual(
            proposition.comptabilite.sous_type_situation_assimilation_1,
            ChoixAssimilation1[self.cmd.sous_type_situation_assimilation_1],
        )
        self.assertEqual(proposition.comptabilite.carte_resident_longue_duree, self.cmd.carte_resident_longue_duree)
        self.assertEqual(
            proposition.comptabilite.carte_cire_sejour_illimite_etranger, self.cmd.carte_cire_sejour_illimite_etranger
        )
        self.assertEqual(proposition.comptabilite.carte_sejour_membre_ue, self.cmd.carte_sejour_membre_ue)
        self.assertEqual(
            proposition.comptabilite.carte_sejour_permanent_membre_ue,
            self.cmd.carte_sejour_permanent_membre_ue,
        )
        self.assertEqual(
            proposition.comptabilite.sous_type_situation_assimilation_2,
            ChoixAssimilation2[self.cmd.sous_type_situation_assimilation_2],
        )
        self.assertEqual(proposition.comptabilite.carte_a_b_refugie, self.cmd.carte_a_b_refugie)
        self.assertEqual(
            proposition.comptabilite.annexe_25_26_refugies_apatrides,
            self.cmd.annexe_25_26_refugies_apatrides,
        )
        self.assertEqual(proposition.comptabilite.attestation_immatriculation, self.cmd.attestation_immatriculation)
        self.assertEqual(proposition.comptabilite.carte_a_b, self.cmd.carte_a_b)
        self.assertEqual(
            proposition.comptabilite.decision_protection_subsidiaire,
            self.cmd.decision_protection_subsidiaire,
        )
        self.assertEqual(
            proposition.comptabilite.decision_protection_temporaire,
            self.cmd.decision_protection_temporaire,
        )
        self.assertEqual(
            proposition.comptabilite.sous_type_situation_assimilation_3,
            ChoixAssimilation3[self.cmd.sous_type_situation_assimilation_3],
        )
        self.assertEqual(
            proposition.comptabilite.titre_sejour_3_mois_professionel,
            self.cmd.titre_sejour_3_mois_professionel,
        )
        self.assertEqual(proposition.comptabilite.fiches_remuneration, self.cmd.fiches_remuneration)
        self.assertEqual(
            proposition.comptabilite.titre_sejour_3_mois_remplacement,
            self.cmd.titre_sejour_3_mois_remplacement,
        )
        self.assertEqual(
            proposition.comptabilite.preuve_allocations_chomage_pension_indemnite,
            self.cmd.preuve_allocations_chomage_pension_indemnite,
        )
        self.assertEqual(proposition.comptabilite.attestation_cpas, self.cmd.attestation_cpas)
        self.assertEqual(proposition.comptabilite.relation_parente, LienParente[self.cmd.relation_parente])
        self.assertEqual(
            proposition.comptabilite.sous_type_situation_assimilation_5,
            ChoixAssimilation5[self.cmd.sous_type_situation_assimilation_5],
        )
        self.assertEqual(
            proposition.comptabilite.composition_menage_acte_naissance,
            self.cmd.composition_menage_acte_naissance,
        )
        self.assertEqual(proposition.comptabilite.acte_tutelle, self.cmd.acte_tutelle)
        self.assertEqual(
            proposition.comptabilite.composition_menage_acte_mariage,
            self.cmd.composition_menage_acte_mariage,
        )
        self.assertEqual(
            proposition.comptabilite.attestation_cohabitation_legale, self.cmd.attestation_cohabitation_legale
        )
        self.assertEqual(proposition.comptabilite.carte_identite_parent, self.cmd.carte_identite_parent)
        self.assertEqual(
            proposition.comptabilite.titre_sejour_longue_duree_parent,
            self.cmd.titre_sejour_longue_duree_parent,
        )
        self.assertEqual(
            proposition.comptabilite.annexe_25_26_refugies_apatrides_decision_protection_parent,
            self.cmd.annexe_25_26_refugies_apatrides_decision_protection_parent,
        )
        self.assertEqual(proposition.comptabilite.titre_sejour_3_mois_parent, self.cmd.titre_sejour_3_mois_parent)
        self.assertEqual(proposition.comptabilite.fiches_remuneration_parent, self.cmd.fiches_remuneration_parent)
        self.assertEqual(proposition.comptabilite.attestation_cpas_parent, self.cmd.attestation_cpas_parent)
        self.assertEqual(
            proposition.comptabilite.sous_type_situation_assimilation_6,
            ChoixAssimilation6[self.cmd.sous_type_situation_assimilation_6],
        )
        self.assertEqual(proposition.comptabilite.decision_bourse_cfwb, self.cmd.decision_bourse_cfwb)
        self.assertEqual(proposition.comptabilite.attestation_boursier, self.cmd.attestation_boursier)
        self.assertEqual(
            proposition.comptabilite.titre_identite_sejour_longue_duree_ue,
            self.cmd.titre_identite_sejour_longue_duree_ue,
        )
        self.assertEqual(proposition.comptabilite.titre_sejour_belgique, self.cmd.titre_sejour_belgique)
        self.assertEqual(proposition.comptabilite.affiliation_sport, ChoixAffiliationSport[self.cmd.affiliation_sport])
        self.assertEqual(proposition.comptabilite.etudiant_solidaire, self.cmd.etudiant_solidaire)
        self.assertEqual(
            proposition.comptabilite.type_numero_compte,
            ChoixTypeCompteBancaire[self.cmd.type_numero_compte]
        )
        self.assertEqual(proposition.comptabilite.numero_compte_iban, self.cmd.numero_compte_iban)
        self.assertEqual(proposition.comptabilite.iban_valide, self.cmd.iban_valide)
        self.assertEqual(proposition.comptabilite.numero_compte_autre_format, self.cmd.numero_compte_autre_format)
        self.assertEqual(proposition.comptabilite.code_bic_swift_banque, self.cmd.code_bic_swift_banque)
        self.assertEqual(proposition.comptabilite.prenom_titulaire_compte, self.cmd.prenom_titulaire_compte)
        self.assertEqual(proposition.comptabilite.nom_titulaire_compte, self.cmd.nom_titulaire_compte)
