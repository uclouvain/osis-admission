##############################################################################
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
##############################################################################
import datetime
from abc import ABC
from typing import List, Optional

from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AdresseDomicileLegalNonCompleteeException,
)
from admission.ddd.admission.domain.enums import TypeFormation
from admission.ddd.admission.domain.service.i_annee_inscription_formation import (
    Date,
    IAnneeInscriptionFormationTranslator,
)
from admission.ddd.admission.domain.service.i_titres_acces import ConditionAccess
from admission.ddd.admission.domain.validator._should_identification_candidat_etre_completee import BE_ISO_CODE
from admission.ddd.admission.dtos import AdressePersonnelleDTO, IdentificationDTO
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition as PropositionGenerale
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from admission.infrastructure.admission.domain.service.profil_candidat import IProfilCandidatTranslator
from base.business.academic_calendar import AcademicEventSessionCalendarHelper
from base.models.academic_calendar import AcademicCalendar
from base.models.academic_year import AcademicYear
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from reference.models.country import Country

__all__ = [
    "AdmissionPoolExternalEnrollmentChangeCalendar",
    "AdmissionPoolExternalReorientationCalendar",
    "AdmissionPoolHue5BelgiumResidencyCalendar",
    "AdmissionPoolHue5ForeignResidencyCalendar",
    "AdmissionPoolHueUclPathwayChangeCalendar",
    "AdmissionPoolInstituteChangeCalendar",
    "AdmissionPoolNonResidentQuotaCalendar",
    "AdmissionPoolUe5BelgianCalendar",
    "AdmissionPoolUe5NonBelgianCalendar",
    "AdmissionPoolVipCalendar",
    "ContinuingEducationAdmissionCalendar",
    "DoctorateAdmissionCalendar",
    "GeneralEducationAdmissionCalendar",
    "SIGLES_WITH_QUOTA",
    "est_formation_contingentee_et_non_resident",
    "PoolCalendar",
]

DIPLOMES_ACCES_BELGE = [
    ConditionAccess.DIPLOMATION_POTENTIEL_MASTER_BELGE,
    ConditionAccess.POTENTIEL_MASTER_BELGE_SANS_DIPLOMATION,
    ConditionAccess.DIPLOMATION_SECONDAIRE_BELGE,
    ConditionAccess.DIPLOMATION_ACADEMIQUE_BELGE,
    ConditionAccess.POTENTIEL_BACHELIER_BELGE_SANS_DIPLOMATION,
    ConditionAccess.DIPLOMATION_POTENTIEL_DOCTORAT_BELGE,
]

SIGLES_WITH_QUOTA = ['KINE1BA', 'VETE1BA', 'LOGO1BA']

SECOND_CYCLE_TYPES = [
    TrainingType.AGGREGATION.name,
    TrainingType.CAPAES.name,
    TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE.name,
] + AnneeInscriptionFormationTranslator.OSIS_ADMISSION_EDUCATION_TYPES_MAPPING[TypeFormation.MASTER.name]


def ensure_consistency_until_n_plus_6(event_reference: str, cutover_date: Date, title: str, end_date: Date = None):
    current_academic_year = AcademicYear.objects.current()
    academic_years = AcademicYear.objects.min_max_years(current_academic_year.year - 1, current_academic_year.year + 6)

    for ac_year in academic_years:
        if end_date is None:
            ac_end_date = datetime.date(
                ac_year.year + 1 + cutover_date.annee, cutover_date.mois, cutover_date.jour
            ) - datetime.timedelta(days=1)
        else:
            ac_end_date = datetime.date(ac_year.year + end_date.annee, end_date.mois, end_date.jour)
        AcademicCalendar.objects.get_or_create(
            reference=event_reference,
            data_year=ac_year,
            defaults={
                'start_date': datetime.date(ac_year.year + cutover_date.annee, cutover_date.mois, cutover_date.jour),
                'end_date': ac_end_date,
                'title': title,
            },
        )


def est_formation_contingentee_et_non_resident(sigle: str, proposition: 'PropositionGenerale'):
    return sigle in SIGLES_WITH_QUOTA and proposition.est_non_resident_au_sens_decret is True


class PoolCalendar(AcademicEventSessionCalendarHelper, ABC):
    cutover_date: Date
    end_date: Optional[Date]

    @classmethod
    def matches_criteria(
        cls,
        annee_academique: int,
        sigle: str,
        access_diplomas: List[str],
        program: 'TrainingType',
        nationalite: 'Country',
        annee_derniere_inscription_ucl: Optional[int],
        profil_candidat_translator: 'IProfilCandidatTranslator',
        profile: 'IdentificationDTO',
        residential_address: 'AdressePersonnelleDTO',
        proposition: 'PropositionGenerale' = None,
    ) -> bool:
        raise NotImplementedError


class DoctorateAdmissionCalendar(PoolCalendar):
    event_reference = AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT.name
    cutover_date = IAnneeInscriptionFormationTranslator.DATE_BASCULE_DOCTORAT

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=IAnneeInscriptionFormationTranslator.DATE_BASCULE_DOCTORAT,
            title='Admission - Doctorat',
        )

    @classmethod
    def matches_criteria(cls, program: TrainingType, **kwargs) -> bool:
        """Candidat inscrit en doctorat"""
        return program == TrainingType.PHD


class GeneralEducationAdmissionCalendar(AcademicEventSessionCalendarHelper):
    event_reference = AcademicCalendarTypes.GENERAL_EDUCATION_ENROLLMENT.name

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=IAnneeInscriptionFormationTranslator.DATE_BASCULE_FORMATION_GENERALE,
            title='Admission - Formation générale',
        )


class ContinuingEducationAdmissionCalendar(PoolCalendar):
    event_reference = AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT.name
    cutover_date = IAnneeInscriptionFormationTranslator.DATE_BASCULE_FORMATION_CONTINUE

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=IAnneeInscriptionFormationTranslator.DATE_BASCULE_FORMATION_CONTINUE,
            title='Admission - Formation continue',
        )

    @classmethod
    def matches_criteria(cls, program: TrainingType, **kwargs) -> bool:
        """Candidat inscrit à la formation continue"""
        return program.name in AnneeInscriptionFormationTranslator.CONTINUING_EDUCATION_TYPES


class AdmissionPoolExternalEnrollmentChangeCalendar(PoolCalendar):
    event_reference = AcademicCalendarTypes.ADMISSION_POOL_EXTERNAL_ENROLLMENT_CHANGE.name
    cutover_date = Date(jour=1, mois=10, annee=0)
    end_date = Date(jour=31, mois=10, annee=0)

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=cls.cutover_date,
            end_date=cls.end_date,
            title="Admission - Modification d'inscription externe",
        )

    @classmethod
    def matches_criteria(cls, program: TrainingType, sigle: str, proposition: 'PropositionGenerale', **kwargs) -> bool:
        """Candidat déjà inscrit l'année N à un autre établissement CF
        (informatiquement : a répondu "oui" à la question sur la modif)"""
        return bool(
            program == TrainingType.BACHELOR
            and proposition.est_modification_inscription_externe
            and not est_formation_contingentee_et_non_resident(sigle, proposition)
        )


class AdmissionPoolExternalReorientationCalendar(PoolCalendar):
    event_reference = AcademicCalendarTypes.ADMISSION_POOL_EXTERNAL_REORIENTATION.name
    cutover_date = Date(jour=1, mois=11, annee=0)
    end_date = Date(jour=15, mois=2, annee=1)

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=cls.cutover_date,
            end_date=cls.end_date,
            title='Admission - Réorientation externe',
        )

    @classmethod
    def matches_criteria(cls, program: TrainingType, sigle: str, proposition: 'PropositionGenerale', **kwargs) -> bool:
        """Candidat déjà inscrit l'année N à un autre établissement CF
        (informatiquement : a répondu ""oui"" à la question sur la réori.)"""
        return bool(
            program == TrainingType.BACHELOR
            and proposition.est_reorientation_inscription_externe
            and not est_formation_contingentee_et_non_resident(sigle, proposition)
        )


class AdmissionPoolVipCalendar(PoolCalendar):
    event_reference = AcademicCalendarTypes.ADMISSION_POOL_VIP.name
    cutover_date = Date(jour=1, mois=11, annee=-1)

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=cls.cutover_date,
            title='Admission - VIP (DD, ErasmsusM, boursierI)',
        )

    @classmethod
    def matches_criteria(
        cls,
        program: TrainingType,
        proposition: PropositionGenerale,
        **kwargs,
    ) -> bool:
        """Candidat est en Double diplôme, Erasmus mundus, BoursierI
        (informatiquement : a coché oui pour une des 3 questions)"""
        return (
            # 2e cycle
            program.name in SECOND_CYCLE_TYPES
            # bourses
            and any(
                [
                    proposition.bourse_double_diplome_id,
                    proposition.bourse_erasmus_mundus_id,
                    proposition.bourse_internationale_id,
                ]
            )
        )


class AdmissionPoolHueUclPathwayChangeCalendar(PoolCalendar):
    event_reference = AcademicCalendarTypes.ADMISSION_POOL_HUE_UCL_PATHWAY_CHANGE.name
    cutover_date = Date(jour=1, mois=11, annee=-1)

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=cls.cutover_date,
            title="Admission - HUE changement de filiere au sein de l'UCLouvain",
        )

    @classmethod
    def matches_criteria(
        cls,
        ue_plus_5: bool,
        matricule_candidat: str,
        annee_academique: int,
        annee_derniere_inscription_ucl: Optional[int],
        sigle: str,
        proposition: 'PropositionGenerale',
        **kwargs,
    ) -> bool:
        """Candidat inscrit à l'UCLouvain en N-1 dans une autre filière
        (informatiquement : identification / dernière année UCLouvain = N-1)"""
        hors_ue_plus_5 = not ue_plus_5
        return (
            hors_ue_plus_5
            and annee_derniere_inscription_ucl == annee_academique - 1
            and not est_formation_contingentee_et_non_resident(sigle, proposition)
        )


class AdmissionPoolInstituteChangeCalendar(PoolCalendar):
    event_reference = AcademicCalendarTypes.ADMISSION_POOL_INSTITUT_CHANGE.name
    cutover_date = Date(jour=1, mois=10, annee=-1)

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=cls.cutover_date,
            title="Admission - Changement d'établissement",
        )

    @classmethod
    def matches_criteria(
        cls,
        annee_academique: int,
        access_diplomas: List[str],
        residential_address: Optional[AdressePersonnelleDTO],
        matricule_candidat: str,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        sigle: str,
        proposition: 'PropositionGenerale',
        **kwargs,
    ) -> bool:
        """Candidat inscrit à un autre établissement Belge en N-1
        (informatiquement : curriculum / en N-1 supérieur belge non-diplômé*)"""
        if residential_address is None:
            raise AdresseDomicileLegalNonCompleteeException()
        return (
            any(belgian_diploma in access_diplomas for belgian_diploma in DIPLOMES_ACCES_BELGE)
            and residential_address.pays == BE_ISO_CODE
            and profil_candidat_translator.est_changement_etablissement(matricule_candidat, annee_academique)
            and not est_formation_contingentee_et_non_resident(sigle, proposition)
        )


class AdmissionPoolUe5BelgianCalendar(PoolCalendar):
    event_reference = AcademicCalendarTypes.ADMISSION_POOL_UE5_BELGIAN.name
    cutover_date = Date(jour=1, mois=11, annee=-1)

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=cls.cutover_date,
            title="Admission - Nationalité UE+5 et diplôme d'accès belge",
        )

    @classmethod
    def matches_criteria(
        cls,
        ue_plus_5: bool,
        access_diplomas: List[str],
        sigle: str,
        proposition: 'PropositionGenerale',
        **kwargs,
    ) -> bool:
        """Candidat ayant la nationalité dans UE ou 5 pays (Suisse, Islande, Norvège, Liechtenstein, Monaco)
        et un diplôme d'accès Belge"""
        return (
            ue_plus_5
            and any(belgian_diploma in access_diplomas for belgian_diploma in DIPLOMES_ACCES_BELGE)
            and not est_formation_contingentee_et_non_resident(sigle, proposition)
        )


class AdmissionPoolUe5NonBelgianCalendar(PoolCalendar):
    event_reference = AcademicCalendarTypes.ADMISSION_POOL_UE5_NON_BELGIAN.name
    cutover_date = Date(jour=1, mois=9, annee=0)

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=cls.cutover_date,
            title="Admission - Nationalité UE+5 et diplôme d'accès non-belge",
        )

    @classmethod
    def matches_criteria(
        cls,
        ue_plus_5: bool,
        access_diplomas: List[str],
        sigle: str,
        proposition: 'PropositionGenerale',
        **kwargs,
    ) -> bool:
        """Candidat ayant la nationalité dans UE ou 5 pays (Suisse, Islande, Norvège, Liechtenstein, Monaco)
        et un diplôme d'accès non-belge"""
        return (
            ue_plus_5
            and not any(belgian_diploma in access_diplomas for belgian_diploma in DIPLOMES_ACCES_BELGE)
            and not est_formation_contingentee_et_non_resident(sigle, proposition)
        )


class AdmissionPoolHue5BelgiumResidencyCalendar(PoolCalendar):
    event_reference = AcademicCalendarTypes.ADMISSION_POOL_HUE5_BELGIUM_RESIDENCY.name
    cutover_date = Date(jour=1, mois=9, annee=0)

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=cls.cutover_date,
            title="Admission - Nationalité Hors(UE+5) et résidence en Belgique",
        )

    @classmethod
    def matches_criteria(
        cls,
        ue_plus_5: bool,
        residential_address: Optional[AdressePersonnelleDTO],
        sigle: str,
        proposition: 'PropositionGenerale',
        **kwargs,
    ) -> bool:
        """Candidat ayant la nationalité Hors(UE+5) et résident en Belgique"""
        if residential_address is None:  # pragma: no cover
            raise AdresseDomicileLegalNonCompleteeException()
        return (
            not ue_plus_5
            and residential_address.pays == BE_ISO_CODE
            and not est_formation_contingentee_et_non_resident(sigle, proposition)
        )


class AdmissionPoolHue5ForeignResidencyCalendar(PoolCalendar):
    event_reference = AcademicCalendarTypes.ADMISSION_POOL_HUE5_FOREIGN_RESIDENCY.name
    cutover_date = Date(jour=1, mois=5, annee=0)
    end_date = Date(jour=30, mois=4, annee=1)

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=cls.cutover_date,
            end_date=cls.end_date,
            title="Admission - Nationalité Hors(UE+5) et résidence à l'étranger",
        )

    @classmethod
    def matches_criteria(
        cls,
        ue_plus_5: bool,
        residential_address: Optional[AdressePersonnelleDTO],
        sigle: str,
        proposition: 'PropositionGenerale',
        **kwargs,
    ) -> bool:
        """Candidat ayant la nationalité HUE et résident à l'étranger"""
        if residential_address is None:  # pragma: no cover
            raise AdresseDomicileLegalNonCompleteeException()
        return (
            not ue_plus_5
            and residential_address.pays != BE_ISO_CODE
            and not est_formation_contingentee_et_non_resident(sigle, proposition)
        )


class AdmissionPoolNonResidentQuotaCalendar(PoolCalendar):
    event_reference = AcademicCalendarTypes.ADMISSION_POOL_NON_RESIDENT_QUOTA.name
    cutover_date = Date(jour=1, mois=6, annee=0)
    end_date = Date(jour=3, mois=6, annee=0)

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=cls.cutover_date,
            end_date=cls.end_date,
            title="Admission - Contingenté non-résident (au sens du décret)",
        )

    @classmethod
    def matches_criteria(cls, sigle: str, proposition: 'PropositionGenerale', **kwargs) -> bool:
        """Candidat inscrit à la formation contingentée, et il n'est pas résident"""
        return est_formation_contingentee_et_non_resident(sigle, proposition)
