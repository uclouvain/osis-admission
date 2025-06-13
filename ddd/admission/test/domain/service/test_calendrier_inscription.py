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
from unittest.mock import PropertyMock, MagicMock

import freezegun
import mock
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AdresseDomicileLegalNonCompleteeException,
    IdentificationNonCompleteeException,
)
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionECGE3DPMinimaleFactory,
)
from admission.ddd.admission.domain.service.i_titres_acces import ITitresAcces, Titres
from admission.ddd.admission.domain.validator.exceptions import (
    AucunPoolCorrespondantException,
    FormationNonTrouveeException,
    ModificationInscriptionExterneNonConfirmeeException,
    PoolNonResidentContingenteNonOuvertException,
    ReorientationInscriptionExterneNonConfirmeeException,
    ResidenceAuSensDuDecretNonRenseigneeException,
)
from admission.ddd.admission.enums import TypeSituationAssimilation
from admission.ddd.admission.formation_continue.test.factory.proposition import (
    PropositionFactory as PropositionContinueFactory,
)
from admission.ddd.admission.formation_generale.test.factory.proposition import (
    PropositionFactory,
)
from admission.ddd.admission.test.factory.formation import (
    FormationFactory,
    FormationIdentityFactory,
)
from admission.ddd.admission.test.factory.profil import ProfilCandidatFactory
from admission.infrastructure.admission.domain.service.in_memory.calendrier_inscription import (
    CalendrierInscriptionInMemory,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import (
    ProfilCandidatInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.formation import (
    FormationGeneraleInMemoryTranslator,
)
from admission.tests.factories.conditions import AdmissionConditionsDTOFactory
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType


@freezegun.freeze_time('2022-03-15')
class CalendrierInscriptionTestCase(TestCase):
    def setUp(self):
        self.profil_candidat_translator = ProfilCandidatInMemoryTranslator()
        self.formation_translator = FormationGeneraleInMemoryTranslator()
        self.profil_candidat_translator.reset()
        mock_calendrier_inscription = mock.patch(
            'admission.ddd.admission.domain.service.i_calendrier_inscription.ICalendrierInscription.'
            'INTERDIRE_INSCRIPTION_ETUDES_CONTINGENTES_POUR_NON_RESIDENT',
            new_callable=PropertyMock,
            return_value=False,
        )
        mock_calendrier_inscription.start()
        self.addCleanup(mock_calendrier_inscription.stop)

    def test_verification_calendrier_inscription_doctorat(self):
        proposition = PropositionAdmissionECGE3DPMinimaleFactory()
        dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
            formation_id=FormationFactory(type=TrainingType.PHD).entity_id,
            proposition=proposition,
            matricule_candidat=proposition.matricule_candidat,
            titres_acces=Titres(AdmissionConditionsDTOFactory()),
            formation=MagicMock(type=TrainingType.PHD),
            profil_candidat_translator=self.profil_candidat_translator,
        )
        self.assertEqual(dto.pool, AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT)

    def test_verification_calendrier_inscription_formation_continue(self):
        proposition = PropositionContinueFactory()
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
            formation_id=FormationFactory(type=TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE).entity_id,
            proposition=proposition,
            matricule_candidat=proposition.matricule_candidat,
            titres_acces=Titres(AdmissionConditionsDTOFactory()),
            formation=MagicMock(type=TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE),
            profil_candidat_translator=self.profil_candidat_translator,
        )
        self.assertEqual(dto.pool, AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT)

    @freezegun.freeze_time('2022-10-15')
    def test_verification_calendrier_inscription_modification_non_renseignee(self):
        # Nous sommes dans la période modification, mais le candidat n'a pas renseigné sa réponse à la modification
        proposition = PropositionFactory(
            formation_id__sigle='ECGE3DP',
            formation_id__annee=2022,
            est_modification_inscription_externe=None,
        )
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        with self.assertRaises(ModificationInscriptionExterneNonConfirmeeException):
            CalendrierInscriptionInMemory.verifier(
                formation_id=proposition.formation_id,
                proposition=proposition,
                matricule_candidat=proposition.matricule_candidat,
                titres_acces=Titres(AdmissionConditionsDTOFactory()),
                formation=MagicMock(type=TrainingType.BACHELOR),
                profil_candidat_translator=self.profil_candidat_translator,
                formation_translator=self.formation_translator,
            )

    @freezegun.freeze_time('2022-10-15')
    def test_verification_calendrier_inscription_modification_renseignee_sans_formulaire(self):
        # Nous sommes dans la période modification, mais le candidat n'a pas renseigné le formulaire associé
        proposition = PropositionFactory(
            formation_id__sigle='ECGE3DP',
            formation_id__annee=2022,
            est_modification_inscription_externe=True,
            formulaire_modification_inscription=[],
            attestation_inscription_reguliere_pour_modification_inscription=['u1'],
        )
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        with self.assertRaises(ModificationInscriptionExterneNonConfirmeeException):
            CalendrierInscriptionInMemory.verifier(
                formation_id=proposition.formation_id,
                proposition=proposition,
                matricule_candidat=proposition.matricule_candidat,
                titres_acces=Titres(AdmissionConditionsDTOFactory()),
                formation=MagicMock(type=TrainingType.BACHELOR),
                profil_candidat_translator=self.profil_candidat_translator,
                formation_translator=self.formation_translator,
            )

    @freezegun.freeze_time('2022-10-15')
    def test_verification_calendrier_inscription_modification_renseignee_attestation_inscription(self):
        # Nous sommes dans la période modification, mais le candidat n'a pas renseigné l'attestation associée
        proposition = PropositionFactory(
            formation_id__sigle='ECGE3DP',
            formation_id__annee=2022,
            est_modification_inscription_externe=True,
            formulaire_modification_inscription=['u1'],
            attestation_inscription_reguliere_pour_modification_inscription=[],
        )
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        with self.assertRaises(ModificationInscriptionExterneNonConfirmeeException):
            CalendrierInscriptionInMemory.verifier(
                formation_id=proposition.formation_id,
                proposition=proposition,
                matricule_candidat=proposition.matricule_candidat,
                titres_acces=Titres(AdmissionConditionsDTOFactory()),
                formation=MagicMock(type=TrainingType.BACHELOR),
                profil_candidat_translator=self.profil_candidat_translator,
                formation_translator=self.formation_translator,
            )

    @freezegun.freeze_time('2022-10-15')
    def test_verification_calendrier_inscription_modification_validee(self):
        # Nous sommes dans la période modification et le candidat l'a validée
        proposition = PropositionFactory(est_bachelier_en_modification=True)
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
            formation_id=proposition.formation_id,
            proposition=proposition,
            matricule_candidat=proposition.matricule_candidat,
            titres_acces=Titres(AdmissionConditionsDTOFactory()),
            formation=MagicMock(type=TrainingType.BACHELOR),
            profil_candidat_translator=self.profil_candidat_translator,
        )
        self.assertEqual(dto.pool, AcademicCalendarTypes.ADMISSION_POOL_EXTERNAL_ENROLLMENT_CHANGE)

    @freezegun.freeze_time('2022-10-15')
    def test_verification_calendrier_inscription_modification_non_choisie(self):
        # Nous sommes dans la période modification et le candidat ne l'a pas choisi (mais répondu)
        proposition = PropositionFactory(est_modification_inscription_externe=False)
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        pool = None
        try:
            dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
                formation_id=proposition.formation_id,
                proposition=proposition,
                matricule_candidat=proposition.matricule_candidat,
                titres_acces=Titres(AdmissionConditionsDTOFactory()),
                formation=MagicMock(type=TrainingType.BACHELOR),
                profil_candidat_translator=self.profil_candidat_translator,
            )
            pool = dto.pool
        except AucunPoolCorrespondantException:
            pass
        self.assertNotEqual(pool, AcademicCalendarTypes.ADMISSION_POOL_EXTERNAL_ENROLLMENT_CHANGE)

    @freezegun.freeze_time('2022-12-15')
    def test_verification_calendrier_inscription_reorientation_non_renseignee(self):
        # Nous sommes dans la période réorientation, mais le candidat n'a pas renseigné sa réponse à la réorientation
        proposition = PropositionFactory(
            formation_id__sigle='ECGE3DP',
            formation_id__annee=2022,
            est_reorientation_inscription_externe=None,
        )
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        with self.assertRaises(ReorientationInscriptionExterneNonConfirmeeException):
            CalendrierInscriptionInMemory.verifier(
                formation_id=proposition.formation_id,
                proposition=proposition,
                matricule_candidat=proposition.matricule_candidat,
                titres_acces=Titres(AdmissionConditionsDTOFactory()),
                formation=MagicMock(type=TrainingType.BACHELOR),
                profil_candidat_translator=self.profil_candidat_translator,
                formation_translator=self.formation_translator,
            )

    @freezegun.freeze_time('2022-12-15')
    def test_verification_calendrier_inscription_reorientation_renseignee_sans_piece_jointe(self):
        # Nous sommes dans la période réorientation, mais le candidat n'a pas téléversé la pièce jointe requise
        proposition = PropositionFactory(
            formation_id__sigle='ECGE3DP',
            formation_id__annee=2022,
            est_reorientation_inscription_externe=True,
            attestation_inscription_reguliere=[],
            formulaire_reorientation=['uuid-formulaire_reorientation'],
        )
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        with self.assertRaises(ReorientationInscriptionExterneNonConfirmeeException):
            CalendrierInscriptionInMemory.verifier(
                formation_id=proposition.formation_id,
                proposition=proposition,
                matricule_candidat=proposition.matricule_candidat,
                titres_acces=Titres(AdmissionConditionsDTOFactory()),
                formation=MagicMock(type=TrainingType.BACHELOR),
                profil_candidat_translator=self.profil_candidat_translator,
                formation_translator=self.formation_translator,
            )

        proposition = PropositionFactory(
            formation_id__sigle='ECGE3DP',
            formation_id__annee=2022,
            est_reorientation_inscription_externe=True,
            formulaire_reorientation=[],
            attestation_inscription_reguliere=['uuid_attestation_inscription_reguliere'],
        )
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        with self.assertRaises(ReorientationInscriptionExterneNonConfirmeeException):
            CalendrierInscriptionInMemory.verifier(
                formation_id=proposition.formation_id,
                proposition=proposition,
                matricule_candidat=proposition.matricule_candidat,
                titres_acces=Titres(AdmissionConditionsDTOFactory()),
                formation=MagicMock(type=TrainingType.BACHELOR),
                profil_candidat_translator=self.profil_candidat_translator,
                formation_translator=self.formation_translator,
            )

    @freezegun.freeze_time('2022-12-15')
    def test_verification_calendrier_inscription_reorientation_validee(self):
        # Nous sommes dans la période réorientation et le candidat l'a validée
        proposition = PropositionFactory(est_bachelier_en_reorientation=True)
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
            formation_id=proposition.formation_id,
            proposition=proposition,
            matricule_candidat=proposition.matricule_candidat,
            titres_acces=Titres(AdmissionConditionsDTOFactory()),
            formation=MagicMock(type=TrainingType.BACHELOR),
            profil_candidat_translator=self.profil_candidat_translator,
        )
        self.assertEqual(dto.pool, AcademicCalendarTypes.ADMISSION_POOL_EXTERNAL_REORIENTATION)
        self.assertEqual(dto.annee, 2022)

    @freezegun.freeze_time('2022-03-15')
    def test_verification_calendrier_inscription_reorientation_validee_hors_periode(self):
        # Nous ne sommes pas dans la période réorientation mais le candidat l'a validée
        proposition = PropositionFactory(est_bachelier_en_reorientation=True)
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        pool = None
        try:
            dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
                formation_id=proposition.formation_id,
                proposition=proposition,
                matricule_candidat=proposition.matricule_candidat,
                titres_acces=Titres(AdmissionConditionsDTOFactory()),
                formation=MagicMock(type=TrainingType.BACHELOR),
                profil_candidat_translator=self.profil_candidat_translator,
            )
            pool = dto.pool
        except AucunPoolCorrespondantException:
            pass
        self.assertNotEqual(pool, AcademicCalendarTypes.ADMISSION_POOL_EXTERNAL_REORIENTATION)

    @freezegun.freeze_time('2022-12-15')
    def test_verification_calendrier_inscription_reorientation_non_choisie(self):
        # Nous sommes dans la période réorientation et le candidat ne l'a pas choisi (mais répondu)
        proposition = PropositionFactory(est_reorientation_inscription_externe=False)
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        pool = None
        try:
            dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
                formation_id=proposition.formation_id,
                proposition=proposition,
                matricule_candidat=proposition.matricule_candidat,
                titres_acces=Titres(AdmissionConditionsDTOFactory()),
                formation=MagicMock(type=TrainingType.BACHELOR),
                profil_candidat_translator=self.profil_candidat_translator,
            )
            pool = dto.pool
        except AucunPoolCorrespondantException:
            pass
        self.assertNotEqual(pool, AcademicCalendarTypes.ADMISSION_POOL_EXTERNAL_REORIENTATION)

    def test_formation_contigentee_mais_residence_non_choisie(self):
        # Inscription à une formation contingentée, mais le candidat n'a pas renseigné sa résidence
        proposition = PropositionFactory(formation_id__sigle="VETE1BA", est_non_resident_au_sens_decret=None)
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        with self.assertRaises(ResidenceAuSensDuDecretNonRenseigneeException):
            CalendrierInscriptionInMemory.verifier(
                formation_id=proposition.formation_id,
                proposition=proposition,
                matricule_candidat=proposition.matricule_candidat,
                titres_acces=Titres(AdmissionConditionsDTOFactory()),
                formation=MagicMock(type=TrainingType.BACHELOR),
                profil_candidat_translator=self.profil_candidat_translator,
                formation_translator=self.formation_translator,
            )

    @freezegun.freeze_time('2022-03-15')
    def test_formation_contigentee_et_non_residence_validee_hors_periode(self):
        # Inscription à une formation contingentée et le candidat a validé sa non-résidence
        proposition = PropositionFactory(
            formation_id__sigle="VETE1BA",
            formation_id__annee=2022,
            est_non_resident_au_sens_decret=True,
        )
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        with self.assertRaises(PoolNonResidentContingenteNonOuvertException):
            CalendrierInscriptionInMemory.verifier(
                formation_id=proposition.formation_id,
                proposition=proposition,
                matricule_candidat=proposition.matricule_candidat,
                titres_acces=Titres(AdmissionConditionsDTOFactory()),
                formation=MagicMock(type=TrainingType.BACHELOR),
                profil_candidat_translator=self.profil_candidat_translator,
                formation_translator=self.formation_translator,
            )

    @freezegun.freeze_time('2022-06-02')
    def test_formation_contigentee_et_non_residence_validee_dans_periode(self):
        # Inscription à une formation contingentée et le candidat a validé sa non-résidence
        proposition = PropositionFactory(
            formation_id__annee=2022,
            formation_id__sigle="VETE1BA",
            est_non_resident_au_sens_decret=True,
        )
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
            formation_id=proposition.formation_id,
            proposition=proposition,
            matricule_candidat=proposition.matricule_candidat,
            titres_acces=Titres(AdmissionConditionsDTOFactory()),
            formation=MagicMock(type=TrainingType.BACHELOR),
            profil_candidat_translator=self.profil_candidat_translator,
        )
        self.assertEqual(dto.pool, AcademicCalendarTypes.ADMISSION_POOL_NON_RESIDENT_QUOTA)

    def test_formation_contigentee_et_residence(self):
        # Inscription à une formation contingentée et le candidat est résident
        proposition = PropositionFactory(formation_id__sigle="VETE1BA", est_non_resident_au_sens_decret=False)
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        pool = None
        try:
            dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
                formation_id=proposition.formation_id,
                proposition=proposition,
                matricule_candidat=proposition.matricule_candidat,
                titres_acces=Titres(AdmissionConditionsDTOFactory()),
                formation=MagicMock(type=TrainingType.BACHELOR),
                profil_candidat_translator=self.profil_candidat_translator,
            )
            pool = dto.pool
        except AucunPoolCorrespondantException:
            pass
        self.assertNotEqual(pool, AcademicCalendarTypes.ADMISSION_POOL_NON_RESIDENT_QUOTA)

    def test_determination_sans_adresse(self):
        proposition = PropositionFactory()
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        with self.assertRaises(AdresseDomicileLegalNonCompleteeException):
            CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
                formation_id=proposition.formation_id,
                proposition=proposition,
                matricule_candidat=proposition.matricule_candidat,
                titres_acces=Titres(AdmissionConditionsDTOFactory()),
                formation=MagicMock(type=TrainingType.BACHELOR),
                profil_candidat_translator=self.profil_candidat_translator,
            )

    def test_determination_sans_nationalite(self):
        proposition = PropositionFactory()
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat, identification__pays_nationalite=None)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        with self.assertRaises(IdentificationNonCompleteeException):
            CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
                formation_id=proposition.formation_id,
                proposition=proposition,
                matricule_candidat=proposition.matricule_candidat,
                titres_acces=Titres(AdmissionConditionsDTOFactory()),
                formation=MagicMock(type=TrainingType.BACHELOR),
                profil_candidat_translator=self.profil_candidat_translator,
            )

    @freezegun.freeze_time('22/09/2022')
    def test_formation_non_dispensee_annee_suivante(self):
        proposition = PropositionFactory(
            formation_id=FormationIdentityFactory(
                annee=2025,
                sigle='MA_FORMATION_NON_TROUVEE',
            )
        )
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        conditions = ITitresAcces.condition_matrix[(TrainingType.BACHELOR,)]
        with self.assertRaises(FormationNonTrouveeException):
            CalendrierInscriptionInMemory.verifier(
                formation_id=proposition.formation_id,
                proposition=proposition,
                matricule_candidat=proposition.matricule_candidat,
                titres_acces=Titres(AdmissionConditionsDTOFactory(diplomation_secondaire_belge=True), *conditions),
                formation=MagicMock(type=TrainingType.BACHELOR),
                profil_candidat_translator=self.profil_candidat_translator,
                formation_translator=self.formation_translator,
            )

    @freezegun.freeze_time('22/10/2021')
    def test_vip(self):
        proposition = PropositionFactory()
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat)
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        self.profil_candidat_translator.est_changement_etablissement = lambda *_: True
        dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
            formation_id=proposition.formation_id,
            proposition=proposition,
            matricule_candidat=proposition.matricule_candidat,
            titres_acces=Titres(AdmissionConditionsDTOFactory()),
            formation=MagicMock(type=TrainingType.MASTER_M1),
            profil_candidat_translator=self.profil_candidat_translator,
        )
        self.assertEqual(dto.pool, AcademicCalendarTypes.ADMISSION_POOL_VIP)

    @freezegun.freeze_time('22/09/2022')
    def test_changement_etablissement(self):
        proposition = PropositionFactory()
        profil = ProfilCandidatFactory(matricule=proposition.matricule_candidat, coordonnees__domicile_legal__pays="BE")
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        self.profil_candidat_translator.get_changements_etablissement = lambda *_: {2022: True}
        conditions = ITitresAcces.condition_matrix[(TrainingType.BACHELOR,)]
        dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
            formation_id=proposition.formation_id,
            proposition=proposition,
            matricule_candidat=proposition.matricule_candidat,
            titres_acces=Titres(AdmissionConditionsDTOFactory(diplomation_secondaire_belge=True), *conditions),
            formation=MagicMock(type=TrainingType.BACHELOR),
            profil_candidat_translator=self.profil_candidat_translator,
        )
        self.assertEqual(dto.pool, AcademicCalendarTypes.ADMISSION_POOL_INSTITUT_CHANGE)

    @freezegun.freeze_time('22/10/2022')
    def test_changement_filiere(self):
        proposition = PropositionFactory()
        profil = ProfilCandidatFactory(
            identification__annee_derniere_inscription_ucl=2021,
            matricule=proposition.matricule_candidat,
            coordonnees__domicile_legal__pays="AR",
            identification__pays_nationalite="AR",
        )
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
            formation_id=proposition.formation_id,
            proposition=proposition,
            matricule_candidat=proposition.matricule_candidat,
            titres_acces=Titres(AdmissionConditionsDTOFactory()),
            formation=MagicMock(type=TrainingType.BACHELOR),
            profil_candidat_translator=self.profil_candidat_translator,
        )
        self.assertEqual(dto.pool, AcademicCalendarTypes.ADMISSION_POOL_HUE_UCL_PATHWAY_CHANGE)

    @freezegun.freeze_time('01/03/2022')
    def test_ue5_belge(self):
        proposition = PropositionFactory()
        profil = ProfilCandidatFactory(
            matricule=proposition.matricule_candidat,
            identification__pays_nationalite="FR",
        )
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        conditions = ITitresAcces.condition_matrix[(TrainingType.BACHELOR,)]
        dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
            formation_id=proposition.formation_id,
            proposition=proposition,
            matricule_candidat=proposition.matricule_candidat,
            titres_acces=Titres(AdmissionConditionsDTOFactory(diplomation_secondaire_belge=True), *conditions),
            formation=MagicMock(type=TrainingType.BACHELOR),
            profil_candidat_translator=self.profil_candidat_translator,
        )
        self.assertEqual(dto.pool, AcademicCalendarTypes.ADMISSION_POOL_UE5_BELGIAN)

    @freezegun.freeze_time('01/03/2022')
    def test_ue5_belge_pour_certificat(self):
        proposition = PropositionFactory(
            avec_bourse_double_diplome=False,
            avec_bourse_internationale=False,
            avec_bourse_erasmus_mundus=False,
            bourse_double_diplome_id=None,
            bourse_internationale_id=None,
            bourse_erasmus_mundus_id=None,
        )
        profil = ProfilCandidatFactory(
            matricule=proposition.matricule_candidat,
            identification__pays_nationalite="FR",
        )
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
            formation_id=FormationFactory(type=TrainingType.CERTIFICATE).entity_id,
            proposition=proposition,
            matricule_candidat=proposition.matricule_candidat,
            titres_acces=Titres(AdmissionConditionsDTOFactory()),
            formation=MagicMock(type=TrainingType.CERTIFICATE),
            profil_candidat_translator=self.profil_candidat_translator,
        )
        self.assertEqual(dto.pool, AcademicCalendarTypes.ADMISSION_POOL_UE5_BELGIAN)

        proposition = PropositionFactory(
            avec_bourse_internationale=False,
            avec_bourse_erasmus_mundus=False,
            bourse_internationale_id=None,
            bourse_erasmus_mundus_id=None,
        )
        profil = ProfilCandidatFactory(
            matricule=proposition.matricule_candidat,
            identification__pays_nationalite="FR",
        )
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
            formation_id=FormationFactory(type=TrainingType.CERTIFICATE).entity_id,
            proposition=proposition,
            matricule_candidat=proposition.matricule_candidat,
            titres_acces=Titres(AdmissionConditionsDTOFactory()),
            formation=MagicMock(type=TrainingType.CERTIFICATE),
            profil_candidat_translator=self.profil_candidat_translator,
        )
        self.assertEqual(dto.pool, AcademicCalendarTypes.ADMISSION_POOL_VIP)

    @freezegun.freeze_time('22/10/2022')
    def test_ue5_non_belge(self):
        proposition = PropositionFactory()
        profil = ProfilCandidatFactory(
            matricule=proposition.matricule_candidat,
            identification__pays_nationalite="FR",
        )
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        conditions = ITitresAcces.condition_matrix[(TrainingType.BACHELOR,)]
        dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
            formation_id=proposition.formation_id,
            proposition=proposition,
            matricule_candidat=proposition.matricule_candidat,
            titres_acces=Titres(AdmissionConditionsDTOFactory(diplomation_secondaire_etranger=True), *conditions),
            formation=MagicMock(type=TrainingType.BACHELOR),
            profil_candidat_translator=self.profil_candidat_translator,
        )
        self.assertEqual(dto.pool, AcademicCalendarTypes.ADMISSION_POOL_UE5_NON_BELGIAN)

    @freezegun.freeze_time('22/10/2022')
    def test_hors_ue5_assimile(self):
        proposition = PropositionFactory(
            comptabilite__type_situation_assimilation=TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS
        )
        profil = ProfilCandidatFactory(
            matricule=proposition.matricule_candidat,
            identification__pays_nationalite="AR",
            coordonnees__domicile_legal__pays="AR",
        )

        conditions = ITitresAcces.condition_matrix[(TrainingType.BACHELOR,)]
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
            formation_id=proposition.formation_id,
            proposition=proposition,
            matricule_candidat=proposition.matricule_candidat,
            titres_acces=Titres(AdmissionConditionsDTOFactory(diplomation_secondaire_etranger=True), *conditions),
            formation=MagicMock(type=TrainingType.BACHELOR),
            profil_candidat_translator=self.profil_candidat_translator,
        )
        self.assertEqual(dto.pool, AcademicCalendarTypes.ADMISSION_POOL_UE5_NON_BELGIAN)

    @freezegun.freeze_time('22/10/2022')
    def test_hors_ue5_residence_belge(self):
        proposition = PropositionFactory()
        profil = ProfilCandidatFactory(
            matricule=proposition.matricule_candidat,
            identification__pays_nationalite="AR",
            coordonnees__domicile_legal__pays="BE",
        )
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
            formation_id=proposition.formation_id,
            proposition=proposition,
            matricule_candidat=proposition.matricule_candidat,
            titres_acces=Titres(AdmissionConditionsDTOFactory()),
            formation=MagicMock(type=TrainingType.BACHELOR),
            profil_candidat_translator=self.profil_candidat_translator,
        )
        self.assertEqual(dto.pool, AcademicCalendarTypes.ADMISSION_POOL_HUE5_BELGIUM_RESIDENCY)

    def test_hors_ue5_residence_etranger(self):
        proposition = PropositionFactory()
        profil = ProfilCandidatFactory(
            matricule=proposition.matricule_candidat,
            identification__pays_nationalite="AR",
            coordonnees__domicile_legal__pays="AR",
        )
        self.profil_candidat_translator.profil_candidats.append(profil.identification)
        self.profil_candidat_translator.get_coordonnees = lambda m: profil.coordonnees
        dto = CalendrierInscriptionInMemory.determiner_annee_academique_et_pot(
            formation_id=proposition.formation_id,
            proposition=proposition,
            matricule_candidat=proposition.matricule_candidat,
            titres_acces=Titres(AdmissionConditionsDTOFactory()),
            formation=MagicMock(type=TrainingType.BACHELOR),
            profil_candidat_translator=self.profil_candidat_translator,
        )
        self.assertEqual(dto.pool, AcademicCalendarTypes.ADMISSION_POOL_HUE5_FOREIGN_RESIDENCY)
