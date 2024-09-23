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
import uuid
from typing import Dict, List, Optional

from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.db import models
from django.db.models import (
    Exists,
    OuterRef,
    Subquery,
    Prefetch,
    F,
    Value,
    Case,
    When,
    ExpressionWrapper,
    Q,
    BooleanField,
    QuerySet,
)
from django.db.models.functions import ExtractYear, ExtractMonth, Concat
from django.utils.translation import get_language

from admission.contrib.models import EPCInjection as AdmissionEPCInjection
from admission.contrib.models.epc_injection import EPCInjectionType, EPCInjectionStatus as AdmissionEPCInjectionStatus
from admission.contrib.models.functions import ArrayLength
from admission.ddd import LANGUES_OBLIGATOIRES_DOCTORAT
from admission.ddd import NB_MOIS_MIN_VAE
from admission.ddd.admission.doctorat.preparation.dtos import ConditionsComptabiliteDTO
from admission.ddd.admission.doctorat.preparation.dtos.connaissance_langue import ConnaissanceLangueDTO
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import CurriculumAdmissionDTO
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.validator.exceptions import ExperienceNonTrouveeException
from admission.ddd.admission.dtos import AdressePersonnelleDTO, CoordonneesDTO, IdentificationDTO
from admission.ddd.admission.dtos.etudes_secondaires import EtudesSecondairesAdmissionDTO
from admission.ddd.admission.dtos.resume import ResumeCandidatDTO
from admission.ddd.admission.enums.valorisation_experience import (
    ExperiencesCVRecuperees,
)
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.models.enums.community import CommunityEnum
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
from base.models.person_address import PersonAddress
from base.tasks.synchronize_entities_addresses import UCLouvain_acronym
from ddd.logic.shared_kernel.profil.dtos.etudes_secondaires import (
    DiplomeBelgeEtudesSecondairesDTO,
    DiplomeEtrangerEtudesSecondairesDTO,
    AlternativeSecondairesDTO,
    ValorisationEtudesSecondairesDTO,
)
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import (
    AnneeExperienceAcademiqueDTO,
    ExperienceAcademiqueDTO,
    ExperienceNonAcademiqueDTO,
    CurriculumAExperiencesDTO,
)
from osis_profile import BE_ISO_CODE
from osis_profile.models import (
    EducationalExperienceYear,
    ProfessionalExperience,
    EducationalExperience,
)
from osis_profile.models.education import LanguageKnowledge
from osis_profile.models.epc_injection import (
    EPCInjection as CurriculumEPCInjection,
    ExperienceType,
    EPCInjectionStatus as CurriculumEPCInjectionStatus,
)


# TODO: a mettre dans infra/shared_kernel/profil
class ProfilCandidatTranslator(IProfilCandidatTranslator):
    @classmethod
    def has_default_language(cls) -> bool:
        """Returns True if the current language is the default one."""
        return get_language() == settings.LANGUAGE_CODE

    @classmethod
    def _get_identification_dto(
        cls,
        candidate: Person,
        residential_country: str,
        has_default_language: bool,
    ) -> IdentificationDTO:
        """Returns the DTO of the identification data of the given candidate."""
        country_of_citizenship = (
            {
                'pays_nationalite': candidate.country_of_citizenship.iso_code,
                'nom_pays_nationalite': getattr(
                    candidate.country_of_citizenship,
                    'name' if has_default_language else 'name_en',
                ),
                'pays_nationalite_europeen': candidate.country_of_citizenship.european_union,
            }
            if candidate.country_of_citizenship_id
            else {
                'pays_nationalite': '',
                'nom_pays_nationalite': '',
                'pays_nationalite_europeen': None,
            }
        )
        birth_country = (
            {
                'pays_naissance': candidate.birth_country.iso_code,
                'nom_pays_naissance': getattr(candidate.birth_country, 'name' if has_default_language else 'name_en'),
            }
            if candidate.birth_country_id
            else {
                'pays_naissance': '',
                'nom_pays_naissance': '',
            }
        )

        return IdentificationDTO(
            matricule=candidate.global_id,
            nom=candidate.last_name,
            prenom=candidate.first_name,
            date_naissance=candidate.birth_date,
            annee_naissance=candidate.birth_year,
            langue_contact=candidate.language,
            nom_langue_contact=dict(settings.LANGUAGES).get(candidate.language),
            sexe=candidate.sex,
            genre=candidate.gender,
            photo_identite=candidate.id_photo,
            carte_identite=candidate.id_card,
            date_expiration_carte_identite=candidate.id_card_expiry_date,
            passeport=candidate.passport,
            date_expiration_passeport=candidate.passport_expiry_date,
            numero_registre_national_belge=candidate.national_number,
            numero_carte_identite=candidate.id_card_number,
            numero_passeport=candidate.passport_number,
            email=candidate.email,
            lieu_naissance=candidate.birth_place,
            etat_civil=candidate.civil_state,
            annee_derniere_inscription_ucl=candidate.last_registration_year and candidate.last_registration_year.year,
            noma_derniere_inscription_ucl=candidate.last_registration_id,
            pays_residence=residential_country,
            autres_prenoms=candidate.middle_name,
            **country_of_citizenship,
            **birth_country,
        )

    @classmethod
    def _get_address_dto(
        cls,
        address: Optional[PersonAddress],
        has_default_language: bool,
    ) -> Optional[AdressePersonnelleDTO]:
        """Returns the DTO of the given address."""
        return (
            AdressePersonnelleDTO(
                rue=address.street,
                code_postal=address.postal_code or '',
                ville=address.city or '',
                pays=address.country.iso_code if address.country else '',
                nom_pays=getattr(address.country, 'name' if has_default_language else 'name_en')
                if address.country
                else '',
                boite_postale=address.postal_box,
                numero_rue=address.street_number,
            )
            if address
            else None
        )

    @classmethod
    def _get_coordonnees_dto(cls, candidate: Person, has_default_language: bool) -> 'CoordonneesDTO':
        """Returns the DTO of the coordinates of the given candidate."""
        adresses = {a.label: a for a in candidate.personaddress_set.all()}

        residential_address = adresses.get(PersonAddressType.RESIDENTIAL.name)
        contact_address = adresses.get(PersonAddressType.CONTACT.name)

        return CoordonneesDTO(
            numero_mobile=candidate.phone_mobile,
            adresse_email_privee=candidate.private_email,
            domicile_legal=cls._get_address_dto(residential_address, has_default_language),
            adresse_correspondance=cls._get_address_dto(contact_address, has_default_language),
            numero_contact_urgence=candidate.emergency_contact_phone,
        )

    @classmethod
    def get_connaissances_langues(cls, matricule: str) -> List[ConnaissanceLangueDTO]:
        languages = (
            LanguageKnowledge.objects.select_related('language')
            .filter(person__global_id=matricule)
            .alias(
                relevancy=Case(
                    When(language__code='EN', then=2),
                    When(language__code='FR', then=1),
                    default=0,
                ),
            )
            .order_by('-relevancy', 'language__code')
        )
        return cls._get_language_knowledge_dto(languages=languages)

    @classmethod
    def _get_language_knowledge_dto(
        cls,
        candidate: Optional[Person] = None,
        languages: Optional[List[LanguageKnowledge]] = None,
    ) -> List[ConnaissanceLangueDTO]:
        """Returns the DTO of the language knowledge data of the given candidate."""
        return [
            ConnaissanceLangueDTO(
                nom_langue_fr=langue.language.name if langue.language else '',
                nom_langue_en=langue.language.name_en if langue.language else '',
                langue=langue.language.code if langue.language else '',
                comprehension_orale=langue.listening_comprehension or '',
                capacite_orale=langue.speaking_ability or '',
                capacite_ecriture=langue.writing_ability or '',
                certificat=langue.certificate or '',
            )
            for langue in (candidate.languages_knowledge.all() if candidate else languages)
        ]

    @classmethod
    def _get_secondary_studies_dto(
        cls,
        candidate: Person,
        has_default_language: bool,
    ):
        belgian_high_school_diploma = getattr(candidate, 'belgianhighschooldiploma', None)
        foreign_high_school_diploma = getattr(candidate, 'foreignhighschooldiploma', None)
        high_school_diploma_alternative = getattr(candidate, 'highschooldiplomaalternative', None)

        potential_diploma = belgian_high_school_diploma or foreign_high_school_diploma
        return EtudesSecondairesAdmissionDTO(
            diplome_etudes_secondaires=candidate.graduated_from_high_school,
            valorisation=ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=candidate.is_valuated_by_epc,  # From annotation
                types_formations_admissions_valorisees=candidate.valuated_training_types,  # From annotation
            ),
            annee_diplome_etudes_secondaires=candidate.graduated_from_high_school_year.year
            if candidate.graduated_from_high_school_year
            else None,
            diplome_belge=DiplomeBelgeEtudesSecondairesDTO(
                uuid=belgian_high_school_diploma.uuid,
                diplome=belgian_high_school_diploma.high_school_diploma,
                type_enseignement=belgian_high_school_diploma.educational_type,
                autre_type_enseignement=belgian_high_school_diploma.educational_other,
                nom_institut=belgian_high_school_diploma.institute.name
                if belgian_high_school_diploma.institute_id
                else belgian_high_school_diploma.other_institute_name,
                adresse_institut=getattr(candidate, 'belgian_highschool_diploma_institute_address', '')
                if belgian_high_school_diploma.institute_id
                else belgian_high_school_diploma.other_institute_address,
                communaute=belgian_high_school_diploma.community or '',
            )
            if belgian_high_school_diploma
            else None,
            diplome_etranger=DiplomeEtrangerEtudesSecondairesDTO(
                uuid=foreign_high_school_diploma.uuid,
                type_diplome=foreign_high_school_diploma.foreign_diploma_type,
                regime_linguistique=foreign_high_school_diploma.linguistic_regime.code
                if foreign_high_school_diploma.linguistic_regime
                else foreign_high_school_diploma.other_linguistic_regime,
                pays_regime_linguistique=getattr(
                    foreign_high_school_diploma.linguistic_regime,
                    'name' if has_default_language else 'name_en',
                )
                if foreign_high_school_diploma.linguistic_regime
                else foreign_high_school_diploma.other_linguistic_regime,
                pays_membre_ue=foreign_high_school_diploma.country.european_union,
                pays_iso_code=foreign_high_school_diploma.country.iso_code,
                pays_nom=getattr(foreign_high_school_diploma.country, 'name' if has_default_language else 'name_en'),
                releve_notes=foreign_high_school_diploma.high_school_transcript,
                traduction_releve_notes=foreign_high_school_diploma.high_school_transcript_translation,
                diplome=foreign_high_school_diploma.high_school_diploma,
                traduction_diplome=foreign_high_school_diploma.high_school_diploma_translation,
                equivalence=foreign_high_school_diploma.equivalence,
                decision_final_equivalence_ue=foreign_high_school_diploma.final_equivalence_decision_ue,
                decision_final_equivalence_hors_ue=foreign_high_school_diploma.final_equivalence_decision_not_ue,
                preuve_decision_equivalence=foreign_high_school_diploma.equivalence_decision_proof,
            )
            if foreign_high_school_diploma
            else None,
            alternative_secondaires=AlternativeSecondairesDTO(
                uuid=high_school_diploma_alternative.uuid,
                examen_admission_premier_cycle=high_school_diploma_alternative.first_cycle_admission_exam,
            )
            if high_school_diploma_alternative
            else None,
            identifiant_externe=potential_diploma.external_id if potential_diploma else None,
            injectee=candidate.secondaire_injecte_par_admission or candidate.secondaire_injecte_par_cv,
        )

    @classmethod
    def _get_non_academic_experiences_dtos(
        cls,
        experiences_non_academiques: QuerySet[ProfessionalExperience],
    ) -> List[ExperienceNonAcademiqueDTO]:
        return [
            ExperienceNonAcademiqueDTO(
                date_debut=experience.start_date,
                date_fin=experience.end_date,
                employeur=experience.institute_name,
                type=experience.type,
                certificat=experience.certificate,
                fonction=experience.role,
                secteur=experience.sector,
                autre_activite=experience.activity,
                uuid=experience.uuid,
                valorisee_par_admissions=getattr(experience, 'valuated_from_admissions', None),
                injectee=experience.injecte_par_admission or experience.injecte_par_cv,
                identifiant_externe=experience.external_id,
            )
            for experience in experiences_non_academiques
        ]

    @classmethod
    def _get_academic_experience_year_dto(cls, educational_experience_year: EducationalExperienceYear):
        return AnneeExperienceAcademiqueDTO(
            uuid=educational_experience_year.uuid,
            resultat=educational_experience_year.result,
            annee=educational_experience_year.academic_year.year,
            releve_notes=educational_experience_year.transcript,
            traduction_releve_notes=educational_experience_year.transcript_translation,
            credits_inscrits=educational_experience_year.registered_credit_number,
            credits_acquis=educational_experience_year.acquired_credit_number,
            avec_bloc_1=educational_experience_year.with_block_1,
            avec_complement=educational_experience_year.with_complement,
            allegement=educational_experience_year.reduction,
            est_reorientation_102=educational_experience_year.is_102_change_of_course,
            credits_inscrits_communaute_fr=educational_experience_year.fwb_registered_credit_number,
            credits_acquis_communaute_fr=educational_experience_year.fwb_acquired_credit_number,
        )

    @classmethod
    def _get_academic_experiences_dtos(
        cls,
        matricule: str,
        has_default_language: bool,
        uuid_proposition: str,
        experiences_cv_recuperees: ExperiencesCVRecuperees = ExperiencesCVRecuperees.TOUTES,
        uuid_experience: str = '',
    ) -> List[ExperienceAcademiqueDTO]:
        """Returns the DTO of the academic experiences of the given candidate."""

        educational_experience_years: QuerySet[EducationalExperienceYear] = (
            EducationalExperienceYear.objects.filter(
                educational_experience__person__global_id=matricule,
            )
            .select_related(
                'academic_year',
                'educational_experience__country',
                'educational_experience__linguistic_regime',
                'educational_experience__program',
                'educational_experience__fwb_equivalent_program',
                'educational_experience__institute',
            )
            .order_by('-academic_year__year')
        )

        educational_experience_years = educational_experience_years.annotate(
            valuated_from_admissions=ArrayAgg(
                'educational_experience__valuated_from_admission__uuid',
                filter=Q(educational_experience__valuated_from_admission__isnull=False),
            ),
        )

        if experiences_cv_recuperees == ExperiencesCVRecuperees.SEULEMENT_VALORISEES:
            educational_experience_years = educational_experience_years.alias(
                nb_valuated_admissions=ArrayLength('valuated_from_admissions'),
            ).filter(nb_valuated_admissions__gt=0)
        elif experiences_cv_recuperees == ExperiencesCVRecuperees.SEULEMENT_VALORISEES_PAR_ADMISSION:
            educational_experience_years = educational_experience_years.filter(
                educational_experience__educational_valuated_experiences__baseadmission_id=uuid.UUID(
                    str(uuid_proposition)
                )
            )

        if uuid_experience:
            educational_experience_years = educational_experience_years.filter(
                educational_experience__uuid=uuid_experience,
            )

        educational_experience_years = educational_experience_years.annotate(
            injecte_par_admission=Exists(
                AdmissionEPCInjection.objects.filter(
                    admission__uuid=OuterRef('educational_experience__valuated_from_admission__uuid'),
                    type=EPCInjectionType.DEMANDE.name,
                    status__in=AdmissionEPCInjectionStatus.blocking_statuses_for_experience(),
                )
            ),
            injecte_par_cv=Exists(
                CurriculumEPCInjection.objects.filter(
                    experience_uuid=OuterRef('educational_experience__uuid'),
                    status__in=CurriculumEPCInjectionStatus.blocking_statuses_for_experience(),
                )
            ),
        )
        educational_experience_dtos: Dict[int, ExperienceAcademiqueDTO] = {}
        for experience_year in educational_experience_years:
            experience_year_dto = cls._get_academic_experience_year_dto(experience_year)
            if experience_year.educational_experience.pk not in educational_experience_dtos:
                institute = (
                    {
                        'nom_institut': experience_year.educational_experience.institute.name,
                        'code_institut': experience_year.educational_experience.institute.acronym,
                        'communaute_institut': experience_year.educational_experience.institute.community,
                        'adresse_institut': '',
                        'type_institut': experience_year.educational_experience.institute.establishment_type,
                    }
                    if experience_year.educational_experience.institute
                    else {
                        'nom_institut': experience_year.educational_experience.institute_name,
                        'code_institut': '',
                        'communaute_institut': '',
                        'adresse_institut': experience_year.educational_experience.institute_address,
                        'type_institut': '',
                    }
                )
                linguistic_regime = (
                    {
                        'regime_linguistique': experience_year.educational_experience.linguistic_regime.code,
                        'nom_regime_linguistique': getattr(
                            experience_year.educational_experience.linguistic_regime,
                            'name' if has_default_language else 'name_en',
                        ),
                    }
                    if experience_year.educational_experience.linguistic_regime
                    else {
                        'regime_linguistique': '',
                        'nom_regime_linguistique': '',
                    }
                )
                program_info = {
                    'nom_formation': '',
                    'nom_formation_equivalente_communaute_fr': '',
                    'cycle_formation': '',
                    'est_autre_formation': None,
                }

                if experience_year.educational_experience.education_name:
                    program_info['nom_formation'] = experience_year.educational_experience.education_name
                    program_info['est_autre_formation'] = True

                if experience_year.educational_experience.program_id:
                    program_info['nom_formation'] = experience_year.educational_experience.program.title
                    program_info['cycle_formation'] = experience_year.educational_experience.program.cycle
                    program_info['est_autre_formation'] = False

                if experience_year.educational_experience.fwb_equivalent_program_id:
                    program_info[
                        'nom_formation_equivalente_communaute_fr'
                    ] = experience_year.educational_experience.fwb_equivalent_program.title
                    program_info[
                        'cycle_formation'
                    ] = experience_year.educational_experience.fwb_equivalent_program.cycle

                educational_experience_dtos[experience_year.educational_experience.pk] = ExperienceAcademiqueDTO(
                    uuid=experience_year.educational_experience.uuid,
                    pays=experience_year.educational_experience.country.iso_code,
                    nom_pays=getattr(
                        experience_year.educational_experience.country,
                        'name' if has_default_language else 'name_en',
                    ),
                    a_obtenu_diplome=experience_year.educational_experience.obtained_diploma,
                    rang_diplome=experience_year.educational_experience.rank_in_diploma,
                    date_prevue_delivrance_diplome=experience_year.educational_experience.expected_graduation_date,
                    titre_memoire=experience_year.educational_experience.dissertation_title,
                    note_memoire=experience_year.educational_experience.dissertation_score,
                    resume_memoire=experience_year.educational_experience.dissertation_summary,
                    releve_notes=experience_year.educational_experience.transcript,
                    traduction_releve_notes=experience_year.educational_experience.transcript_translation,
                    diplome=experience_year.educational_experience.graduate_degree,
                    traduction_diplome=experience_year.educational_experience.graduate_degree_translation,
                    type_releve_notes=experience_year.educational_experience.transcript_type,
                    annees=[experience_year_dto],
                    grade_obtenu=experience_year.educational_experience.obtained_grade,
                    systeme_evaluation=experience_year.educational_experience.evaluation_type,
                    type_enseignement=experience_year.educational_experience.study_system,
                    valorisee_par_admissions=getattr(experience_year, 'valuated_from_admissions', None),
                    injectee=experience_year.injecte_par_admission or experience_year.injecte_par_cv,
                    identifiant_externe=experience_year.educational_experience.external_id,
                    **institute,
                    **linguistic_regime,
                    **program_info,
                )
            else:
                educational_experience_dtos[experience_year.educational_experience.pk].annees.append(
                    experience_year_dto
                )
        return list(educational_experience_dtos.values())

    @classmethod
    def get_identification(cls, matricule: str) -> 'IdentificationDTO':

        person = (
            Person.objects.select_related(
                'country_of_citizenship',
                'birth_country',
                'last_registration_year',
            )
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

        return cls._get_identification_dto(
            candidate=person,
            residential_country=person.residential_country_iso_code or '',
            has_default_language=cls.has_default_language(),
        )

    @classmethod
    def get_coordonnees(cls, matricule: str) -> 'CoordonneesDTO':
        candidat = (
            Person.objects.prefetch_related(
                Prefetch(
                    "personaddress_set",
                    queryset=PersonAddress.objects.filter(
                        label__in=[PersonAddressType.CONTACT.name, PersonAddressType.RESIDENTIAL.name]
                    ).select_related("country"),
                )
            )
            .only('private_email', 'phone_mobile', 'emergency_contact_phone')
            .get(global_id=matricule)
        )

        return cls._get_coordonnees_dto(candidate=candidat, has_default_language=cls.has_default_language())

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
    def get_secondary_studies_valuation_annotations(cls):
        return dict(
            belgian_highschool_diploma_institute_address=Concat(
                F('belgianhighschooldiploma__institute__entity__entityversion__entityversionaddress__street'),
                Value(' '),
                F('belgianhighschooldiploma__institute__entity__entityversion__entityversionaddress__street_number'),
                Value(', '),
                F('belgianhighschooldiploma__institute__entity__entityversion__entityversionaddress__postal_code'),
                Value(' '),
                F('belgianhighschooldiploma__institute__entity__entityversion__entityversionaddress__city'),
            ),
            is_valuated_by_epc=ExpressionWrapper(
                Q(belgianhighschooldiploma__external_id__isnull=False)
                | Q(foreignhighschooldiploma__external_id__isnull=False),
                output_field=BooleanField(),
            ),
            valuated_training_types=ArrayAgg(
                'baseadmissions__training__education_group_type__name',
                filter=Q(baseadmissions__valuated_secondary_studies_person_id=F('pk')),
            ),
        )

    @classmethod
    def get_etudes_secondaires(cls, matricule: str) -> 'EtudesSecondairesAdmissionDTO':
        candidate: Person = (
            Person.objects.select_related(
                'graduated_from_high_school_year',
                'highschooldiplomaalternative',
                'belgianhighschooldiploma__institute',
                'foreignhighschooldiploma__country',
                'foreignhighschooldiploma__linguistic_regime',
            )
            .annotate(
                secondaire_injecte_par_admission=Exists(
                    AdmissionEPCInjection.objects.filter(
                        admission__candidate_id=OuterRef('pk'),
                        type=EPCInjectionType.DEMANDE.name,
                        status__in=AdmissionEPCInjectionStatus.blocking_statuses_for_experience(),
                    )
                ),
                secondaire_injecte_par_cv=Exists(
                    CurriculumEPCInjection.objects.filter(
                        type_experience=ExperienceType.HIGH_SCHOOL.name,
                        person_id=OuterRef('pk'),
                        status__in=CurriculumEPCInjectionStatus.blocking_statuses_for_experience(),
                    )
                ),
                **cls.get_secondary_studies_valuation_annotations(),
            )
            .get(global_id=matricule)
        )

        return cls._get_secondary_studies_dto(
            candidate,
            cls.has_default_language(),
        )

    @classmethod
    def get_experiences_non_academiques(
        cls,
        matricule: str,
        uuid_proposition: str,
        experiences_cv_recuperees: ExperiencesCVRecuperees = ExperiencesCVRecuperees.TOUTES,
        uuid_experience: str = '',
    ) -> List[ExperienceNonAcademiqueDTO]:
        non_academic_experiences: QuerySet[ProfessionalExperience] = (
            ProfessionalExperience.objects.filter(
                person__global_id=matricule,
            )
            .annotate(
                valuated_from_admissions=ArrayAgg(
                    'valuated_from_admission__uuid',
                    filter=Q(valuated_from_admission__isnull=False),
                ),
                injecte_par_admission=Exists(
                    AdmissionEPCInjection.objects.filter(
                        admission__uuid=OuterRef('valuated_from_admission__uuid'),
                        type=EPCInjectionType.DEMANDE.name,
                        status__in=AdmissionEPCInjectionStatus.blocking_statuses_for_experience(),
                    )
                ),
                injecte_par_cv=Exists(
                    CurriculumEPCInjection.objects.filter(
                        experience_uuid=OuterRef('uuid'),
                        status__in=CurriculumEPCInjectionStatus.blocking_statuses_for_experience(),
                    )
                ),
            )
            .order_by('-start_date', '-end_date')
        )

        if experiences_cv_recuperees == ExperiencesCVRecuperees.SEULEMENT_VALORISEES:
            non_academic_experiences = non_academic_experiences.alias(
                nb_valuated_admissions=ArrayLength('valuated_from_admissions'),
            ).filter(nb_valuated_admissions__gt=0)
        elif experiences_cv_recuperees == ExperiencesCVRecuperees.SEULEMENT_VALORISEES_PAR_ADMISSION:
            non_academic_experiences = non_academic_experiences.filter(
                professional_valuated_experiences__baseadmission_id=uuid.UUID(str(uuid_proposition))
            )

        if uuid_experience:
            non_academic_experiences = non_academic_experiences.filter(uuid=uuid_experience)[:1]

        return cls._get_non_academic_experiences_dtos(non_academic_experiences)

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
    def get_experience_academique(
        cls,
        matricule: str,
        uuid_proposition: str,
        uuid_experience: str,
    ) -> 'ExperienceAcademiqueDTO':
        experiences = cls._get_academic_experiences_dtos(
            matricule,
            cls.has_default_language(),
            uuid_proposition,
            uuid_experience=uuid_experience,
        )

        if not experiences:
            raise ExperienceNonTrouveeException

        return experiences[0]

    @classmethod
    def get_experience_non_academique(
        cls,
        matricule: str,
        uuid_proposition: str,
        uuid_experience: str,
    ) -> 'ExperienceNonAcademiqueDTO':
        experiences = cls.get_experiences_non_academiques(
            matricule,
            uuid_proposition=uuid_proposition,
            uuid_experience=uuid_experience,
        )

        if not experiences:
            raise ExperienceNonTrouveeException

        return experiences[0]

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
                IProfilCandidatTranslator.MOIS_DEBUT_ANNEE_ACADEMIQUE_A_VALORISER,
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
                    AdmissionEPCInjection.objects.filter(
                        admission__candidate_id=OuterRef('pk'),
                        type=EPCInjectionType.DEMANDE.name,
                        status__in=AdmissionEPCInjectionStatus.blocking_statuses_for_experience(),
                    )
                ),
                secondaire_injecte_par_cv=Exists(
                    CurriculumEPCInjection.objects.filter(
                        type_experience=ExperienceType.HIGH_SCHOOL.name,
                        person_id=OuterRef('pk'),
                        status__in=CurriculumEPCInjectionStatus.blocking_statuses_for_experience(),
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
