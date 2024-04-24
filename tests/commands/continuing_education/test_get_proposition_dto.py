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
import datetime
import uuid
from unittest.mock import patch

import freezegun
from django.conf import settings
from django.test import TestCase, override_settings
from osis_history.models import HistoryEntry
from django.utils.translation import override

from admission.contrib.models import ContinuingEducationAdmission
from admission.ddd.admission.dtos import AdressePersonnelleDTO
from admission.ddd.admission.dtos.campus import CampusDTO
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.formation_continue.commands import RecupererPropositionQuery
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
    ChoixTypeAdresseFacturation,
    ChoixMoyensDecouverteFormation,
    ChoixEdition,
)
from admission.ddd.admission.formation_continue.domain.validator.exceptions import PropositionNonTrouveeException
from admission.ddd.admission.formation_continue.dtos import PropositionDTO
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.student import StudentFactory
from infrastructure.messages_bus import message_bus_instance
from osis_profile import BE_ISO_CODE
from reference.tests.factories.country import CountryFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
@freezegun.freeze_time('2023-01-01')
class GetPropositionDTOTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.country = CountryFactory()
        cls.academic_years = {
            str(academic_year.year): academic_year
            for academic_year in AcademicYearFactory.produce(2023, number_past=2, number_future=2)
        }
        cls.other_country = CountryFactory()

    def setUp(self) -> None:
        school = EntityFactory()
        EntityVersionFactory(entity=school, acronym='SCH')

        self.admission: ContinuingEducationAdmission = ContinuingEducationAdmissionFactory(
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
            training__enrollment_campus__name='Louvain-la-Neuve',
            training__enrollment_campus__location='Allée des Etats-Unis',
            training__enrollment_campus__postal_code='1348',
            training__enrollment_campus__city='Louvain-la-Neuve',
            training__enrollment_campus__country=self.other_country,
            training__enrollment_campus__street='Place de l\'Université',
            training__enrollment_campus__postal_box='b1',
            training__enrollment_campus__street_number='1',
            training__enrollment_campus__sic_enrollment_email='sic@example.be',
            training__management_entity=school,
            candidate__private_email='john.doe@example.com',
            training__credits=180,
            candidate__country_of_citizenship=self.country,
            candidate__language=BE_ISO_CODE,
            determined_academic_year=self.academic_years['2023'],
            determined_pool=AcademicCalendarTypes.ADMISSION_POOL_EXTERNAL_REORIENTATION.name,
            submitted_at=datetime.datetime(2023, 2, 2),
            head_office_name='Center',
            unique_business_number='0123456782',
            vat_number='FR123456789',
            professional_email='john.doe.pro@example.com',
            billing_address_type=ChoixTypeAdresseFacturation.AUTRE.name,
            billing_address_street='Rue du Pin',
            billing_address_street_number='10',
            billing_address_postal_code='1340',
            billing_address_city='Louvain-la-Neuve',
            billing_address_country=self.other_country,
            billing_address_recipient='recipient@example.be',
            billing_address_postal_box='b1',
            motivations='Motivations',
            ways_to_find_out_about_the_course=[ChoixMoyensDecouverteFormation.AMIS.name],
            requested_documents='',
            interested_mark=True,
            edition=ChoixEdition.QUATRE.name,
            in_payement_order=False,
            reduced_rights=True,
            pay_by_training_cheque=False,
            cep=True,
            payement_spread=False,
            training_spread=True,
            experience_knowledge_valorisation=False,
            assessment_test_presented=True,
            assessment_test_succeeded=False,
            certificate_provided=True,
            tff_label='Label ttf',
        )

        self.teaching_campus = CampusFactory(
            name='Campus de Mons',
            location='Allée de Belgique',
            postal_code='7000',
            city='Mons',
            country=self.other_country,
            street='Place du Parc',
            postal_box='b2',
            street_number='20',
            sic_enrollment_email='sic_mons@example.be',
        )

        version = self.admission.training.educationgroupversion_set.first()
        version.root_group.main_teaching_campus = self.teaching_campus
        version.root_group.save()

        self.history_entry = HistoryEntry.objects.create(
            object_uuid=self.admission.uuid,
            tags=['proposition', 'status-changed'],
        )

        self.student = StudentFactory(person=self.admission.candidate)

        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("osis_document.api.utils.get_remote_metadata", return_value={"name": "myfile"})
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("osis_document.api.utils.confirm_remote_upload", return_value=str(uuid.uuid4()))
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            'osis_document.contrib.fields.FileField._confirm_multiple_upload',
            side_effect=lambda _, value, __: [str(uuid.uuid4())] if value else [],
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _get_command_result(self, uuid_proposition=None) -> PropositionDTO:
        return message_bus_instance.invoke(
            RecupererPropositionQuery(uuid_proposition=uuid_proposition or self.admission.uuid),
        )

    def test_get_proposition_dto_with_base_data(self):
        result = self._get_command_result()

        self.assertEqual(result.uuid, self.admission.uuid)
        self.assertEqual(
            result.formation,
            FormationDTO(
                sigle=self.admission.training.acronym,
                code=self.admission.training.partial_acronym,
                annee=self.admission.training.academic_year.year,
                date_debut=self.admission.training.academic_year.start_date,
                intitule=self.admission.training.title,
                intitule_fr=self.admission.training.title,
                intitule_en=self.admission.training.title_english,
                campus=CampusDTO(
                    nom=self.teaching_campus.name,
                    code_postal=self.teaching_campus.postal_code,
                    ville=self.teaching_campus.city,
                    pays_iso_code=self.teaching_campus.country.iso_code,
                    nom_pays=self.teaching_campus.country.name,
                    rue=self.teaching_campus.street,
                    numero_rue=self.teaching_campus.street_number,
                    boite_postale=self.teaching_campus.postal_box,
                    localisation=self.teaching_campus.location,
                    uuid=self.teaching_campus.uuid,
                    email_inscription_sic=self.teaching_campus.sic_enrollment_email,
                ),
                type=self.admission.training.education_group_type.name,
                code_domaine=self.admission.training.main_domain.code,
                campus_inscription=CampusDTO(
                    nom=self.admission.training.enrollment_campus.name,
                    code_postal=self.admission.training.enrollment_campus.postal_code,
                    ville=self.admission.training.enrollment_campus.city,
                    pays_iso_code=self.admission.training.enrollment_campus.country.iso_code,
                    nom_pays=self.admission.training.enrollment_campus.country.name,
                    rue=self.admission.training.enrollment_campus.street,
                    numero_rue=self.admission.training.enrollment_campus.street_number,
                    boite_postale=self.admission.training.enrollment_campus.postal_box,
                    localisation=self.admission.training.enrollment_campus.location,
                    uuid=self.admission.training.enrollment_campus.uuid,
                    email_inscription_sic=self.admission.training.enrollment_campus.sic_enrollment_email,
                ),
                sigle_entite_gestion='SCH',
                credits=180,
            ),
        )
        self.assertEqual(result.reference, f'L-SCH22-{self.admission}')
        self.assertEqual(result.annee_calculee, self.admission.determined_academic_year.year)
        self.assertEqual(result.pot_calcule, self.admission.determined_pool)
        self.assertEqual(result.date_fin_pot, None)
        self.assertEqual(result.creee_le, self.admission.created_at)
        self.assertEqual(result.modifiee_le, self.admission.modified_at)
        self.assertEqual(result.soumise_le, self.admission.submitted_at)
        self.assertEqual(result.erreurs, [])
        self.assertEqual(result.statut, self.admission.status)
        self.assertEqual(result.matricule_candidat, self.admission.candidate.global_id)
        self.assertEqual(result.prenom_candidat, self.admission.candidate.first_name)
        self.assertEqual(result.nom_candidat, self.admission.candidate.last_name)
        self.assertEqual(result.pays_nationalite_candidat, self.admission.candidate.country_of_citizenship.iso_code)
        self.assertEqual(
            result.pays_nationalite_ue_candidat,
            self.admission.candidate.country_of_citizenship.european_union,
        )
        self.assertEqual(result.nom_pays_nationalite_candidat, self.admission.candidate.country_of_citizenship.name)
        self.assertEqual(result.noma_candidat, self.student.registration_id)
        self.assertEqual(result.langue_contact_candidat, self.admission.candidate.language)
        self.assertEqual(result.adresse_email_candidat, self.admission.candidate.private_email)
        self.assertEqual(result.date_changement_statut, self.history_entry.created)
        self.assertEqual(result.candidat_a_plusieurs_demandes, False)
        self.assertEqual(result.reponses_questions_specifiques, self.admission.specific_question_answers)
        self.assertEqual(result.curriculum, self.admission.curriculum)
        self.assertEqual(result.equivalence_diplome, self.admission.diploma_equivalence)
        self.assertEqual(result.copie_titre_sejour, self.admission.residence_permit)
        self.assertEqual(result.documents_additionnels, self.admission.additional_documents)
        self.assertEqual(result.inscription_a_titre, self.admission.registration_as)
        self.assertEqual(result.nom_siege_social, self.admission.head_office_name)
        self.assertEqual(result.numero_unique_entreprise, self.admission.unique_business_number)
        self.assertEqual(result.numero_tva_entreprise, self.admission.vat_number)
        self.assertEqual(result.type_adresse_facturation, self.admission.billing_address_type)
        self.assertEqual(
            result.adresse_facturation,
            AdressePersonnelleDTO(
                rue=self.admission.billing_address_street,
                code_postal=self.admission.billing_address_postal_code,
                ville=self.admission.billing_address_city,
                pays=self.admission.billing_address_country.iso_code,
                nom_pays=self.admission.billing_address_country.name,
                numero_rue=self.admission.billing_address_street_number,
                boite_postale=self.admission.billing_address_postal_box,
                destinataire=self.admission.billing_address_recipient,
            ),
        )
        self.assertEqual(result.elements_confirmation, self.admission.confirmation_elements)
        self.assertEqual(result.pdf_recapitulatif, self.admission.pdf_recap)
        self.assertEqual(result.motivations, self.admission.motivations)
        self.assertEqual(result.moyens_decouverte_formation, self.admission.ways_to_find_out_about_the_course)
        self.assertEqual(result.documents_demandes, self.admission.requested_documents)
        self.assertEqual(result.marque_d_interet, self.admission.interested_mark)
        self.assertEqual(result.edition, self.admission.edition)
        self.assertEqual(result.en_ordre_de_paiement, self.admission.in_payement_order)
        self.assertEqual(result.droits_reduits, self.admission.reduced_rights)
        self.assertEqual(result.paye_par_cheque_formation, self.admission.pay_by_training_cheque)
        self.assertEqual(result.cep, self.admission.cep)
        self.assertEqual(result.etalement_des_paiments, self.admission.payement_spread)
        self.assertEqual(result.etalement_de_la_formation, self.admission.training_spread)
        self.assertEqual(result.valorisation_des_acquis_d_experience, self.admission.experience_knowledge_valorisation)
        self.assertEqual(result.a_presente_l_epreuve_d_evaluation, self.admission.assessment_test_presented)
        self.assertEqual(result.a_reussi_l_epreuve_d_evaluation, self.admission.assessment_test_succeeded)
        self.assertEqual(result.diplome_produit, self.admission.certificate_provided)
        self.assertEqual(result.intitule_du_tff, self.admission.tff_label)

    def test_get_proposition_with_missing_data(self):
        self.admission.candidate.country_of_citizenship = None

        self.admission.candidate.save()

        self.admission.determined_academic_year = None
        self.admission.billing_address_country = None
        self.admission.determined_academic_year = None

        self.admission.save()

        self.admission.training.enrollment_campus.country = None
        self.admission.training.enrollment_campus.save(update_fields=['country'])

        self.teaching_campus.country = None
        self.teaching_campus.save(update_fields=['country'])

        result = self._get_command_result()

        self.assertEqual(result.pays_nationalite_candidat, '')
        self.assertEqual(result.pays_nationalite_ue_candidat, None)
        self.assertEqual(result.nom_pays_nationalite_candidat, '')
        self.assertEqual(result.annee_calculee, None)
        self.assertEqual(result.adresse_facturation.pays, '')
        self.assertEqual(result.adresse_facturation.nom_pays, '')
        self.assertEqual(result.formation.campus_inscription.pays_iso_code, '')
        self.assertEqual(result.formation.campus_inscription.nom_pays, '')
        self.assertEqual(result.formation.campus.pays_iso_code, '')
        self.assertEqual(result.formation.campus.nom_pays, '')

        self.admission.training.enrollment_campus = None
        self.admission.training.save(update_fields=['enrollment_campus'])

        result = self._get_command_result()

        self.assertEqual(result.formation.campus_inscription, None)

    def test_get_proposition_with_english_translations(self):
        with override(settings.LANGUAGE_CODE_EN):
            result = self._get_command_result()

            self.assertEqual(result.formation.intitule, self.admission.training.title_english)
            self.assertEqual(result.formation.campus.nom_pays, self.teaching_campus.country.name_en)
            self.assertEqual(
                result.formation.campus_inscription.nom_pays,
                self.admission.training.enrollment_campus.country.name_en,
            )
            self.assertEqual(
                result.nom_pays_nationalite_candidat,
                self.admission.candidate.country_of_citizenship.name_en,
            )
            self.assertEqual(
                result.adresse_facturation.nom_pays,
                self.admission.billing_address_country.name_en,
            )

    def test_get_proposition_with_several_enrolments(self):
        second_admission = ContinuingEducationAdmissionFactory(
            candidate=self.admission.candidate,
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
            determined_academic_year=self.admission.determined_academic_year,
        )

        result = self._get_command_result()
        self.assertEqual(result.candidat_a_plusieurs_demandes, True)

        second_admission.status = ChoixStatutPropositionContinue.ANNULEE.name
        second_admission.save()

        result = self._get_command_result()
        self.assertEqual(result.candidat_a_plusieurs_demandes, False)

        second_admission.status = ChoixStatutPropositionContinue.EN_BROUILLON.name
        second_admission.save()

        result = self._get_command_result()
        self.assertEqual(result.candidat_a_plusieurs_demandes, False)

    def test_get_unknown_proposition_triggers_exception(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self._get_command_result(uuid_proposition=uuid.uuid4())
