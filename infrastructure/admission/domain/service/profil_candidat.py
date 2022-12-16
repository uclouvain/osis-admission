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
import datetime
from typing import Dict, List

from django.db.models import Exists, OuterRef, Subquery

from admission.ddd.admission.doctorat.preparation.dtos import ConditionsComptabiliteDTO, CurriculumDTO
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import (
    AnneeExperienceAcademiqueDTO,
    ExperienceAcademiqueDTO,
)
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.validator._should_identification_candidat_etre_completee import BE_ISO_CODE
from admission.ddd.admission.dtos import AdressePersonnelleDTO, CoordonneesDTO, EtudesSecondairesDTO, IdentificationDTO
from base.models.enums.community import CommunityEnum
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
from base.models.person_address import PersonAddress
from base.tasks.synchronize_entities_addresses import UCLouvain_acronym
from osis_profile.models import (
    BelgianHighSchoolDiploma,
    EducationalExperienceYear,
    ForeignHighSchoolDiploma,
    ProfessionalExperience,
)
from osis_profile.models.education import HighSchoolDiplomaAlternative, LanguageKnowledge


class ProfilCandidatTranslator(IProfilCandidatTranslator):
    @classmethod
    def get_identification(cls, matricule: str) -> 'IdentificationDTO':
        person = (
            Person.objects.select_related('country_of_citizenship', 'birth_country')
            .annotate(
                residential_country_iso_code=Subquery(
                    PersonAddress.objects.filter(
                        label=PersonAddressType.RESIDENTIAL.name,
                        person_id=OuterRef('pk'),
                    ).values('country__iso_code')[:1]
                )
            )
            .get(global_id=matricule)
        )

        return IdentificationDTO(
            matricule=matricule,
            nom=person.last_name,
            prenom=person.first_name,
            date_naissance=person.birth_date,
            annee_naissance=person.birth_year,
            pays_nationalite=person.country_of_citizenship.iso_code if person.country_of_citizenship_id else None,
            langue_contact=person.language,
            sexe=person.sex,
            genre=person.gender,
            photo_identite=person.id_photo,
            carte_identite=person.id_card,
            passeport=person.passport,
            numero_registre_national_belge=person.national_number,
            numero_carte_identite=person.id_card_number,
            numero_passeport=person.passport_number,
            email=person.email,
            pays_naissance=person.birth_country.iso_code if person.birth_country_id else None,
            lieu_naissance=person.birth_place,
            etat_civil=person.civil_state,
            annee_derniere_inscription_ucl=person.last_registration_year,
            noma_derniere_inscription_ucl=person.last_registration_id,
            pays_residence=person.residential_country_iso_code,
        )

    @classmethod
    def get_coordonnees(cls, matricule: str) -> 'CoordonneesDTO':
        adresses = {
            a.label: a
            for a in PersonAddress.objects.select_related('country').filter(
                person__global_id=matricule,
                label__in=[PersonAddressType.CONTACT.name, PersonAddressType.RESIDENTIAL.name],
            )
        }
        domicile_legal = adresses.get(PersonAddressType.RESIDENTIAL.name)
        adresse_correspondance = adresses.get(PersonAddressType.CONTACT.name)

        return CoordonneesDTO(
            domicile_legal=AdressePersonnelleDTO(
                rue=domicile_legal.street,
                code_postal=domicile_legal.postal_code,
                ville=domicile_legal.city,
                pays=domicile_legal.country.iso_code if domicile_legal.country else None,
                boite_postale=domicile_legal.postal_box,
                numero_rue=domicile_legal.street_number,
                lieu_dit=domicile_legal.place,
            )
            if domicile_legal
            else None,
            adresse_correspondance=AdressePersonnelleDTO(
                rue=adresse_correspondance.street,
                code_postal=adresse_correspondance.postal_code,
                ville=adresse_correspondance.city,
                pays=adresse_correspondance.country.iso_code if adresse_correspondance.country else None,
                boite_postale=adresse_correspondance.postal_box,
                numero_rue=adresse_correspondance.street_number,
                lieu_dit=adresse_correspondance.place,
            )
            if adresse_correspondance
            else None,
        )

    @classmethod
    def get_langues_connues(cls, matricule: str) -> List[str]:
        return (
            LanguageKnowledge.objects.select_related('language')
            .filter(
                person__global_id=matricule,
            )
            .values_list('language__code', flat=True)
        )

    @classmethod
    def get_etudes_secondaires(cls, matricule: str) -> 'EtudesSecondairesDTO':
        result = (
            Person.objects.annotate(
                presence_etudes_secondaires_belges=Exists(
                    BelgianHighSchoolDiploma.objects.filter(person_id=OuterRef('pk'))
                ),
                presence_etudes_secondaires_etrangeres=Exists(
                    ForeignHighSchoolDiploma.objects.filter(person_id=OuterRef('pk'))
                ),
                presence_examen_admission_premier_cycle=Exists(
                    HighSchoolDiplomaAlternative.objects.filter(person_id=OuterRef('pk'))
                ),
            )
            .values(
                'presence_etudes_secondaires_belges',
                'presence_etudes_secondaires_etrangeres',
                'presence_examen_admission_premier_cycle',
            )
            .get(global_id=matricule)
        )
        return EtudesSecondairesDTO(**result)

    @classmethod
    def get_curriculum(cls, matricule: str, annee_courante: int) -> 'CurriculumDTO':
        minimal_years = cls.get_annees_minimum_curriculum(matricule, annee_courante)
        date_maximale = cls.get_date_maximale_curriculum()

        annees_experiences_academiques = EducationalExperienceYear.objects.filter(
            educational_experience__person__global_id=matricule,
        ).select_related('educational_experience__country', 'academic_year')

        experiences_academiques_dtos: Dict[int, ExperienceAcademiqueDTO] = {}

        for annee_experience in annees_experiences_academiques:
            annee_experience_dto = AnneeExperienceAcademiqueDTO(
                resultat=annee_experience.result,
                annee=annee_experience.academic_year.year,
            )
            if annee_experience.educational_experience.pk not in experiences_academiques_dtos:
                experiences_academiques_dtos[annee_experience.educational_experience.pk] = ExperienceAcademiqueDTO(
                    pays=annee_experience.educational_experience.country.iso_code,
                    annees=[annee_experience_dto],
                )
            else:
                experiences_academiques_dtos[annee_experience.educational_experience.pk].annees.append(
                    annee_experience_dto
                )

        dates_experiences_non_academiques = ProfessionalExperience.objects.filter(
            person__global_id=matricule,
            start_date__lte=date_maximale,
            end_date__gte=minimal_years.get('minimal_date'),
        ).values_list('start_date', 'end_date')

        return CurriculumDTO(
            experiences_academiques=list(experiences_academiques_dtos.values()),
            annee_diplome_etudes_secondaires_belges=minimal_years.get('belgian_highschool_diploma_year'),
            annee_diplome_etudes_secondaires_etrangeres=minimal_years.get('foreign_highschool_diploma_year'),
            annee_derniere_inscription_ucl=minimal_years.get('last_registration_year'),
            dates_experiences_non_academiques=list(dates_experiences_non_academiques),
        )

    @classmethod
    def get_annees_minimum_curriculum(cls, global_id, current_year):
        person = (
            Person.objects.select_related(
                'last_registration_year',
                'belgianhighschooldiploma__academic_graduation_year',
                'foreignhighschooldiploma__academic_graduation_year',
            )
            .only(
                'belgianhighschooldiploma__academic_graduation_year__year',
                'foreignhighschooldiploma__academic_graduation_year__year',
                'last_registration_year__year',
            )
            .get(global_id=global_id)
        )

        belgian_highschool_diploma_year = (
            person.belgianhighschooldiploma.academic_graduation_year.year
            if hasattr(person, 'belgianhighschooldiploma')
            else None
        )
        foreign_highschool_diploma_year = (
            person.foreignhighschooldiploma.academic_graduation_year.year
            if hasattr(person, 'foreignhighschooldiploma')
            else None
        )

        last_registration_year = person.last_registration_year.year if person.last_registration_year else None

        minimal_year = cls.get_annee_minimale_a_completer_cv(
            annee_courante=current_year,
            annee_derniere_inscription_ucl=last_registration_year,
            annee_diplome_etudes_secondaires_belges=belgian_highschool_diploma_year,
            annee_diplome_etudes_secondaires_etrangeres=foreign_highschool_diploma_year,
        )

        return {
            'minimal_date': datetime.date(minimal_year, IProfilCandidatTranslator.MOIS_DEBUT_ANNEE_ACADEMIQUE, 1),
            'last_registration_year': last_registration_year,
            'belgian_highschool_diploma_year': belgian_highschool_diploma_year,
            'foreign_highschool_diploma_year': foreign_highschool_diploma_year,
        }

    @classmethod
    def get_conditions_comptabilite(
        cls,
        matricule: str,
        annee_courante: int,
    ) -> 'ConditionsComptabiliteDTO':
        minimal_years = cls.get_annees_minimum_curriculum(
            global_id=matricule,
            current_year=annee_courante,
        )

        person = Person.objects.only('pk', 'country_of_citizenship').get(global_id=matricule)

        is_ue_country = (
            person.country_of_citizenship.european_union if getattr(person, 'country_of_citizenship') else None
        )

        has_attented_french_community_institute = (
            EducationalExperienceYear.objects.filter(
                educational_experience__person=person,
                educational_experience__institute__community=CommunityEnum.FRENCH_SPEAKING.name,
                academic_year__year__gte=minimal_years.get('minimal_date').year,
            )
            .exclude(
                educational_experience__institute__code=UCLouvain_acronym,
            )
            .exists()
        )

        return ConditionsComptabiliteDTO(
            pays_nationalite_ue=is_ue_country,
            a_frequente_recemment_etablissement_communaute_fr=has_attented_french_community_institute,
        )

    @classmethod
    def get_changements_etablissement(cls, matricule: str, annees: List[int]) -> Dict[int, bool]:
        """Inscrit à un autre établissement Belge en N-1
        (informatiquement : curriculum / en N-1 supérieur belge non-diplômé)"""
        qs = dict(
            EducationalExperienceYear.objects.filter(academic_year__year__in=[annee - 1 for annee in annees])
            .annotate(
                est_changement=Exists(
                    EducationalExperienceYear.objects.filter(
                        educational_experience__person__global_id=matricule,
                        educational_experience__country__iso_code=BE_ISO_CODE,
                        educational_experience__obtained_diploma=False,
                        academic_year__year=OuterRef('academic_year__year'),
                    )
                ),
            )
            .distinct('academic_year__year')
            .values_list('academic_year__year', 'est_changement')
        )
        return {annee: qs.get(annee - 1) for annee in annees}
