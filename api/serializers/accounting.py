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
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from admission.ddd.projet_doctoral.preparation.commands import CompleterComptabilitePropositionCommand
from admission.infrastructure.projet_doctoral.preparation.domain.service.profil_candidat import ProfilCandidatTranslator
from admission.utils import takewhile_return_attribute_values
from base.models.academic_year import current_academic_year
from base.models.enums.community import CommunityEnum
from base.models.person import Person
from base.tasks.synchronize_entities_addresses import UCLouvain_acronym
from base.utils.serializers import DTOSerializer
from osis_profile.models import EducationalExperienceYear


class CompleterComptabilitePropositionCommandSerializer(DTOSerializer):
    class Meta:
        source = CompleterComptabilitePropositionCommand


class AccountingConditionsSerializer(serializers.ModelSerializer):
    has_ue_nationality = serializers.BooleanField(
        source='country_of_citizenship.european_union',
        allow_null=True,
        read_only=True,
    )
    last_french_community_high_education_institutes_attended = SerializerMethodField(
        allow_null=True,
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Define a custom schema as the default schema type of a SerializerMethodField is string
        self.fields['last_french_community_high_education_institutes_attended'].field_schema = {
            'type': 'object',
            'properties': {
                'academic_year': {'type': 'integer'},
                'names': {'type': 'array', 'items': {'type': 'string'}},
            },
        }

    def get_last_french_community_high_education_institutes_attended(self, instance: Person):
        # Absence of debts conditions -> check, on the basis of the CV, the absence of debt to the last high
        # education establishment of the French community attended by the candidate, when it is not UCLouvain, and
        # only within the scope of the academic years that must be justified
        cv_minimal_years = ProfilCandidatTranslator.get_annees_minimum_curriculum(
            global_id=instance.global_id,
            current_year=current_academic_year().year,
        )
        last_institutes = (
            EducationalExperienceYear.objects.filter(
                educational_experience__person=instance,
                educational_experience__institute__community=CommunityEnum.FRENCH_SPEAKING.name,
                academic_year__year__gte=cv_minimal_years.get('minimal_year'),
            )
            .exclude(
                educational_experience__institute__code=UCLouvain_acronym,
            )
            .values('academic_year__year', 'educational_experience__institute__name')
        )

        if last_institutes:
            year = last_institutes[0].get('academic_year__year')

            names = takewhile_return_attribute_values(
                lambda institute: institute.get('academic_year__year') == year,
                last_institutes,
                'educational_experience__institute__name'
            )

            return {
                'academic_year': year,
                'names': names,
            }

    class Meta:
        model = Person
        fields = [
            'has_ue_nationality',
            'last_french_community_high_education_institutes_attended',
        ]
