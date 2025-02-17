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
import datetime
import uuid

import freezegun
import mock
from django.test import TestCase

from admission.ddd import FR_ISO_CODE
from admission.ddd.admission.doctorat.preparation.commands import (
    VerifierPropositionQuery,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixEtatSignature,
    ChoixStatutPropositionDoctorale,
    ChoixStatutSignatureGroupeDeSupervision,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AbsenceDeDetteNonCompleteeDoctoratException,
    AdresseCorrespondanceNonCompleteeException,
    AdresseDomicileLegalNonCompleteeException,
    AnneesCurriculumNonSpecifieesException,
    AssimilationNonCompleteeDoctoratException,
    CandidatNonTrouveException,
    CarteBancaireRemboursementAutreFormatNonCompleteDoctoratException,
    CarteBancaireRemboursementIbanNonCompleteDoctoratException,
    CarteIdentiteeNonSpecifieeException,
    DateOuAnneeNaissanceNonSpecifieeException,
    DetailsPasseportNonSpecifiesException,
    ExperiencesAcademiquesNonCompleteesException,
    FichierCurriculumNonRenseigneException,
    IdentificationNonCompleteeException,
    LanguesConnuesNonSpecifieesException,
    NomEtPrenomNonSpecifiesException,
    NumeroIdentiteBelgeNonSpecifieException,
    NumeroIdentiteNonSpecifieException,
    ProcedureDemandeSignatureNonLanceeException,
    PropositionNonApprouveeParMembresCAException,
    PropositionNonApprouveeParPromoteurException,
    TypeCompteBancaireRemboursementNonCompleteDoctoratException,
)
from admission.ddd.admission.doctorat.preparation.test.factory.groupe_de_supervision import (
    _SignatureMembreCAFactory,
    _SignaturePromoteurFactory,
)
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPConfirmeeFactory,
    _ComptabiliteFactory,
)
from admission.ddd.admission.domain.validator.exceptions import (
    NombrePropositionsSoumisesDepasseException,
    QuestionsSpecifiquesCurriculumNonCompleteesException,
    QuestionsSpecifiquesEtudesSecondairesNonCompleteesException,
)
from admission.ddd.admission.enums import (
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    ChoixTypeCompteBancaire,
    LienParente,
    TypeSituationAssimilation,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import (
    AnneeExperienceAcademique,
    ExperienceAcademique,
    ExperienceNonAcademique,
    ProfilCandidatInMemoryTranslator,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.enums.establishment_type import EstablishmentTypeEnum
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import (
    AcademicYear,
    AcademicYearIdentity,
)
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import (
    AcademicYearInMemoryRepository,
)
from osis_profile import BE_ISO_CODE
from osis_profile.models.enums.curriculum import (
    ActivitySector,
    ActivityType,
    EvaluationSystem,
    Grade,
    Result,
    TranscriptType,
)
from reference.models.enums.cycle import Cycle


class TestVerifierPropositionServiceCommun(TestCase):
    def assertHasInstance(self, container, cls, msg=None):
        if not any(isinstance(obj, cls) for obj in container):
            self.fail(msg or f"No instance of '{cls}' has been found")

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.params_default_experience_non_academique = {
            'uuid': str(uuid.uuid4()),
            'employeur': 'UCL',
            'type': ActivityType.WORK.name,
            'certificat': [],
            'fonction': 'Bibliothécaire',
            'secteur': ActivitySector.PUBLIC.name,
            'autre_activite': '',
        }

    def setUp(self) -> None:
        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.proposition_repository = PropositionInMemoryRepository()
        self.groupe_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.proposition = PropositionAdmissionSC3DPConfirmeeFactory(
            statut=ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE,
        )
        self.proposition_repository.save(self.proposition)
        self.groupe_supervision = self.groupe_supervision_repository.get_by_proposition_id(self.proposition.entity_id)
        self.candidat = self.candidat_translator.profil_candidats[0]
        self.adresse_domicile_legal = self.candidat_translator.adresses_candidats[0]
        self.adresse_correspondance = self.candidat_translator.adresses_candidats[1]
        self.experiences_non_academiques = self.candidat_translator.experiences_non_academiques
        self.addCleanup(self.proposition_repository.reset)
        self.message_bus = message_bus_in_memory_instance
        self.academic_year_repository = AcademicYearInMemoryRepository()
        self.etudes_secondaires = self.candidat_translator.etudes_secondaires.get(self.candidat.matricule)
        if self.etudes_secondaires:
            self.etudes_secondaires.annee_diplome_etudes_secondaires = None

        for annee in range(2016, 2021):
            self.academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )

        # Mock datetime to return the 2020 year as the current year
        patcher = freezegun.freeze_time('2020-11-01')
        patcher.start()
        self.addCleanup(patcher.stop)

        self.cmd = VerifierPropositionQuery(uuid_proposition=self.proposition.entity_id.uuid)


class TestVerifierPropositionService(TestVerifierPropositionServiceCommun):
    def test_should_verifier_etre_ok_si_complet(self):
        proposition_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(proposition_id.uuid, self.proposition.entity_id.uuid)

    def test_should_retourner_erreur_si_candidat_non_trouve(self):
        with mock.patch.multiple(self.candidat, matricule='unknown_user_id'):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), CandidatNonTrouveException)

    def test_should_retourner_erreur_si_demande_signature_pas_en_cours(self):
        with mock.patch.object(
            self.groupe_supervision,
            'statut_signature',
            ChoixStatutSignatureGroupeDeSupervision.IN_PROGRESS,
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertIsInstance(context.exception.exceptions.pop(), ProcedureDemandeSignatureNonLanceeException)

    def test_should_retourner_erreur_si_tous_promoteurs_n_ont_pas_approuve(self):
        self.groupe_supervision.signatures_promoteurs.append(
            _SignaturePromoteurFactory(promoteur_id__uuid='promoteur-SC3DP', etat=ChoixEtatSignature.DECLINED),
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)
        self.assertIsInstance(context.exception.exceptions.pop(), PropositionNonApprouveeParPromoteurException)

        self.groupe_supervision.signatures_promoteurs.pop()

    def test_should_retourner_erreur_si_tous_membres_ca_n_ont_pas_approuve(self):
        self.groupe_supervision.signatures_membres_CA.append(
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED),
        )

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)
        self.assertIsInstance(context.exception.exceptions.pop(), PropositionNonApprouveeParMembresCAException)

        self.groupe_supervision.signatures_membres_CA.pop()

    def _test_should_retourner_erreur_si_comptabilite_incomplete(self, comptabilite, exception):
        with mock.patch.object(self.proposition, 'comptabilite', comptabilite):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)
            self.assertTrue(any(member for member in context.exception.exceptions if isinstance(member, exception)))

    def _test_should_retourner_erreur_si_assimilation_incomplete(self, comptabilite, exception):
        with mock.patch.object(self.candidat, 'pays_nationalite', 'CA'):
            self._test_should_retourner_erreur_si_comptabilite_incomplete(
                comptabilite=comptabilite,
                exception=exception,
            )

    def test_should_retourner_erreur_si_absence_dettes_incomplet(self):
        self._test_should_retourner_erreur_si_comptabilite_incomplete(
            comptabilite=_ComptabiliteFactory(attestation_absence_dette_etablissement=[]),
            exception=AbsenceDeDetteNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_incomplete_pour_type_situation(self):
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=_ComptabiliteFactory(type_situation_assimilation=None),
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_incomplete_pour_type_assimilation_1(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE,
            sous_type_situation_assimilation_1='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_1_incomplete_pour_carte_resident_longue_duree(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE,
            sous_type_situation_assimilation_1=ChoixAssimilation1.TITULAIRE_CARTE_RESIDENT_LONGUE_DUREE,
            carte_resident_longue_duree=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_1_incomplete_pour_carte_etranger(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE,
            sous_type_situation_assimilation_1=ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER,
            carte_cire_sejour_illimite_etranger=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_1_incomplete_pour_carte_sejour_membre_famille_ue(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE,
            sous_type_situation_assimilation_1=ChoixAssimilation1.TITULAIRE_CARTE_SEJOUR_MEMBRE_UE,
            carte_sejour_membre_ue=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_1_incomplete_pour_carte_sejour_permanent_membre_famille_ue(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE,
            sous_type_situation_assimilation_1=ChoixAssimilation1.TITULAIRE_CARTE_SEJOUR_PERMANENT_MEMBRE_UE,
            carte_sejour_permanent_membre_ue=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_incomplete_pour_type_assimilation_2(self):
        situation = TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=situation,
            sous_type_situation_assimilation_2='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_2_incomplete_pour_refugie(self):
        situation = TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=situation,
            sous_type_situation_assimilation_2=ChoixAssimilation2.REFUGIE,
            carte_a_b_refugie=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_2_incomplete_pour_demandeur_asile_annexe(self):
        situation = TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=situation,
            sous_type_situation_assimilation_2=ChoixAssimilation2.DEMANDEUR_ASILE,
            annexe_25_26_refugies_apatrides=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_2_incomplete_pour_demandeur_asile_attestation(self):
        situation = TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=situation,
            sous_type_situation_assimilation_2=ChoixAssimilation2.DEMANDEUR_ASILE,
            attestation_immatriculation=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_2_incomplete_pour_protection_subsidiaire_carte_a_b(self):
        situation = TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=situation,
            sous_type_situation_assimilation_2=ChoixAssimilation2.PROTECTION_SUBSIDIAIRE,
            carte_a_b=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_2_incomplete_pour_protection_subsidiaire_decision(self):
        situation = TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=situation,
            sous_type_situation_assimilation_2=ChoixAssimilation2.PROTECTION_SUBSIDIAIRE,
            decision_protection_subsidiaire=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_2_incomplete_pour_protection_temporaire(self):
        situation = TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=situation,
            sous_type_situation_assimilation_2=ChoixAssimilation2.PROTECTION_TEMPORAIRE,
            decision_protection_temporaire=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_incomplete_pour_type_assimilation_3(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT'
            ],
            sous_type_situation_assimilation_3='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_3_incomplete_pour_revenus_professionnels_titre_sejour(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT'
            ],
            sous_type_situation_assimilation_3=ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS,
            titre_sejour_3_mois_professionel=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_3_incomplete_pour_revenus_professionnels_fiche_remuneration(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT'
            ],
            sous_type_situation_assimilation_3=ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS,
            fiches_remuneration=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_3_incomplete_pour_revenus_remplacemente_titre_sejour(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT'
            ],
            sous_type_situation_assimilation_3=ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT,
            titre_sejour_3_mois_remplacement=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_3_incomplete_pour_revenus_remplacemente_preuve_allocations(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT'
            ],
            sous_type_situation_assimilation_3=ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT,
            preuve_allocations_chomage_pension_indemnite=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_4_incomplete(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS,
            attestation_cpas=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_incomplete_pour_type_assimilation_5(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            relation_parente=LienParente.COHABITANT_LEGAL,
            sous_type_situation_assimilation_5='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_incomplete_pour_lien_parente_assimilation_5(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.A_NATIONALITE_UE,
            relation_parente='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_avec_pere_composition_menage_acte_naissance(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.A_NATIONALITE_UE,
            relation_parente=LienParente.PERE,
            composition_menage_acte_naissance=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_avec_mere_composition_menage_acte_naissance(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.A_NATIONALITE_UE,
            relation_parente=LienParente.MERE,
            composition_menage_acte_naissance=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_avec_tuteur_acte_tutelle(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.A_NATIONALITE_UE,
            relation_parente=LienParente.TUTEUR_LEGAL,
            acte_tutelle=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_avec_conjoint_acte_tutelle(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.A_NATIONALITE_UE,
            relation_parente=LienParente.CONJOINT,
            composition_menage_acte_mariage=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_avec_cohabitant_legal_attestation(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.A_NATIONALITE_UE,
            relation_parente=LienParente.COHABITANT_LEGAL,
            attestation_cohabitation_legale=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_carte_identite(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.A_NATIONALITE_UE,
            relation_parente=LienParente.PERE,
            carte_identite_parent=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_titre_sejour_longue_duree(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.TITULAIRE_TITRE_SEJOUR_LONGUE_DUREE,
            relation_parente=LienParente.PERE,
            titre_sejour_longue_duree_parent=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_refugie_apatride(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5[
                'CANDIDATE_REFUGIE_OU_REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE'
            ],
            relation_parente=LienParente.PERE,
            annexe_25_26_refugies_apatrides_decision_protection_parent=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_titre_sejour(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5[
                'AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT'
            ],
            relation_parente=LienParente.PERE,
            titre_sejour_3_mois_parent=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_revenus(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5[
                'AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT'
            ],
            relation_parente=LienParente.PERE,
            fiches_remuneration_parent=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_5_incomplete_attestation_cpas(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation[
                'PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4'
            ],
            sous_type_situation_assimilation_5=ChoixAssimilation5.PRIS_EN_CHARGE_OU_DESIGNE_CPAS,
            relation_parente=LienParente.PERE,
            attestation_cpas_parent=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_incomplete_pour_type_assimilation_6(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2,
            sous_type_situation_assimilation_6='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_6_incomplete_bourse_communaute_francaise(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2,
            sous_type_situation_assimilation_6=ChoixAssimilation6.A_BOURSE_ETUDES_COMMUNAUTE_FRANCAISE,
            decision_bourse_cfwb=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_6_incomplete_bourse_cooperation_developpement(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2,
            sous_type_situation_assimilation_6=ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT,
            attestation_boursier=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_7_incomplete_titre_identite_sejour_longue_duree_ue(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.RESIDENT_LONGUE_DUREE_UE_HORS_BELGIQUE,
            titre_identite_sejour_longue_duree_ue=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_assimilation_7_incomplete_titre_sejour_belgique(self):
        comptabilite = _ComptabiliteFactory(
            type_situation_assimilation=TypeSituationAssimilation.RESIDENT_LONGUE_DUREE_UE_HORS_BELGIQUE,
            type_numero_compte=ChoixTypeCompteBancaire.AUTRE_FORMAT,
            titre_sejour_belgique=[],
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=AssimilationNonCompleteeDoctoratException,
        )

    def test_should_retourner_erreur_si_type_compte_bancaire_non_renseigne(self):
        comptabilite = _ComptabiliteFactory(
            type_numero_compte=None,
        )
        self._test_should_retourner_erreur_si_comptabilite_incomplete(
            comptabilite=comptabilite,
            exception=TypeCompteBancaireRemboursementNonCompleteDoctoratException,
        )

    def test_should_retourner_erreur_si_compte_bancaire_iban_incomplet(self):
        comptabilite = _ComptabiliteFactory(
            type_numero_compte=ChoixTypeCompteBancaire.IBAN,
            numero_compte_iban='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=CarteBancaireRemboursementIbanNonCompleteDoctoratException,
        )

    def test_should_retourner_erreur_prenom_titulaire_compte_bancaire_iban_non_renseigne(self):
        comptabilite = _ComptabiliteFactory(
            type_numero_compte=ChoixTypeCompteBancaire.IBAN,
            prenom_titulaire_compte='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=CarteBancaireRemboursementIbanNonCompleteDoctoratException,
        )

    def test_should_retourner_erreur_nom_titulaire_compte_bancaire_iban_non_renseigne(self):
        comptabilite = _ComptabiliteFactory(
            type_numero_compte=ChoixTypeCompteBancaire.IBAN,
            nom_titulaire_compte='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=CarteBancaireRemboursementIbanNonCompleteDoctoratException,
        )

    def test_should_retourner_erreur_si_numero_compte_bancaire_autre_format_non_renseigne(self):
        comptabilite = _ComptabiliteFactory(
            type_numero_compte=ChoixTypeCompteBancaire.AUTRE_FORMAT,
            numero_compte_autre_format='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=CarteBancaireRemboursementAutreFormatNonCompleteDoctoratException,
        )

    def test_should_retourner_erreur_si_code_bic_compte_bancaire_autre_format_non_renseigne(self):
        comptabilite = _ComptabiliteFactory(
            type_numero_compte=ChoixTypeCompteBancaire.AUTRE_FORMAT,
            code_bic_swift_banque='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=CarteBancaireRemboursementAutreFormatNonCompleteDoctoratException,
        )

    def test_should_retourner_erreur_prenom_titulaire_compte_bancaire_autre_format_non_renseigne(self):
        comptabilite = _ComptabiliteFactory(
            type_numero_compte=ChoixTypeCompteBancaire.AUTRE_FORMAT,
            prenom_titulaire_compte='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=CarteBancaireRemboursementAutreFormatNonCompleteDoctoratException,
        )

    def test_should_retourner_erreur_nom_titulaire_compte_bancaire_autre_format_non_renseigne(self):
        comptabilite = _ComptabiliteFactory(
            type_numero_compte=ChoixTypeCompteBancaire.AUTRE_FORMAT,
            nom_titulaire_compte='',
        )
        self._test_should_retourner_erreur_si_assimilation_incomplete(
            comptabilite=comptabilite,
            exception=CarteBancaireRemboursementAutreFormatNonCompleteDoctoratException,
        )

    def test_should_verification_renvoyer_erreur_si_trop_de_demandes_envoyees(self):
        propositions = self.proposition_repository.search(matricule_candidat=self.candidat.matricule)
        last_proposition = propositions.pop()
        for proposition in propositions:
            proposition.statut = ChoixStatutPropositionDoctorale.EN_BROUILLON
        last_proposition.statut = ChoixStatutPropositionDoctorale.CONFIRMEE
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertHasInstance(context.exception.exceptions, NombrePropositionsSoumisesDepasseException)
