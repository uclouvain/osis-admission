# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from admission.ddd.admission.doctorat.preparation import commands as doctorate_education_commands
from admission.ddd.admission.doctorat.preparation.dtos import ComptabiliteDTO as DoctorateAccountingDTO
from admission.ddd.admission.formation_generale import commands as general_education_commands
from admission.ddd.admission.formation_generale.dtos import ComptabiliteDTO as GeneralAccountingDTO
from admission.infrastructure.admission.domain.service.profil_candidat import (
    ProfilCandidatTranslator,
)
from admission.utils import takewhile_return_attribute_values
from base.models.academic_year import AcademicYear
from base.models.enums.community import CommunityEnum
from base.models.person import Person
from base.tasks.synchronize_entities_addresses import UCLouvain_acronym
from base.utils.serializers import DTOSerializer
from osis_profile.models import EducationalExperienceYear


def get_last_french_community_high_education_institutes(candidate: Person, date: datetime.datetime):
    # Absence of debts conditions -> check, on the basis of the CV, the absence of debt to the last high
    # education establishment of the French community attended by the candidate, when it is not UCLouvain, and
    # only within the scope of the academic years that must be justified
    cv_minimal_years = ProfilCandidatTranslator.get_annees_minimum_curriculum(
        global_id=candidate.global_id,
        current_year=AcademicYear.objects.current(date).year,
    )
    last_institutes = (
        EducationalExperienceYear.objects.filter(
            educational_experience__person=candidate,
            educational_experience__institute__community=CommunityEnum.FRENCH_SPEAKING.name,
            academic_year__year__gte=cv_minimal_years.get('minimal_date').year,
        )
        .exclude(
            educational_experience__institute__acronym=UCLouvain_acronym,
        )
        .values('academic_year__year', 'educational_experience__institute__name')
    )

    if last_institutes:
        year = last_institutes[0].get('academic_year__year')

        names = takewhile_return_attribute_values(
            lambda institute: institute.get('academic_year__year') == year,
            last_institutes,
            'educational_experience__institute__name',
        )

        return {
            'academic_year': year,
            'names': list(names),
        }


class DoctorateEducationAccountingDTOSerializer(DTOSerializer):
    derniers_etablissements_superieurs_communaute_fr_frequentes = SerializerMethodField(
        allow_null=True,
    )
    a_nationalite_ue = serializers.SerializerMethodField(allow_null=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Define custom schemas as the default schema type of a SerializerMethodField is string
        self.fields['derniers_etablissements_superieurs_communaute_fr_frequentes'].field_schema = {
            'type': 'object',
            'properties': {
                'academic_year': {'type': 'integer'},
                'names': {'type': 'array', 'items': {'type': 'string'}},
            },
        }
        self.fields['a_nationalite_ue'].field_schema = {
            'type': 'boolean',
        }

    def get_derniers_etablissements_superieurs_communaute_fr_frequentes(self, _):
        # Absence of debts conditions -> check, on the basis of the CV, the absence of debt to the last high
        # education establishment of the French community attended by the candidate, when it is not UCLouvain, and
        # only within the scope of the academic years that must be justified
        return get_last_french_community_high_education_institutes(self.context['candidate'], datetime.datetime.now())

    def get_a_nationalite_ue(self, _):
        country = getattr(self.context['candidate'], 'country_of_citizenship')
        return country.european_union if country else None

    class Meta:
        source = DoctorateAccountingDTO
        extra_kwargs = {
            'numero_compte_autre_format': {'max_length': 255},
            'numero_compte_iban': {'max_length': 34},
            'prenom_titulaire_compte': {'max_length': 128},
            'nom_titulaire_compte': {'max_length': 128},
        }


class GeneralEducationAccountingDTOSerializer(DoctorateEducationAccountingDTOSerializer):
    class Meta:
        source = GeneralAccountingDTO
        extra_kwargs = {
            'numero_compte_autre_format': {'max_length': 255},
            'numero_compte_iban': {'max_length': 34},
            'prenom_titulaire_compte': {'max_length': 128},
            'nom_titulaire_compte': {'max_length': 128},
        }


class CompleterComptabilitePropositionDoctoraleCommandSerializer(DTOSerializer):
    auteur_modification = None

    class Meta:
        source = doctorate_education_commands.CompleterComptabilitePropositionCommand
        extra_kwargs = {
            'numero_compte_autre_format': {'max_length': 255},
            'numero_compte_iban': {'max_length': 34},
            'prenom_titulaire_compte': {'max_length': 128},
            'nom_titulaire_compte': {'max_length': 128},
        }


class CompleterComptabilitePropositionGeneraleCommandSerializer(DTOSerializer):
    auteur_modification = None

    class Meta:
        source = general_education_commands.CompleterComptabilitePropositionCommand
        extra_kwargs = {
            'numero_compte_autre_format': {'max_length': 255},
            'numero_compte_iban': {'max_length': 34},
            'prenom_titulaire_compte': {'max_length': 128},
            'nom_titulaire_compte': {'max_length': 128},
        }
