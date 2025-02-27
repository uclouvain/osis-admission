# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
import uuid

import freezegun
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import (
    SpecifierInformationsAcceptationPropositionParSicCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
    DispenseOuDroitsMajores,
    DroitsInscriptionMontant,
    MobiliteNombreDeMois,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    ParcoursAnterieurNonSuffisantException,
    SituationPropositionNonSICException,
)
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPConfirmeeFactory,
)
from admission.ddd.admission.domain.model.complement_formation import (
    ComplementFormationIdentity,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import (
    AcademicYear,
    AcademicYearIdentity,
)
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import (
    AcademicYearInMemoryRepository,
)


@freezegun.freeze_time('2020-11-01')
class TestSpecifierInformationsAcceptationPropositionParSic(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.proposition_repository = PropositionInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.command = SpecifierInformationsAcceptationPropositionParSicCommand
        cls.uuid_experience = str(uuid.uuid4())
        academic_year_repository = AcademicYearInMemoryRepository()
        for annee in range(2020, 2022):
            academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )

    def setUp(self) -> None:
        self.proposition = PropositionAdmissionSC3DPConfirmeeFactory(
            statut=ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC,
            est_confirmee=True,
            est_approuvee_par_fac=True,
        )
        self.proposition_repository.save(self.proposition)
        self.parametres_commande_par_defaut = {
            'uuid_proposition': 'uuid-SC3DP-confirmee',
            'avec_complements_formation': False,
            'uuids_complements_formation': [],
            'commentaire_complements_formation': '',
            'nom_personne_contact_programme_annuel': '',
            'email_personne_contact_programme_annuel': '',
            'droits_inscription_montant': '',
            'droits_inscription_montant_autre': None,
            'dispense_ou_droits_majores': '',
            'est_mobilite': None,
            'nombre_de_mois_de_mobilite': '',
            'doit_se_presenter_en_sic': None,
            'communication_au_candidat': '',
            'gestionnaire': '0123456789',
        }

    def test_should_etre_ok_avec_min_informations(self):
        self.proposition.statut = ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC
        self.proposition.checklist_actuelle.parcours_anterieur.statut = ChoixStatutChecklist.GEST_REUSSITE

        resultat = self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        # Vérifier résultat de la commande
        self.assertEqual(resultat.uuid, 'uuid-SC3DP-confirmee')

        # Vérifier la proposition
        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.checklist_actuelle.decision_sic.statut, ChoixStatutChecklist.GEST_EN_COURS)
        self.assertEqual(
            proposition.checklist_actuelle.decision_sic.extra,
            {'en_cours': 'approval'},
        )
        self.assertEqual(proposition.avec_complements_formation, False)
        self.assertEqual(proposition.complements_formation, [])
        self.assertEqual(proposition.commentaire_complements_formation, '')
        self.assertEqual(proposition.nom_personne_contact_programme_annuel_annuel, '')
        self.assertEqual(proposition.email_personne_contact_programme_annuel_annuel, '')
        self.assertIsNone(proposition.droits_inscription_montant)
        self.assertIsNone(proposition.droits_inscription_montant_autre)
        self.assertIsNone(proposition.dispense_ou_droits_majores)
        self.assertIsNone(proposition.est_mobilite)
        self.assertIsNone(proposition.nombre_de_mois_de_mobilite)
        self.assertIsNone(proposition.doit_se_presenter_en_sic)
        self.assertEqual(proposition.communication_au_candidat, '')

    def test_should_lever_exception_si_statut_proposition_non_valide(self):
        self.proposition.checklist_actuelle.parcours_anterieur.statut = ChoixStatutChecklist.GEST_REUSSITE
        self.proposition.statut = ChoixStatutPropositionDoctorale.TRAITEMENT_FAC

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        self.assertIsInstance(context.exception.exceptions.pop(), SituationPropositionNonSICException)

    def test_should_lever_exception_si_parcours_anterieur_non_suffisant(self):
        self.proposition.statut = ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC
        self.proposition.checklist_actuelle.parcours_anterieur.statut = ChoixStatutChecklist.GEST_EN_COURS

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.command(**self.parametres_commande_par_defaut))

        self.assertIsInstance(context.exception.exceptions.pop(), ParcoursAnterieurNonSuffisantException)

    def test_should_etre_ok_si_completee_avec_max_informations(self):
        self.proposition.statut = ChoixStatutPropositionDoctorale.COMPLETEE_POUR_SIC
        self.proposition.checklist_actuelle.parcours_anterieur.statut = ChoixStatutChecklist.GEST_REUSSITE
        self.proposition.annee_calculee = 2020

        # Maximum d'informations données
        resultat = self.message_bus.invoke(
            self.command(
                uuid_proposition='uuid-SC3DP-confirmee',
                avec_complements_formation=True,
                uuids_complements_formation=['uuid-complement-formation-1'],
                commentaire_complements_formation='Mon commentaire concernant les compléments de formation',
                nom_personne_contact_programme_annuel='John Doe',
                email_personne_contact_programme_annuel='john.doe@uclouvain.be',
                droits_inscription_montant=DroitsInscriptionMontant.ANCIENS_DROITS_MAJORES_2505.name,
                droits_inscription_montant_autre=None,
                dispense_ou_droits_majores='DISPENSE_DUREE',
                est_mobilite=True,
                nombre_de_mois_de_mobilite=MobiliteNombreDeMois.SIX.name,
                doit_se_presenter_en_sic=False,
                communication_au_candidat='Communication',
                gestionnaire='0123456789',
            )
        )

        proposition = self.proposition_repository.get(resultat)
        self.assertEqual(proposition.checklist_actuelle.decision_sic.statut, ChoixStatutChecklist.GEST_EN_COURS)
        self.assertEqual(
            proposition.checklist_actuelle.decision_sic.extra,
            {'en_cours': 'approval'},
        )
        self.assertEqual(proposition.avec_complements_formation, True)
        self.assertEqual(
            proposition.complements_formation,
            [
                ComplementFormationIdentity(
                    uuid='uuid-complement-formation-1',
                )
            ],
        )
        self.assertEqual(
            proposition.commentaire_complements_formation,
            'Mon commentaire concernant les compléments de formation',
        )
        self.assertEqual(proposition.nom_personne_contact_programme_annuel_annuel, 'John Doe')
        self.assertEqual(proposition.email_personne_contact_programme_annuel_annuel, 'john.doe@uclouvain.be')
        self.assertEqual(proposition.droits_inscription_montant, DroitsInscriptionMontant.ANCIENS_DROITS_MAJORES_2505)
        self.assertIsNone(proposition.droits_inscription_montant_autre)
        self.assertEqual(proposition.dispense_ou_droits_majores, DispenseOuDroitsMajores.DISPENSE_DUREE)
        self.assertIs(proposition.est_mobilite, True)
        self.assertEqual(proposition.nombre_de_mois_de_mobilite, MobiliteNombreDeMois.SIX)
        self.assertIs(proposition.doit_se_presenter_en_sic, False)
        self.assertEqual(proposition.communication_au_candidat, 'Communication')
