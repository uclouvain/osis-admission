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
from typing import Optional, List, Dict

from django.db import models
from django.db.models import Exists, OuterRef, Prefetch, Case, When
from django.db.models.functions import ExtractYear, ExtractMonth

from admission.ddd import NB_MOIS_MIN_VAE, LANGUES_OBLIGATOIRES_DOCTORAT
from admission.ddd.admission.doctorat.preparation.dtos import ConditionsComptabiliteDTO
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import CurriculumAdmissionDTO
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.dtos.resume import ResumeCandidatDTO
from admission.ddd.admission.enums.valorisation_experience import ExperiencesCVRecuperees
from admission.infrastructure.admission.domain.service.annee_inscription_formation import \
    AnneeInscriptionFormationTranslator
from admission.services.injection_epc import EPCInjection as AdmissionEPCInjection
from base.models.enums.community import CommunityEnum
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
from base.models.person_address import PersonAddress
from base.tasks.synchronize_entities_addresses import UCLouvain_acronym
from ddd.logic.shared_kernel.profil.dtos.etudes_secondaires import ValorisationEtudesSecondairesDTO
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import CurriculumAExperiencesDTO
from osis_profile import BE_ISO_CODE
from osis_profile.models import EducationalExperience, ProfessionalExperience, EducationalExperienceYear
from osis_profile.models.education import LanguageKnowledge
from osis_profile.models.epc_injection import ExperienceType
from osis_profile.services.injection_epc import EPCInjection as CurriculumEPCInjection


class ProfilCandidatTranslator(IProfilCandidatTranslator):
    @classmethod
    def get_curriculum(
        cls,
        matricule: str,
        annee_courante: int,
        uuid_proposition: str,
        experiences_cv_recuperees: ExperiencesCVRecuperees = ExperiencesCVRecuperees.TOUTES,
    ) -> Optional['CurriculumAdmissionDTO']:

        try:
            minimal_years = cls.get_annees_minimum_curriculum(matricule, annee_courante)

            academic_experiences_dtos = cls._get_academic_experiences_dtos(
                matricule,
                cls.has_default_language(),
                uuid_proposition,
                experiences_cv_recuperees=experiences_cv_recuperees,
            )

            non_academic_experiences_dtos = cls.get_experiences_non_academiques(
                matricule=matricule,
                uuid_proposition=uuid_proposition,
                experiences_cv_recuperees=experiences_cv_recuperees,
            )

            return CurriculumAdmissionDTO(
                experiences_academiques=academic_experiences_dtos,
                annee_diplome_etudes_secondaires=minimal_years.get('highschool_diploma_year'),
                annee_derniere_inscription_ucl=minimal_years.get('last_registration_year'),
                experiences_non_academiques=non_academic_experiences_dtos,
                annee_minimum_a_remplir=minimal_years.get('minimal_date').year,
            )
        except Person.DoesNotExist:
            return None

    @classmethod
    def get_existence_experiences_curriculum(cls, matricule: str) -> 'CurriculumAExperiencesDTO':
        experiences_curriculum = (
            Person.objects.annotate(
                a_experience_academique=Exists(EducationalExperience.objects.filter(person_id=OuterRef('pk'))),
                a_experience_non_academique=Exists(ProfessionalExperience.objects.filter(person_id=OuterRef('pk'))),
            )
            .values(
                'a_experience_academique',
                'a_experience_non_academique',
            )
            .get(global_id=matricule)
        )

        return CurriculumAExperiencesDTO(
            a_experience_academique=experiences_curriculum.get('a_experience_academique'),
            a_experience_non_academique=experiences_curriculum.get('a_experience_non_academique'),
        )

    @classmethod
    def get_annees_minimum_curriculum(cls, global_id, current_year):
        person = (
            Person.objects.select_related(
                'graduated_from_high_school_year',
                'last_registration_year',
            )
            .only(
                'graduated_from_high_school_year__year',
                'last_registration_year__year',
            )
            .get(global_id=global_id)
        )

        last_registration_year = person.last_registration_year.year if person.last_registration_year else None
        graduated_from_high_school_year = (
            person.graduated_from_high_school_year.year if person.graduated_from_high_school_year else None
        )

        minimal_year = cls.get_annee_minimale_a_completer_cv(
            annee_courante=current_year,
            annee_derniere_inscription_ucl=last_registration_year,
            annee_diplome_etudes_secondaires=graduated_from_high_school_year,
        )

        return {
            'minimal_date': datetime.date(
                minimal_year,
                cls.MOIS_DEBUT_ANNEE_ACADEMIQUE_A_VALORISER,
                1,
            ),
            'last_registration_year': last_registration_year,
            'highschool_diploma_year': graduated_from_high_school_year,
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

        person = (
            Person.objects.only('pk', 'country_of_citizenship')
            .select_related('country_of_citizenship')
            .get(global_id=matricule)
        )

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
                educational_experience__institute__acronym=UCLouvain_acronym,
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

    @classmethod
    def valorisation_etudes_secondaires(cls, matricule: str) -> ValorisationEtudesSecondairesDTO:
        valuation = (
            Person.objects.filter(global_id=matricule)
            .annotate(**cls.get_secondary_studies_valuation_annotations())
            .values('is_valuated_by_epc', 'valuated_training_types')
            .first()
        )

        return (
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=valuation['is_valuated_by_epc'],
                types_formations_admissions_valorisees=valuation['valuated_training_types'],
            )
            if valuation
            else ValorisationEtudesSecondairesDTO()
        )

    @classmethod
    def est_potentiel_vae(cls, matricule: str) -> bool:
        nombre_mois = (
            ProfessionalExperience.objects.filter(person__global_id=matricule)
            .annotate(
                nombre_mois=(ExtractYear('end_date') - ExtractYear('start_date')) * 12
                + (ExtractMonth('end_date') - ExtractMonth('start_date'))
                + 1
                # + 1 car la date de début est le premier jour du mois et la date de fin, le dernier jour du mois
            )
            .aggregate(total=models.Sum('nombre_mois'))
        ).get('total')
        return nombre_mois >= NB_MOIS_MIN_VAE if nombre_mois else False

    @classmethod
    def recuperer_toutes_informations_candidat(
        cls,
        matricule: str,
        formation: str,
        annee_courante: int,
        uuid_proposition: str,
        experiences_cv_recuperees: ExperiencesCVRecuperees = ExperiencesCVRecuperees.TOUTES,
    ) -> ResumeCandidatDTO:
        has_default_language = cls.has_default_language()

        queryset = (
            Person.objects.prefetch_related(
                Prefetch(
                    'personaddress_set',
                    queryset=PersonAddress.objects.filter(
                        label__in=[PersonAddressType.RESIDENTIAL.name, PersonAddressType.CONTACT.name],
                    ).select_related('country'),
                ),
            )
            .select_related(
                'country_of_citizenship',
                'birth_country',
                'last_registration_year',
                'graduated_from_high_school_year',
                'highschooldiplomaalternative',
                'belgianhighschooldiploma__institute',
                'foreignhighschooldiploma__country',
                'foreignhighschooldiploma__linguistic_regime',
            )
            .annotate(
                secondaire_injecte_par_admission=Exists(
                    AdmissionEPCInjection.objects.filter(admission__candidate_id=OuterRef('pk'))
                ),
                secondaire_injecte_par_cv=Exists(
                    CurriculumEPCInjection.objects.filter(
                        type_experience=ExperienceType.HIGH_SCHOOL.name,
                        person_id=OuterRef('pk'),
                    )
                ),
                **cls.get_secondary_studies_valuation_annotations(),
            )
        )

        is_doctorate = formation in AnneeInscriptionFormationTranslator.DOCTORATE_EDUCATION_TYPES
        if is_doctorate:
            queryset = queryset.prefetch_related(
                Prefetch(
                    'languages_knowledge',
                    queryset=LanguageKnowledge.objects.select_related('language')
                    .alias(
                        order=Case(
                            *[
                                When(language__code=language, then=index)
                                for index, language in enumerate(LANGUES_OBLIGATOIRES_DOCTORAT)
                            ],
                            default=len(LANGUES_OBLIGATOIRES_DOCTORAT),
                        ),
                    )
                    .all()
                    .order_by('order', 'language__code'),
                ),
            )

        candidate: Person = queryset.get(global_id=matricule)

        last_registration_year = candidate.last_registration_year.year if candidate.last_registration_year else None
        graduated_from_high_school_year = (
            candidate.graduated_from_high_school_year.year if candidate.graduated_from_high_school_year else None
        )
        coordonnees_dto = cls._get_coordonnees_dto(candidate=candidate, has_default_language=has_default_language)

        curriculum_dto = CurriculumAdmissionDTO(
            annee_derniere_inscription_ucl=last_registration_year,
            annee_diplome_etudes_secondaires=graduated_from_high_school_year,
            experiences_academiques=cls._get_academic_experiences_dtos(
                matricule,
                has_default_language,
                uuid_proposition,
                experiences_cv_recuperees,
            ),
            experiences_non_academiques=cls.get_experiences_non_academiques(
                matricule=matricule,
                uuid_proposition=uuid_proposition,
                experiences_cv_recuperees=experiences_cv_recuperees,
            ),
            annee_minimum_a_remplir=cls.get_annee_minimale_a_completer_cv(
                annee_courante=annee_courante,
                annee_diplome_etudes_secondaires=graduated_from_high_school_year,
                annee_derniere_inscription_ucl=last_registration_year,
            ),
        )
        return ResumeCandidatDTO(
            identification=cls._get_identification_dto(
                candidate=candidate,
                residential_country=coordonnees_dto.domicile_legal.pays if coordonnees_dto.domicile_legal else '',
                has_default_language=has_default_language,
            ),
            coordonnees=coordonnees_dto,
            curriculum=curriculum_dto,
            etudes_secondaires=cls._get_secondary_studies_dto(
                candidate=candidate,
                has_default_language=has_default_language,
            ),
            connaissances_langues=cls._get_language_knowledge_dto(candidate) if is_doctorate else None,
        )
