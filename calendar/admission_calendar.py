# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from abc import ABC
from typing import Dict, List, Optional

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
from admission.ddd.admission.dtos import AdressePersonnelleDTO
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
    "AdmissionAccessConditionsUrl",
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
    ConditionAccess.POTENTIEL_ACCES_VAE,
    ConditionAccess.ALTERNATIVE_ETUDES_SECONDAIRES,
]

SIGLES_WITH_QUOTA = ['KINE1BA', 'VETE1BA', 'LOGO1BA']

SECOND_CYCLE_TYPES = [
    TrainingType.AGGREGATION.name,
    TrainingType.CAPAES.name,
    TrainingType.UNIVERSITY_SECOND_CYCLE_CERTIFICATE.name,
] + AnneeInscriptionFormationTranslator.OSIS_ADMISSION_EDUCATION_TYPES_MAPPING[TypeFormation.MASTER.name]

DAY_BEFORE_NEXT = object()


def ensure_consistency_until_n_plus_6(
    event_reference: str,
    cutover_date: Date,
    title: str,
    end_date: Optional[Date] = DAY_BEFORE_NEXT,
):
    current_academic_year = AcademicYear.objects.current()
    academic_years = AcademicYear.objects.min_max_years(current_academic_year.year - 1, current_academic_year.year + 6)

    for ac_year in academic_years:
        ac_end_date = None
        if end_date is DAY_BEFORE_NEXT:
            ac_end_date = datetime.date(
                ac_year.year + 1 + cutover_date.annee, cutover_date.mois, cutover_date.jour
            ) - datetime.timedelta(days=1)
        elif end_date is not None:
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


class AdmissionAccessConditionsUrl(AcademicEventSessionCalendarHelper):
    event_reference = AcademicCalendarTypes.ADMISSION_ACCESS_CONDITIONS_URL.name
    cutover_date = Date(jour=14, mois=3, annee=0)
    end_date = None

    @classmethod
    def ensure_consistency_until_n_plus_6(cls):
        ensure_consistency_until_n_plus_6(
            event_reference=cls.event_reference,
            cutover_date=cls.cutover_date,
            end_date=cls.end_date,
            title="Publication du catalogue de formation sur le site UCLouvain",
        )


def est_formation_contingentee_et_non_resident(sigle: str, proposition: Optional['PropositionGenerale']):
    return sigle in SIGLES_WITH_QUOTA and proposition.est_non_resident_au_sens_decret is True


class PoolCalendar(AcademicEventSessionCalendarHelper, ABC):
    cutover_date: Date
    end_date: Optional[Date]

    @classmethod
    def matches_criteria(
        cls,
        annee_academique: int,
        sigle: str,
        ue_plus_5: bool,
        access_diplomas: List[str],
        training_type: 'TrainingType',
        residential_address: 'AdressePersonnelleDTO',
        annee_derniere_inscription_ucl: Optional[int],
        matricule_candidat: str,
        profil_candidat_translator: 'IProfilCandidatTranslator',
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
    def matches_criteria(cls, training_type: TrainingType, **kwargs) -> bool:
        """Candidat inscrit en doctorat"""
        return training_type == TrainingType.PHD


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
    def matches_criteria(cls, training_type: TrainingType, **kwargs) -> bool:
        """Candidat inscrit à la formation continue"""
        return training_type.name in AnneeInscriptionFormationTranslator.CONTINUING_EDUCATION_TYPES


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
    def matches_criteria(
        cls,
        training_type: TrainingType,
        sigle: str,
        proposition: 'PropositionGenerale',
        **kwargs,
    ) -> bool:
        """Candidat déjà inscrit l'année N à un autre établissement CF
        (informatiquement : a répondu "oui" à la question sur la modif)"""
        return bool(
            isinstance(proposition, PropositionGenerale)
            and training_type == TrainingType.BACHELOR
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
    def matches_criteria(
        cls,
        training_type: TrainingType,
        sigle: str,
        proposition: 'PropositionGenerale',
        **kwargs,
    ) -> bool:
        """Candidat déjà inscrit l'année N à un autre établissement CF
        (informatiquement : a répondu ""oui"" à la question sur la réori.)"""
        return bool(
            isinstance(proposition, PropositionGenerale)
            and training_type == TrainingType.BACHELOR
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
        training_type: TrainingType,
        proposition: PropositionGenerale,
        **kwargs,
    ) -> bool:
        """Candidat est en Double diplôme, Erasmus mundus, BoursierI
        (informatiquement : a coché oui pour une des 3 questions)"""
        return (
            isinstance(proposition, PropositionGenerale)
            # 2e cycle
            and training_type.name in SECOND_CYCLE_TYPES
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
            isinstance(proposition, PropositionGenerale)
            and hors_ue_plus_5
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
        changements_etablissement: Dict[int, bool],
        sigle: str,
        proposition: 'PropositionGenerale',
        **kwargs,
    ) -> bool:
        """Candidat inscrit à un autre établissement Belge en N-1
        (informatiquement : curriculum / en N-1 supérieur belge non-diplômé*)"""
        if not isinstance(proposition, PropositionGenerale):
            return False
        if residential_address is None:
            raise AdresseDomicileLegalNonCompleteeException()
        return (
            any(belgian_diploma in access_diplomas for belgian_diploma in DIPLOMES_ACCES_BELGE)
            and residential_address.pays == BE_ISO_CODE
            and changements_etablissement.get(annee_academique, False)
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
            isinstance(proposition, PropositionGenerale)
            and ue_plus_5
            and any(belgian_diploma in access_diplomas for belgian_diploma in DIPLOMES_ACCES_BELGE)
            and not est_formation_contingentee_et_non_resident(sigle, proposition)
        )


class AdmissionPoolUe5NonBelgianCalendar(PoolCalendar):
    event_reference = AcademicCalendarTypes.ADMISSION_POOL_UE5_NON_BELGIAN.name
    cutover_date = Date(jour=1, mois=9, annee=-1)

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
            isinstance(proposition, PropositionGenerale)
            and ue_plus_5
            and bool(access_diplomas)
            and not any(belgian_diploma in access_diplomas for belgian_diploma in DIPLOMES_ACCES_BELGE)
            and not est_formation_contingentee_et_non_resident(sigle, proposition)
        )


class AdmissionPoolHue5BelgiumResidencyCalendar(PoolCalendar):
    event_reference = AcademicCalendarTypes.ADMISSION_POOL_HUE5_BELGIUM_RESIDENCY.name
    cutover_date = Date(jour=1, mois=9, annee=-1)

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
        if not isinstance(proposition, PropositionGenerale):
            return False
        if residential_address is None:  # pragma: no cover
            raise AdresseDomicileLegalNonCompleteeException()
        return (
            not ue_plus_5
            and residential_address.pays == BE_ISO_CODE
            and not est_formation_contingentee_et_non_resident(sigle, proposition)
        )


class AdmissionPoolHue5ForeignResidencyCalendar(PoolCalendar):
    event_reference = AcademicCalendarTypes.ADMISSION_POOL_HUE5_FOREIGN_RESIDENCY.name
    cutover_date = Date(jour=1, mois=5, annee=-1)
    end_date = Date(jour=31, mois=3, annee=0)

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
        if not isinstance(proposition, PropositionGenerale):
            return False
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
        return isinstance(proposition, PropositionGenerale) and est_formation_contingentee_et_non_resident(
            sigle,
            proposition,
        )
