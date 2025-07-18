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
from typing import Optional
from unittest import TestCase, mock

import freezegun

from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AnneesCurriculumNonSpecifieesException,
    ExperiencesAcademiquesNonCompleteesException,
)
from admission.ddd.admission.dtos.etudes_secondaires import (
    EtudesSecondairesAdmissionDTO,
)
from admission.ddd.admission.formation_generale.commands import (
    VerifierCurriculumApresSoumissionQuery,
)
from admission.ddd.admission.formation_generale.domain.builder.proposition_identity_builder import (
    PropositionIdentityBuilder,
)
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import (
    AnneeExperienceAcademique,
    ExperienceAcademique,
    ExperienceNonAcademique,
    ProfilCandidatInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.enums.community import CommunityEnum
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import (
    AcademicYear,
    AcademicYearIdentity,
)
from epc.models.enums.etat_inscription import EtatInscriptionFormation
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import (
    AcademicYearInMemoryRepository,
)
from infrastructure.shared_kernel.profil.domain.service.in_memory.parcours_interne import (
    ExperienceParcoursInterneInMemoryTranslator,
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
from osis_profile.tests.factories.curriculum import (
    AnneeExperienceParcoursInterneDTOFactory,
    ExperienceParcoursInterneDTOFactory,
)
from reference.models.enums.cycle import Cycle


class TestVerifierCurriculumApresSoumissionService(TestCase):
    experience_academiques_complete: Optional[ExperienceAcademique] = None

    def assertHasInstance(self, container, cls, msg=None):
        if not any(isinstance(obj, cls) for obj in container):
            self.fail(msg or f"No instance of '{cls}' has been found")

    def assertHasNoInstance(self, container, cls, msg=None):
        if any(isinstance(obj, cls) for obj in container):
            self.fail(msg or f"Instance of '{cls}' has been found")

    @classmethod
    def setUpClass(cls) -> None:
        cls.experience_academiques_complete = ExperienceAcademique(
            personne='0000000001',
            communaute_fr=True,
            pays=BE_ISO_CODE,
            annees=[
                AnneeExperienceAcademique(
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2011,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                    credits_inscrits=10,
                    credits_acquis=10,
                ),
                AnneeExperienceAcademique(
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2013,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                    credits_inscrits=10,
                    credits_acquis=10,
                ),
                AnneeExperienceAcademique(
                    uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                    annee=2014,
                    resultat=Result.SUCCESS.name,
                    releve_notes=['releve_notes.pdf'],
                    traduction_releve_notes=['traduction_releve_notes.pdf'],
                    credits_inscrits=10,
                    credits_acquis=10,
                ),
            ],
            traduction_releve_notes=['traduction_releve_notes.pdf'],
            releve_notes=['releve.pdf'],
            type_releve_notes=TranscriptType.ONE_FOR_ALL_YEARS.name,
            a_obtenu_diplome=False,
            diplome=['diplome.pdf'],
            traduction_diplome=['traduction_diplome.pdf'],
            regime_linguistique='',
            note_memoire='',
            rang_diplome='',
            resume_memoire=[],
            titre_memoire='',
            date_prevue_delivrance_diplome=None,
            uuid='9cbdf4db-2454-4cbf-9e48-55d2a9881ee6',
            nom_formation='Formation AA',
            grade_obtenu=Grade.GREAT_DISTINCTION.name,
            systeme_evaluation=EvaluationSystem.ECTS_CREDITS.name,
            adresse_institut='',
            code_institut='',
            communaute_institut='',
            nom_institut='',
            nom_pays='',
            nom_regime_linguistique='',
            type_enseignement='',
            type_institut='',
            nom_formation_equivalente_communaute_fr='',
            cycle_formation='',
            grade_academique_formation='1',
        )

        cls.params_defaut_experience_non_academique = {
            'uuid': str(uuid.uuid4()),
            'employeur': 'UCL',
            'type': ActivityType.WORK.name,
            'certificat': [],
            'fonction': 'Bibliothécaire',
            'secteur': ActivitySector.PUBLIC.name,
            'autre_activite': '',
            'personne': '0000000001',
        }

        cls.experiences_parcours_internes = [
            ExperienceParcoursInterneDTOFactory(
                annees=[
                    AnneeExperienceParcoursInterneDTOFactory(
                        etat_inscription=EtatInscriptionFormation.ERREUR.name,
                        annee=2011,
                    ),
                    AnneeExperienceParcoursInterneDTOFactory(
                        etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
                        annee=2012,
                    ),
                    AnneeExperienceParcoursInterneDTOFactory(
                        etat_inscription=EtatInscriptionFormation.ANNULATION_UCL.name,
                        annee=2013,
                    ),
                ]
            ),
            ExperienceParcoursInterneDTOFactory(
                annees=[
                    AnneeExperienceParcoursInterneDTOFactory(
                        etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
                        annee=2014,
                    ),
                ]
            ),
        ]

    def assertAnneesCurriculum(self, exceptions, messages):
        messages_renvoyes = []
        for exception in exceptions:
            self.assertIsInstance(
                exception, (AnneesCurriculumNonSpecifieesException, ExperiencesAcademiquesNonCompleteesException)
            )
            messages_renvoyes.append(exception.message)

        self.assertCountEqual(messages, messages_renvoyes)

    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

        self.academic_year_repository = AcademicYearInMemoryRepository()
        self.proposition_in_memory = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_in_memory.reset)

        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.experiences_academiques = self.candidat_translator.experiences_academiques

        self.candidat = self.candidat_translator.profil_candidats[1]
        self.experiences_non_academiques = self.candidat_translator.experiences_non_academiques

        self.adresse_residentielle = next(
            adresse
            for adresse in self.candidat_translator.adresses_candidats
            if adresse.personne == self.candidat.matricule
        )

        self.master_proposition = self.proposition_in_memory.get(
            entity_id=PropositionIdentityBuilder.build_from_uuid(uuid='uuid-MASTER-SCI'),
        )
        self.master_proposition.soumise_le = datetime.datetime(2014, 11, 1)
        self.master_proposition.formation_id = FormationIdentityFactory(annee=2015, sigle='MASTER-SCI')

        self.etudes_secondaires = self.candidat_translator.etudes_secondaires
        self.etudes_secondaires[self.master_proposition.matricule_candidat] = EtudesSecondairesAdmissionDTO(
            annee_diplome_etudes_secondaires=2005,
        )

        for annee in range(2005, 2023):
            self.academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 14),
                )
            )
        # Mock datetime to return the 2020 year as the current year
        patcher = freezegun.freeze_time('2020-11-01')
        patcher.start()
        self.addCleanup(patcher.stop)
        self.cmd = VerifierCurriculumApresSoumissionQuery(uuid_proposition=self.master_proposition.entity_id.uuid)

    def tearDown(self):
        mock.patch.stopall()

    def test_should_retourner_erreur_si_5_dernieres_annees_curriculum_non_saisies(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2010 à Février 2011',
                'De Septembre 2011 à Février 2012',
                'De Septembre 2012 à Février 2013',
                'De Septembre 2013 à Février 2014',
                'De Septembre 2014 à Octobre 2014',
            ],
        )

    def test_should_retourner_erreur_en_fonction_annee_diplomation_secondaires(self):
        self.etudes_secondaires[self.master_proposition.matricule_candidat] = EtudesSecondairesAdmissionDTO(
            annee_diplome_etudes_secondaires=2012,
        )

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2013 à Février 2014',
                'De Septembre 2014 à Octobre 2014',
            ],
        )

    def test_should_retourner_erreur_en_fonction_annee_formation(self):
        self.master_proposition.formation_id = FormationIdentityFactory(annee=2012, sigle='MASTER-SCI')

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2007 à Février 2008',
                'De Septembre 2008 à Février 2009',
                'De Septembre 2009 à Février 2010',
                'De Septembre 2010 à Février 2011',
                'De Septembre 2011 à Février 2012',
            ],
        )

    def test_should_retourner_erreur_en_fonction_date_soumission_demande(self):
        # Date de soumission après la fin de la période à vérifier
        self.master_proposition.soumise_le = datetime.datetime(2015, 3, 15)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2010 à Février 2011',
                'De Septembre 2011 à Février 2012',
                'De Septembre 2012 à Février 2013',
                'De Septembre 2013 à Février 2014',
                'De Septembre 2014 à Février 2015',
            ],
        )

        # Date de soumission avant la fin de la période à vérifier
        self.master_proposition.soumise_le = datetime.datetime(2015, 2, 15)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2010 à Février 2011',
                'De Septembre 2011 à Février 2012',
                'De Septembre 2012 à Février 2013',
                'De Septembre 2013 à Février 2014',
                'De Septembre 2014 à Janvier 2015',
            ],
        )

        # Date de soumission au mois d'octobre -> le dernier mois de septembre n'est pas à valoriser
        self.master_proposition.soumise_le = datetime.datetime(2014, 10, 31)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2010 à Février 2011',
                'De Septembre 2011 à Février 2012',
                'De Septembre 2012 à Février 2013',
                'De Septembre 2013 à Février 2014',
            ],
        )

        self.master_proposition.soumise_le = datetime.datetime(2014, 11, 1)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2010 à Février 2011',
                'De Septembre 2011 à Février 2012',
                'De Septembre 2012 à Février 2013',
                'De Septembre 2013 à Février 2014',
                'De Septembre 2014 à Octobre 2014',
            ],
        )

    def test_should_pas_retourner_erreur_en_fonction_derniere_annee_declaree_inscription_ucl(self):
        with mock.patch.multiple(
            self.candidat,
            annee_derniere_inscription_ucl=2012,
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)

            self.assertAnneesCurriculum(
                context.exception.exceptions,
                [
                    'De Septembre 2010 à Février 2011',
                    'De Septembre 2011 à Février 2012',
                    'De Septembre 2012 à Février 2013',
                    'De Septembre 2013 à Février 2014',
                    'De Septembre 2014 à Octobre 2014',
                ],
            )

    @freezegun.freeze_time('2016-09-15')
    def test_should_pas_retourner_erreur_en_fonction_date_courante(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2010 à Février 2011',
                'De Septembre 2011 à Février 2012',
                'De Septembre 2012 à Février 2013',
                'De Septembre 2013 à Février 2014',
                'De Septembre 2014 à Octobre 2014',
            ],
        )

    def test_should_retourner_erreur_en_fonction_experiences_academiques_candidat(self):
        self.experiences_academiques.append(self.experience_academiques_complete)

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2010 à Février 2011',
                'De Septembre 2012 à Février 2013',
            ],
        )

    def test_should_pas_retourner_erreur_periode_en_fonction_experiences_academiques_incompletes_candidat(self):
        self.experiences_academiques.append(self.experience_academiques_complete)

        with mock.patch.multiple(
            self.experience_academiques_complete,
            a_obtenu_diplome=False,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.SECOND_CYCLE.name,
            avec_complements=True,
            credits_inscrits_complements=None,
            credits_acquis_complements=10,
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)

            self.assertAnneesCurriculum(
                context.exception.exceptions,
                [
                    'L\'expérience académique \'Formation AA\' est incomplète.',
                    'De Septembre 2010 à Février 2011',
                    'De Septembre 2012 à Février 2013',
                ],
            )

        with mock.patch.multiple(
            self.experience_academiques_complete,
            a_obtenu_diplome=False,
            communaute_institut=CommunityEnum.FRENCH_SPEAKING.name,
            cycle_formation=Cycle.SECOND_CYCLE.name,
            avec_complements=True,
            credits_inscrits_complements=None,
            credits_acquis_complements=10,
            grade_academique_formation='2',
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)

            self.assertAnneesCurriculum(
                context.exception.exceptions,
                [
                    'De Septembre 2010 à Février 2011',
                    'De Septembre 2012 à Février 2013',
                ],
            )

    def test_should_retourner_erreur_en_fonction_activites_non_academiques_candidat(self):
        self.experiences_non_academiques.append(
            ExperienceNonAcademique(
                **self.params_defaut_experience_non_academique,
                date_debut=datetime.date(2013, 10, 1),
                date_fin=datetime.date(2014, 1, 31),
            )
        )
        self.experiences_non_academiques.append(
            ExperienceNonAcademique(
                **self.params_defaut_experience_non_academique,
                date_debut=datetime.date(2010, 9, 1),
                date_fin=datetime.date(2012, 8, 31),
            )
        )

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'De Septembre 2012 à Février 2013',
                'Septembre 2013',
                'Février 2014',
                'De Septembre 2014 à Octobre 2014',
            ],
        )

        # Expériences se chevauchant
        self.experiences_non_academiques[-1] = ExperienceNonAcademique(
            **self.params_defaut_experience_non_academique,
            date_debut=datetime.date(2010, 9, 1),
            date_fin=datetime.date(2013, 12, 31),
        )

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd)

        self.assertAnneesCurriculum(
            context.exception.exceptions,
            [
                'Février 2014',
                'De Septembre 2014 à Octobre 2014',
            ],
        )

    def test_should_retourner_erreur_en_fonction_experiences_academiques_internes_candidat(self):
        with mock.patch.object(
            ExperienceParcoursInterneInMemoryTranslator,
            'recuperer',
            return_value=self.experiences_parcours_internes,
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)

            self.assertAnneesCurriculum(
                context.exception.exceptions,
                [
                    'De Septembre 2010 à Février 2011',
                    'De Septembre 2011 à Février 2012',
                    'De Septembre 2013 à Février 2014',
                ],
            )

    def test_should_retourner_erreur_en_fonction_experiences_academiques_et_activites_non_academiques_candidat(self):
        self.experiences_academiques.append(self.experience_academiques_complete)

        self.experiences_non_academiques.append(
            ExperienceNonAcademique(
                **self.params_defaut_experience_non_academique,
                date_debut=datetime.date(2011, 2, 1),
                date_fin=datetime.date(2012, 11, 30),
            )
        )

        with mock.patch.object(
            ExperienceParcoursInterneInMemoryTranslator,
            'recuperer',
            return_value=self.experiences_parcours_internes,
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(self.cmd)

            self.assertAnneesCurriculum(
                context.exception.exceptions,
                [
                    'De Septembre 2010 à Janvier 2011',
                ],
            )
