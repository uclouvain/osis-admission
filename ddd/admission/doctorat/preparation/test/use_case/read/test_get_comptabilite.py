# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import GetComptabiliteQuery
from admission.ddd.admission.doctorat.preparation.dtos import ComptabiliteDTO
from admission.ddd.admission.enums import (
    ChoixTypeCompteBancaire,
    TypeSituationAssimilation,
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    LienParente,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class GetComptabiliteTestCase(TestCase):
    def setUp(self):
        self.message_bus = message_bus_in_memory_instance
        self.cmd = GetComptabiliteQuery(uuid_proposition='uuid-SC3DP')

    def test_get_comptabilite(self):
        result = self.message_bus.invoke(self.cmd)
        self.assertEqual(
            result,
            ComptabiliteDTO(
                type_situation_assimilation=TypeSituationAssimilation.AUCUNE_ASSIMILATION.name,
                etudiant_solidaire=False,
                type_numero_compte=ChoixTypeCompteBancaire.NON.name,
                sous_type_situation_assimilation_1=ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER.name,
                sous_type_situation_assimilation_2=ChoixAssimilation2.PROTECTION_SUBSIDIAIRE.name,
                sous_type_situation_assimilation_3=(
                    ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS.name
                ),
                relation_parente=LienParente.MERE.name,
                sous_type_situation_assimilation_5=ChoixAssimilation5.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
                sous_type_situation_assimilation_6=ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT.name,
                attestation_absence_dette_etablissement=['file_token.pdf'],
                carte_resident_longue_duree=['file_token.pdf'],
                carte_cire_sejour_illimite_etranger=['file_token.pdf'],
                carte_sejour_membre_ue=['file_token.pdf'],
                carte_sejour_permanent_membre_ue=['file_token.pdf'],
                carte_a_b_refugie=['file_token.pdf'],
                annexe_25_26_refugies_apatrides=['file_token.pdf'],
                attestation_immatriculation=['file_token.pdf'],
                carte_a_b=['file_token.pdf'],
                decision_protection_subsidiaire=['file_token.pdf'],
                decision_protection_temporaire=['file_token.pdf'],
                titre_sejour_3_mois_professionel=['file_token.pdf'],
                fiches_remuneration=['file_token.pdf'],
                titre_sejour_3_mois_remplacement=['file_token.pdf'],
                preuve_allocations_chomage_pension_indemnite=['file_token.pdf'],
                attestation_cpas=['file_token.pdf'],
                composition_menage_acte_naissance=['file_token.pdf'],
                acte_tutelle=['file_token.pdf'],
                composition_menage_acte_mariage=['file_token.pdf'],
                attestation_cohabitation_legale=['file_token.pdf'],
                carte_identite_parent=['file_token.pdf'],
                titre_sejour_longue_duree_parent=['file_token.pdf'],
                annexe_25_26_refugies_apatrides_decision_protection_parent=['file_token.pdf'],
                titre_sejour_3_mois_parent=['file_token.pdf'],
                fiches_remuneration_parent=['file_token.pdf'],
                attestation_cpas_parent=['file_token.pdf'],
                decision_bourse_cfwb=['file_token.pdf'],
                attestation_boursier=['file_token.pdf'],
                titre_identite_sejour_longue_duree_ue=['file_token.pdf'],
                titre_sejour_belgique=['file_token.pdf'],
                numero_compte_iban='BE43068999999501',
                iban_valide=True,
                numero_compte_autre_format='123456',
                code_bic_swift_banque='GKCCBEBB',
                prenom_titulaire_compte='John',
                nom_titulaire_compte='Doe',
            ),
        )
