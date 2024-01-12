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

import factory

from admission.contrib.models import GeneralEducationAdmission
from admission.contrib.models.general_education import AdmissionPrerequisiteCourses
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    ChoixStatutChecklist,
)
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from admission.tests.factories.accounting import AccountingFactory
from admission.tests.factories.person import CompletePersonForBachelorFactory
from admission.tests.factories.roles import CandidateFactory
from admission.tests.factories.scholarship import (
    DoubleDegreeScholarshipFactory,
    ErasmusMundusScholarshipFactory,
    InternationalScholarshipFactory,
)
from admission.tests.factories.utils import generate_proposition_reference
from base.models.enums import education_group_categories
from base.models.enums.education_group_types import TrainingType
from base.models.enums.organization_type import MAIN
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFullFactory
from base.tests.factories.person import PersonFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory


class GeneralEducationTrainingFactory(EducationGroupYearFactory):
    academic_year = factory.SubFactory(AcademicYearFactory, current=True)
    education_group_type = factory.SubFactory(
        'base.tests.factories.education_group_type.EducationGroupTypeFactory',
        category=education_group_categories.TRAINING,
        name=factory.fuzzy.FuzzyChoice(AnneeInscriptionFormationTranslator.GENERAL_EDUCATION_TYPES),
    )
    main_domain = factory.SubFactory('reference.tests.factories.domain.DomainFactory')

    @factory.post_generation
    def create_related_group_version_factory(self, create, extracted, **kwargs):
        EducationGroupVersionFactory(
            offer=self,
            version_name='',
            root_group__academic_year__year=self.academic_year.year,
            root_group__main_teaching_campus__name='Louvain-la-Neuve',
        )


def get_checklist():
    default_content = {
        'libelle': '',
        'enfants': [],
        'extra': {},
        'statut': ChoixStatutChecklist.INITIAL_CANDIDAT.name,
    }
    return {
        'donnees_personnelles': default_content,
        'frais_dossier': default_content,
        'assimilation': default_content,
        'choix_formation': default_content,
        'parcours_anterieur': default_content,
        'financabilite': default_content,
        'specificites_formation': default_content,
        'decision_facultaire': default_content,
        'decision_sic': default_content,
    }


class GeneralEducationAdmissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GeneralEducationAdmission

    candidate = factory.SubFactory(PersonFactory)
    reference = factory.LazyAttribute(generate_proposition_reference)
    training = factory.SubFactory(
        GeneralEducationTrainingFactory,
        academic_year__current=True,
        enrollment_campus__name='Mons',
        enrollment_campus__organization__type=MAIN,
    )
    erasmus_mundus_scholarship = factory.SubFactory(ErasmusMundusScholarshipFactory)
    double_degree_scholarship = factory.SubFactory(DoubleDegreeScholarshipFactory)
    international_scholarship = factory.SubFactory(InternationalScholarshipFactory)
    last_update_author = factory.SubFactory(PersonFactory)
    determined_academic_year = factory.SubFactory(AcademicYearFactory, current=True)
    checklist = factory.Dict({'default': True})  # This default value is overriden in a post generation method

    @factory.post_generation
    def create_candidate_role(self, create, extracted, **kwargs):
        CandidateFactory(person=self.candidate)

    class Params:
        bachelor_with_access_conditions_met = factory.Trait(
            training__education_group_type__name=TrainingType.BACHELOR.name,
            candidate=factory.SubFactory(CompletePersonForBachelorFactory),
            is_external_reorientation=False,
            is_external_modification=False,
        )
        admitted = factory.Trait(
            status=ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
            submitted_profile={
                "coordinates": {
                    "city": "Louvain-La-Neuve",
                    "place": "",
                    "street": "Place de l'Université",
                    "country": "BE",
                    "postal_box": "",
                    "postal_code": "1348",
                    "street_number": "2",
                },
                "identification": {
                    "gender": "H",
                    "last_name": "Doe",
                    "first_name": "John",
                    "country_of_citizenship": "BE",
                    "date_of_birth": "2020-01-01",
                },
            },
        )

    @factory.post_generation
    def create_accounting(self, create, extracted, **kwargs):
        AccountingFactory(admission_id=self.pk)

    @factory.post_generation
    def initialize_checklist(self, create, extracted, **kwargs):
        if self.checklist != {'default': True}:
            return

        self.checklist = (
            {}
            if self.status
            in {
                ChoixStatutPropositionGenerale.EN_BROUILLON.name,
                ChoixStatutPropositionGenerale.ANNULEE.name,
            }
            else {
                'initial': get_checklist(),
                'current': get_checklist(),
            }
        )


class AdmissionPrerequisiteCoursesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AdmissionPrerequisiteCourses

    admission = factory.SubFactory(GeneralEducationAdmissionFactory)
    course = factory.SubFactory(LearningUnitYearFullFactory)
