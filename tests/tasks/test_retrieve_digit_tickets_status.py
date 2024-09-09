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
import copy
import uuid
from datetime import datetime, timedelta
from unittest import mock

from django.test import TestCase
from django.test.utils import override_settings
from waffle.testutils import override_switch

from admission.auth.roles.candidate import Candidate
from admission.ddd.admission.commands import RetrieveListeTicketsEnAttenteQuery, \
    RetrieveAndStoreStatutTicketPersonneFromDigitCommand, RecupererMatriculeDigitQuery
from admission.ddd.admission.dtos.statut_ticket_personne import StatutTicketPersonneDTO
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.tasks import retrieve_digit_tickets_status
from admission.tests.factories.curriculum import ProfessionalExperienceFactory, EducationalExperienceFactory, \
    EducationalExperienceYearFactory
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.secondary_studies import BelgianHighSchoolDiplomaFactory
from base.models.enums.civil_state import CivilState
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
from base.models.person_address import PersonAddress
from base.models.person_creation_ticket import PersonTicketCreation, PersonTicketCreationStatus
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_address import PersonAddressFactory
from base.tests.factories.user import UserFactory
from osis_profile.models import ProfessionalExperience, EducationalExperience
from osis_profile.models.enums.curriculum import ActivityType


@override_switch('fusion-digit', active=True)
@override_settings(USE_CELERY=False)
class TestRetrieveDigitTicketsStatus(TestCase):
    def setUp(self):
        self.personne_compte_temporaire = PersonFactory(global_id='89745632')
        self.personne_compte_temporaire_address = PersonAddressFactory(
            person=self.personne_compte_temporaire,
            label = PersonAddressType.RESIDENTIAL.name
        )
        self.addresse_residentielle_personne_temporaire = PersonAddressFactory(
            person=self.personne_compte_temporaire,
            label=PersonAddressType.RESIDENTIAL.name
        )
        self.person_merge_proposal = PersonMergeProposal.objects.create(
            uuid=uuid.uuid4(),
            original_person=self.personne_compte_temporaire,
            proposal_merge_person=None,
            status=PersonMergeStatus.NO_MATCH.name,
            registration_id_sent_to_digit='2456045984',
            similarity_result=[],
            last_similarity_result_update=datetime.now(),
            professional_curex_to_merge=[],
            educational_curex_to_merge=[],
            validation={'valid': 'true', 'errors': []}
        )
        self.ticket_digit = PersonTicketCreation.objects.create(
            uuid=uuid.uuid4(),
            status=PersonTicketCreationStatus.CREATED.name,
            person=self.personne_compte_temporaire,
        )

        # Dossier d'admission
        self.admission = GeneralEducationAdmissionFactory(
            candidate=self.personne_compte_temporaire,
            type_demande=TypeDemande.INSCRIPTION.name,
        )
        # Experience professionelle
        self.experience_professionelle = ProfessionalExperienceFactory(
            start_date=datetime.now() - timedelta(days=20),
            end_date=datetime.now() - timedelta(days=10),
            type=ActivityType.WORK.name,
            person=self.personne_compte_temporaire,
        )
        self.experience_academique = EducationalExperienceFactory(person=self.personne_compte_temporaire)
        EducationalExperienceYearFactory(educational_experience=self.experience_academique)

        # Etudes secondaires
        self.etudes_secondaires_candidat = BelgianHighSchoolDiplomaFactory(person=self.personne_compte_temporaire)

        self._mock_message_bus()
        self._mock_injection_signaletique()
        self._mock_envoyer_queue()

    def _mock_message_bus(self):
        self.patch_message_bus = mock.patch(
            'infrastructure.messages_bus.message_bus_instance.invoke',
            side_effect=self.__mock_message_bus_invoke
        )
        self.message_bus_mocked = self.patch_message_bus.start()
        self.addCleanup(self.patch_message_bus.stop)

    def _mock_injection_signaletique(self):
        self.patch_injection_signaletique = mock.patch(
            'admission.tasks.retrieve_digit_tickets_status._injecter_signaletique_a_epc',
            side_effect=None
        )
        self.injection_signaletique_mocked = self.patch_injection_signaletique.start()
        self.addCleanup(self.patch_injection_signaletique.stop)

    def _mock_envoyer_queue(self):
        self.patch_envoyer_queue = mock.patch(
            'osis_profile.services.injection_epc.InjectionEPCCurriculum.envoyer_curriculum_dans_queue',
            side_effect=None
        )
        self.envoyer_queue_mocked = self.patch_envoyer_queue.start()
        self.addCleanup(self.patch_envoyer_queue.stop)

    def __mock_message_bus_invoke(self, cmd):
        if isinstance(cmd, RetrieveListeTicketsEnAttenteQuery):
            return [
                StatutTicketPersonneDTO(
                    uuid=self.ticket_digit.uuid,
                    request_id=None,
                    matricule=self.ticket_digit.person.global_id,
                    noma='47602400',
                    nom=self.ticket_digit.person.last_name,
                    prenom=self.ticket_digit.person.first_name,
                    statut=self.ticket_digit.status,
                    type_fusion=self.ticket_digit.merge_type,
                    errors=[],
                )
            ]
        elif isinstance(cmd, RetrieveAndStoreStatutTicketPersonneFromDigitCommand):
            self.ticket_digit.status = PersonTicketCreationStatus.DONE.name
            self.ticket_digit.request_id = '1234567'
            self.ticket_digit.save()
            return self.ticket_digit.status
        elif isinstance(cmd, RecupererMatriculeDigitQuery):
            return "00345678"
        raise Exception(f"Unknown command {cmd}")

    def test_assert_change_global_id_and_external_id_and_address_external_id_when_person_is_not_known(self):
        retrieve_digit_tickets_status.run()

        # Ticket DigIT
        self.ticket_digit.refresh_from_db()
        self.assertEqual(self.ticket_digit.status, PersonTicketCreationStatus.DONE.name)

        self.personne_compte_temporaire.refresh_from_db()
        self.assertEqual(self.personne_compte_temporaire.global_id, '00345678')
        self.assertEqual(self.personne_compte_temporaire.external_id, 'osis.person_00345678')
        self.addresse_residentielle_personne_temporaire.refresh_from_db()
        self.assertEqual(self.addresse_residentielle_personne_temporaire.external_id, 'osis.student_address_STUDENT_00345678_RESIDENTIAL')

    def test_assert_do_not_change_global_id_nor_external_id_nor_address_when_known_person_exists(self):

        personne_connue = PersonFactory(global_id='00345678')
        retrieve_digit_tickets_status.run()

        # Ticket DigIT
        self.ticket_digit.refresh_from_db()
        self.assertEqual(self.ticket_digit.status, PersonTicketCreationStatus.DONE.name)

        self.personne_compte_temporaire.refresh_from_db()
        self.assertEqual(self.personne_compte_temporaire.global_id, '89745632')
        self.assertFalse(self.personne_compte_temporaire.external_id)
        self.addresse_residentielle_personne_temporaire.refresh_from_db()
        self.assertFalse(self.addresse_residentielle_personne_temporaire.external_id)

    def test_assert_merge_with_existing_account_and_existing_in_osis(self):
        self.personne_compte_temporaire.global_id = '00345678'   # Set as internal account
        self.personne_compte_temporaire.save()

        personne_connue = PersonFactory(global_id='00948959')
        personne_connue_address = PersonAddressFactory(
            person=personne_connue,
            label=PersonAddressType.RESIDENTIAL.name
        )


        self.etudes_secondaires_personne_connue = BelgianHighSchoolDiplomaFactory(person=personne_connue)
        self.experience_professionelle_personne_connue_gardee = ProfessionalExperienceFactory(
            start_date=datetime.now() - timedelta(days=9),
            end_date=datetime.now() - timedelta(days=8),
            type=ActivityType.OTHER.name,
            person=personne_connue,
        )
        self.experience_academique_personne_connue_gardee = EducationalExperienceFactory(person=personne_connue)
        EducationalExperienceYearFactory(educational_experience=self.experience_academique_personne_connue_gardee)

        self.experience_professionelle_personne_connue_non_gardee = ProfessionalExperienceFactory(
            start_date=datetime.now() - timedelta(days=9),
            end_date=datetime.now() - timedelta(days=8),
            type=ActivityType.OTHER.name,
            person=personne_connue,
        )
        self.experience_academique_personne_connue_non_gardee = EducationalExperienceFactory(person=personne_connue)
        EducationalExperienceYearFactory(educational_experience=self.experience_academique_personne_connue_non_gardee)

        self.person_merge_proposal.status = PersonMergeStatus.IN_PROGRESS.name   # Fusion acceptée par le gestionnaire
        self.person_merge_proposal.selected_global_id = personne_connue.global_id
        self.person_merge_proposal.proposal_merge_person = PersonFactory(
            global_id='',
            last_name='Durant',
            first_name='Thomas',
            middle_name='',
            birth_date=None,
            birth_place='',
            email='thomas.durant@gmail.com',
            gender='M',
            sex='M',
            civil_state=CivilState.SINGLE.name,
            country_of_citizenship=None,
            national_number='',
            id_card_number='',
            passport_number='',
            last_registration_id='',
            id_card_expiry_date=None,
            passport_expiry_date=None,
            emergency_contact_phone='', # champ non modifié par la fusion car pas connu de digit
        )
        self.person_merge_proposal.professional_curex_to_merge = [
            str(self.experience_professionelle_personne_connue_gardee.uuid)
        ]
        self.person_merge_proposal.educational_curex_to_merge = [
            str(self.experience_academique_personne_connue_gardee.uuid)
        ]
        self.person_merge_proposal.save()

        retrieve_digit_tickets_status.run()

        # Ticket DigIT
        self.ticket_digit.refresh_from_db()
        self.assertEqual(self.ticket_digit.status, PersonTicketCreationStatus.DONE.name)

        # Proposition Fusion
        self.person_merge_proposal.refresh_from_db()
        self.assertEqual(self.person_merge_proposal.status, PersonMergeStatus.MERGED.name)
        self.assertIsNone(
            self.person_merge_proposal.proposal_merge_person,
            msg="Doit être supprimée car information fusionnée avec la personne connue",
        )
        self.assertEqual(self.person_merge_proposal.selected_global_id, '')
        self.assertEqual(self.person_merge_proposal.original_person, personne_connue)

        # Personne connue
        personne_connue.refresh_from_db()
        self.assertEqual(personne_connue.global_id, '00948959')
        self.assertEqual(
            personne_connue.last_name,
            'Durant',
            msg="Donnée provenant de la proposition de fusion (aka. proposal_merge_person) qui n'est pas vide",
        )
        self.assertEqual(
            personne_connue.first_name,
            'Thomas',
            msg="Donnée provenant de la proposition de fusion (aka. proposal_merge_person) qui n'est pas vide",
        )
        self.assertEqual(
            personne_connue.private_email,
            self.personne_compte_temporaire.private_email,
            msg="Donnée provenant du candidat (aka. original_person) qui n'est pas vide",
        )
        self.assertEqual(
            personne_connue.sex,
            'M',
            msg="Donnée provenant de la proposition de fusion (aka. proposal_merge_person) qui n'est pas vide",
        )
        self.assertEqual(
            personne_connue.gender,
            'M',
            msg="Donnée provenant du candidat (aka. original_person) qui n'est pas vide",
        )
        self.assertEqual(
            personne_connue.emergency_contact_phone,
            self.personne_compte_temporaire.emergency_contact_phone,
            msg="Donnée provenant du candidat (aka. original_person) qui n'est pas vide",
        )

        # Admission
        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.candidate_id,
            personne_connue.pk,
            msg="Admission doit être reliée à la personne connue",
        )

        # Fusion des experiences
        self.experience_professionelle.refresh_from_db()
        self.assertEqual(
            self.experience_professionelle.person_id,
            personne_connue.pk,
            msg="L'experience professionelle doit être reliée à la personne connue car vient du candidat",
        )

        self.experience_academique.refresh_from_db()
        self.assertEqual(
            self.experience_academique.person_id,
            personne_connue.pk,
            msg="L'experience académique doit être reliée à la personne connue car vient du candidat",
        )

        self.experience_professionelle_personne_connue_gardee.refresh_from_db()
        self.assertEqual(
            self.experience_professionelle_personne_connue_gardee.person_id,
            personne_connue.pk,
            msg="L'experience professionelle gardée est conservée car dans 'professional_curex_to_merge'",
        )

        self.experience_academique_personne_connue_gardee.refresh_from_db()
        self.assertEqual(
            self.experience_academique_personne_connue_gardee.person_id,
            personne_connue.pk,
            msg="L'experience académique gardée est conservée car dans 'educational_curex_to_merge'",
        )

        # l'expérience gardée de la personne connue est valorisée dans le dossier d'admission
        for professional_valuated_experience  in self.experience_professionelle_personne_connue_gardee.professional_valuated_experiences.all(): # noqa
            self.assertEqual(professional_valuated_experience.baseadmission.reference, self.admission.reference)
        for educational_valuated_experience in self.experience_academique_personne_connue_gardee.educational_valuated_experiences.all(): # noqa
            self.assertEqual(educational_valuated_experience.baseadmission.reference, self.admission.reference)

        with self.assertRaises(
            ProfessionalExperience.DoesNotExist,
            msg="L'experience professionelle non gardée doit être effacée car pas dans 'professional_curex_to_merge' "
        ):
            self.experience_professionelle_personne_connue_non_gardee.refresh_from_db()

        with self.assertRaises(
            EducationalExperience.DoesNotExist,
            msg="L'experience academique non gardée doit être effacée car pas dans 'educational_curex_to_merge' "
        ):
            self.experience_academique_personne_connue_non_gardee.refresh_from_db()

        # remplacement des études secondaires de la personne connue par celles du candidat
        self.etudes_secondaires_candidat.refresh_from_db()
        self.assertEqual(self.etudes_secondaires_candidat.person, personne_connue)

        # remplacement addresse personne connue par celle du candidat
        with self.assertRaises(
            PersonAddress.DoesNotExist,
            msg="L'adresse de la personne connue doit être effacée pour être remplacée par celle du candidat"
        ):
            personne_connue_address.refresh_from_db()
        self.personne_compte_temporaire_address.refresh_from_db()
        self.assertEqual(self.personne_compte_temporaire_address.person, personne_connue)
        self.assertIsNotNone(self.personne_compte_temporaire_address.external_id)

        self.assertTrue(
            self.envoyer_queue_mocked.called,
            msg="Suppression envoyée via la queue car il y a des expériences connues à supprimer"
        )


    def test_assert_merge_with_existing_account_but_not_existing_in_osis(self):
        self.personne_compte_temporaire.global_id = '00345678'   # Set as internal account
        self.personne_compte_temporaire.save()

        self.person_merge_proposal.status = PersonMergeStatus.IN_PROGRESS.name  # Fusion acceptée par le gestionnaire
        self.person_merge_proposal.selected_global_id = '00825759'
        self.person_merge_proposal.proposal_merge_person = PersonFactory(
            global_id='',
            last_name='Varky',
            first_name='Louis',
            middle_name='',
            birth_date=None,
            birth_place='',
            email='louis.varky@hotmail.com',
            gender='M',
            sex='M',
            civil_state=CivilState.MARRIED.name,
            country_of_citizenship=None,
            national_number='',
            id_card_number='',
            passport_number='',
            last_registration_id='',
            id_card_expiry_date=None,
            passport_expiry_date=None,
        )
        self.person_merge_proposal.professional_curex_to_merge = [
            str(self.experience_professionelle.uuid),
        ]
        self.person_merge_proposal.educational_curex_to_merge = [
            str(self.experience_academique.uuid),
        ]
        self.person_merge_proposal.save()

        retrieve_digit_tickets_status.run()

        # Ticket DigIT
        self.ticket_digit.refresh_from_db()
        self.assertEqual(self.ticket_digit.status, PersonTicketCreationStatus.DONE.name)

        # Proposition Fusion
        self.person_merge_proposal.refresh_from_db()
        self.assertEqual(self.person_merge_proposal.status, PersonMergeStatus.MERGED.name)
        self.assertIsNone(
            self.person_merge_proposal.proposal_merge_person,
            msg="Doit être supprimée car information fusionnée avec la personne connue",
        )
        self.assertEqual(self.person_merge_proposal.selected_global_id, '')

        # Personne connue
        personne_connue_creee = Person.objects.get(global_id='00825759')
        self.assertEqual(
            personne_connue_creee.external_id,
            "osis.person_00825759",
            msg="External id doit être = au global_id afin d'éviter des soucis avec la synchro",
        )
        self.assertEqual(
            personne_connue_creee.last_name,
            'Varky',
            msg="Donnée provenant de la proposition de fusion (aka. proposal_merge_person) qui n'est pas vide",
        )
        self.assertEqual(
            personne_connue_creee.first_name,
            'Louis',
            msg="Donnée provenant de la proposition de fusion (aka. proposal_merge_person) qui n'est pas vide",
        )
        self.assertEqual(
            personne_connue_creee.sex,
            'M',
            msg="Donnée provenant de la proposition de fusion (aka. proposal_merge_person) qui n'est pas vide",
        )
        self.assertEqual(
            personne_connue_creee.gender,
            'M',
            msg="Donnée provenant de la proposition de fusion (aka. proposal_merge_person) qui n'est pas vide",
        )

        # Admission
        self.admission.refresh_from_db()
        self.assertEqual(
            self.admission.candidate_id,
            personne_connue_creee.pk,
            msg="Admission doit être reliée à la personne connue",
        )

        # Fusion des experiences
        self.experience_professionelle.refresh_from_db()
        self.assertEqual(
            self.experience_professionelle.person_id,
            personne_connue_creee.pk,
            msg="L'experience professionelle doit être reliée à la personne connue car vient du candidat",
        )

        self.experience_academique.refresh_from_db()
        self.assertEqual(
            self.experience_academique.person_id,
            personne_connue_creee.pk,
            msg="L'experience académique doit être reliée à la personne connue car vient du candidat",
        )

        self.assertFalse(
            self.envoyer_queue_mocked.called,
            msg="Pas de suppression envoyée via la queue car pas d'expérience connue à supprimer"
        )

        # Address
        self.personne_compte_temporaire_address.refresh_from_db()
        self.assertIsNotNone(self.personne_compte_temporaire_address)
        self.assertIsNotNone(self.personne_compte_temporaire_address.external_id)


    def test_assert_merge_with_duplicate_candidate_account_created_by_candidate_and_existing_in_osis(self):
        self.personne_compte_temporaire.global_id = '00345678'  # Set as internal account
        self.personne_compte_temporaire.save()

        # on considere que la premiere personne a déjà été mergée
        self.person_merge_proposal.delete()


        # simulate creation of a duplicate account
        self.doublon_personne_compte_temporaire = copy.deepcopy(self.personne_compte_temporaire)
        self.doublon_personne_compte_temporaire.global_id = '80000001'
        self.doublon_personne_compte_temporaire.user = UserFactory()
        self.doublon_personne_compte_temporaire.pk = None
        self.doublon_personne_compte_temporaire.uuid = uuid.uuid4()
        self.doublon_personne_compte_temporaire.save()
        Candidate.objects.create(person=self.doublon_personne_compte_temporaire)

        self.person_merge_proposal_doublon = PersonMergeProposal.objects.create(
            uuid=uuid.uuid4(),
            original_person=self.doublon_personne_compte_temporaire,
            proposal_merge_person=None,
            status=PersonMergeStatus.IN_PROGRESS.name,
            registration_id_sent_to_digit='2456045984',
            similarity_result=[],
            last_similarity_result_update=datetime.now(),
            professional_curex_to_merge=[],
            educational_curex_to_merge=[],
            validation={'valid': 'true', 'errors': []}
        )
        self.ticket_digit = PersonTicketCreation.objects.create(
            uuid=uuid.uuid4(),
            status=PersonTicketCreationStatus.CREATED.name,
            person=self.doublon_personne_compte_temporaire,
        )

        # Dossier d'admission
        self.admission = GeneralEducationAdmissionFactory(
            candidate=self.doublon_personne_compte_temporaire,
            type_demande=TypeDemande.INSCRIPTION.name,
        )

        self.person_merge_proposal_doublon.status = PersonMergeStatus.IN_PROGRESS.name   # Fusion acceptée par le gestionnaire
        self.person_merge_proposal_doublon.selected_global_id = self.personne_compte_temporaire.global_id
        self.person_merge_proposal_doublon.original_person = self.doublon_personne_compte_temporaire
        self.person_merge_proposal_doublon.proposal_merge_person = PersonFactory(
            global_id='',
            last_name=self.personne_compte_temporaire.last_name,
            first_name=self.personne_compte_temporaire.first_name,
            middle_name='',
            birth_date=None,
            birth_place='',
            email=self.personne_compte_temporaire.email,
            gender='M',
            sex='M',
            civil_state=CivilState.SINGLE.name,
            country_of_citizenship=None,
            national_number='',
            id_card_number='',
            passport_number='',
            last_registration_id='',
            id_card_expiry_date=None,
            passport_expiry_date=None,
            emergency_contact_phone='', # champ non modifié par la fusion car pas connu de digit
        )
        self.person_merge_proposal_doublon.save()

        self.candidat_original = Candidate.objects.get(person=self.personne_compte_temporaire)
        self.candidat_doublon = Candidate.objects.get(person=self.doublon_personne_compte_temporaire)

        retrieve_digit_tickets_status.run()

        with self.assertRaises(
                Candidate.DoesNotExist,
                msg="Si le rôle candidat existe déjà pour la personne, on supprime celui du candidat"
        ):
            self.candidat_doublon.refresh_from_db()

        self.assertTrue(
            self.envoyer_queue_mocked.called,
            msg="Suppression envoyée via la queue car il y a des expériences connues à supprimer"
        )


    def test_assert_in_error_when_internal_global_id_is_different_from_digit_global_id(self):
        self.personne_compte_temporaire.global_id = '00746799'
        self.personne_compte_temporaire.save()

        retrieve_digit_tickets_status.run()

        # Ticket DigIT
        self.ticket_digit.refresh_from_db()
        self.assertEqual(
            self.ticket_digit.status,
            PersonTicketCreationStatus.ERROR.name,
            msg="Doit être en erreur car situation anormale que le compte interne (global_id = XXX) "
                "n'est pas le meme que celui que DigIT renvoie sur base du noma"
        )

    def test_assert_in_error_when_ticket_in_error_before_current(self):
        ticket_digit_anterieur = PersonTicketCreation.objects.create(
            uuid=uuid.uuid4(),
            status=PersonTicketCreationStatus.ERROR.name,
            person=self.personne_compte_temporaire,
        )
        ticket_digit_anterieur.created_at = self.ticket_digit.created_at - timedelta(days=1)
        ticket_digit_anterieur.save()

        retrieve_digit_tickets_status.run()

        # Ticket DigIT
        self.ticket_digit.refresh_from_db()
        self.assertEqual(
            self.ticket_digit.status,
            PersonTicketCreationStatus.ERROR.name,
            msg="Doit être en erreur car situation anormale, un ticket est lancé avant un ticket antérieur DigIT"
        )

    def test_assert_process_when_tickets_before_are_done(self):
        ticket_digit_anterieur = PersonTicketCreation.objects.create(
            uuid=uuid.uuid4(),
            status=PersonTicketCreationStatus.DONE_WITH_WARNINGS.name,
            person=self.personne_compte_temporaire,
        )
        ticket_digit_anterieur.created_at = self.ticket_digit.created_at - timedelta(days=1)
        ticket_digit_anterieur.save()

        retrieve_digit_tickets_status.run()

        # Ticket DigIT
        self.ticket_digit.refresh_from_db()
        self.assertEqual(
            self.ticket_digit.status,
            PersonTicketCreationStatus.DONE.name,
            msg="Doit être ok car les tickets antérieurs sont DONE/DONE WITH WARNINGS"
        )
