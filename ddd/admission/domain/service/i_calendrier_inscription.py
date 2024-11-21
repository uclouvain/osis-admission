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
import logging
from pprint import pformat
from typing import List, Optional, Tuple, Union

import attr

from admission.calendar.admission_calendar import *
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    IdentificationNonCompleteeException,
)
from admission.ddd.admission.domain.model.formation import FormationIdentity
from admission.ddd.admission.domain.service.i_formation_translator import IFormationTranslator
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.i_titres_acces import Titres
from admission.ddd.admission.domain.validator.exceptions import (
    AucunPoolCorrespondantException,
    FormationNonTrouveeException,
    ModificationInscriptionExterneNonConfirmeeException,
    PoolNonResidentContingenteNonOuvertException,
    PoolOuAnneeDifferentException,
    ReorientationInscriptionExterneNonConfirmeeException,
    ResidenceAuSensDuDecretNonRenseigneeException,
    ResidenceAuSensDuDecretNonDisponiblePourInscriptionException,
)
from admission.ddd.admission.dtos import IdentificationDTO
from admission.ddd.admission.dtos.conditions import InfosDetermineesDTO
from admission.ddd.admission.enums import TypeSituationAssimilation
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.dtos import PropositionDTO
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from osis_common.ddd import interface

logger = logging.getLogger(__name__)


class ICalendrierInscription(interface.DomainService):
    pools = [
        DoctorateAdmissionCalendar(),
        ContinuingEducationAdmissionCalendar(),
        AdmissionPoolExternalEnrollmentChangeCalendar(),
        AdmissionPoolVipCalendar(),
        AdmissionPoolHueUclPathwayChangeCalendar(),
        AdmissionPoolInstituteChangeCalendar(),
        AdmissionPoolUe5BelgianCalendar(),
        AdmissionPoolUe5NonBelgianCalendar(),
        AdmissionPoolHue5BelgiumResidencyCalendar(),
        AdmissionPoolHue5ForeignResidencyCalendar(),
        AdmissionPoolNonResidentQuotaCalendar(),
    ]
    priority_pools = [
        AdmissionPoolExternalReorientationCalendar(),
    ]
    all_pools = priority_pools + pools

    # Les inscriptions pour une formation contingentée pour un candidat non résident au sens du décret via osis
    # sont interdites pour le moment
    INTERDIRE_INSCRIPTION_ETUDES_CONTINGENTES_POUR_NON_RESIDENT = True

    @classmethod
    def determiner_annee_academique_et_pot(
        cls,
        formation_id: 'FormationIdentity',
        matricule_candidat: str,
        titres_acces: 'Titres',
        type_formation: 'TrainingType',
        profil_candidat_translator: 'IProfilCandidatTranslator',
        proposition: Optional['Proposition'] = None,
    ) -> 'InfosDetermineesDTO':

        pool_ouverts = cls.get_pool_ouverts()
        cls.verifier_residence_au_sens_du_decret(formation_id.sigle, proposition)
        cls.verifier_reorientation_renseignee_si_eligible(type_formation, formation_id, proposition, pool_ouverts)
        cls.verifier_modification_renseignee_si_eligible(type_formation, formation_id, proposition, pool_ouverts)
        cls.verifier_formation_contingentee_ouvert(formation_id.sigle, proposition, formation_id.annee, pool_ouverts)

        identification = profil_candidat_translator.get_identification(matricule_candidat)
        residential_address = profil_candidat_translator.get_coordonnees(matricule_candidat).domicile_legal
        if identification.pays_nationalite is None:
            raise IdentificationNonCompleteeException()
        situation_assimilation = (
            proposition
            and getattr(proposition, 'comptabilite', None)
            and getattr(proposition.comptabilite, 'type_situation_assimilation', None)
        )
        ue_plus_5 = cls.est_ue_plus_5(identification, situation_assimilation)
        annees_prioritaires, annees = cls.get_annees_academiques_pour_calcul(type_formation=type_formation)
        changements_etablissement = profil_candidat_translator.get_changements_etablissement(matricule_candidat, annees)

        log_messages = [
            f"""
--------- Pool determination ---------
annees_calcul={annees},
formation_id={formation_id},
ue_plus_5={ue_plus_5},
access_diplomas={pformat(titres_acces.get_valid_conditions())},
training_type={type_formation},
residential_address={residential_address and pformat(attr.asdict(residential_address))},
annee_derniere_inscription_ucl={identification.annee_derniere_inscription_ucl},
matricule_candidat={matricule_candidat},
changements_etablissement={changements_etablissement},
proposition={('Proposition(' + pformat(attr.asdict(proposition)) + ')') if proposition else 'None'},
        """,
        ]
        current_kwargs = dict(
            logs=log_messages,
            pool_ouverts=pool_ouverts,
            sigle=formation_id.sigle,
            ue_plus_5=ue_plus_5,
            access_diplomas=titres_acces.get_valid_conditions(),
            training_type=type_formation,
            residential_address=residential_address,
            annee_derniere_inscription_ucl=identification.annee_derniere_inscription_ucl,
            matricule_candidat=matricule_candidat,
            changements_etablissement=changements_etablissement,
            proposition=proposition,
        )

        for annee in annees_prioritaires:
            pool = cls.determiner_pool_pour_annee_academique(
                pools=cls.priority_pools,
                annee_academique=annee,
                **current_kwargs,
            )
            if pool:
                logger.debug('\n'.join(log_messages))
                return InfosDetermineesDTO(annee, pool)
            log_messages.append("")

        for annee in annees:
            pool = cls.determiner_pool_pour_annee_academique(
                pools=cls.pools,
                annee_academique=annee,
                **current_kwargs,
            )
            if pool:
                logger.debug('\n'.join(log_messages))
                return InfosDetermineesDTO(annee, pool)
            log_messages.append("")
        else:  # pragma: no cover
            logger.debug('\n'.join(log_messages))
            raise AucunPoolCorrespondantException()

    @classmethod
    def determiner_pool_pour_annee_academique(
        cls,
        logs: List[str],
        pool_ouverts: List[Tuple[str, int]],
        pools: List[PoolCalendar],
        **kwargs,
    ) -> Optional['AcademicCalendarTypes']:
        for pool in pools:
            annee = kwargs['annee_academique']
            logs.append(
                f"{str(AcademicCalendarTypes.get_value(pool.event_reference)):<70} {annee}"
                f" pool_est_ouvert: {(pool.event_reference, annee) in pool_ouverts} \t"
                f"matches_criteria: {pool.matches_criteria(**kwargs)}"
            )
            if (pool.event_reference, annee) in pool_ouverts and pool.matches_criteria(**kwargs):
                return AcademicCalendarTypes[pool.event_reference]
        return None  # pragma: no cover

    @classmethod
    def verifier(
        cls,
        formation_id: 'FormationIdentity',
        proposition: 'Proposition',
        matricule_candidat: str,
        titres_acces: 'Titres',
        type_formation: 'TrainingType',
        profil_candidat_translator: 'IProfilCandidatTranslator',
        formation_translator: 'IFormationTranslator',
        annee_soumise: int = None,
        pool_soumis: 'AcademicCalendarTypes' = None,
    ) -> None:
        determination = cls.determiner_annee_academique_et_pot(
            formation_id,
            matricule_candidat,
            titres_acces,
            type_formation,
            profil_candidat_translator,
            proposition,
        )
        # Si le candidat s'inscrit pour une acad future, mais que la formation n'existe pas dans cette acad
        if determination.annee != formation_id.annee:
            if not formation_translator.verifier_existence(formation_id.sigle, determination.annee):
                raise FormationNonTrouveeException(formation_id.sigle, determination.annee)

        # Vérifier la concordance entre l'année/pool soumis et ceux calculés
        if (
            annee_soumise is not None
            and pool_soumis is not None
            and (determination.annee != annee_soumise or determination.pool != pool_soumis)
        ):
            raise PoolOuAnneeDifferentException(determination.annee, determination.pool, annee_soumise, pool_soumis)

    @classmethod
    def verifier_reorientation_renseignee_si_eligible(
        cls,
        program: 'TrainingType',
        formation_id: 'FormationIdentity',
        proposition: Optional['Proposition'],
        pool_ouverts: List[Tuple[str, int]],
    ):
        """Si le candidat pourrait tomber dans le pool de reorientation et n'a pas répondu à la question"""
        if cls.eligible_a_la_reorientation(program.name, formation_id.sigle, proposition, pool_ouverts) and (
            proposition
            and (
                proposition.est_reorientation_inscription_externe is None
                or proposition.est_reorientation_inscription_externe
                and not (proposition.attestation_inscription_reguliere and proposition.formulaire_reorientation)
            )
        ):
            raise ReorientationInscriptionExterneNonConfirmeeException()

    @classmethod
    def verifier_modification_renseignee_si_eligible(
        cls,
        program: 'TrainingType',
        formation_id: 'FormationIdentity',
        proposition: Optional['Proposition'],
        pool_ouverts: List[Tuple[str, int]],
    ):
        """Si le candidat pourrait tomber dans le pool de modification et n'a pas répondu à la question"""
        if cls.eligible_a_la_modification(program.name, formation_id.sigle, proposition, pool_ouverts) and (
            proposition
            and (
                proposition.est_modification_inscription_externe is None
                or proposition.est_modification_inscription_externe
                and not proposition.formulaire_modification_inscription
            )
        ):
            raise ModificationInscriptionExterneNonConfirmeeException()

    @classmethod
    def verifier_residence_au_sens_du_decret(cls, sigle: str, proposition: Optional['Proposition']):
        """Si le candidat s'inscrit dans une formation contingentée et n'a pas répondu à la question
        sur la résidence au sens du décret."""
        if cls.inscrit_formation_contingentee(sigle) and proposition:
            if proposition.est_non_resident_au_sens_decret is None:
                raise ResidenceAuSensDuDecretNonRenseigneeException()
            elif (
                cls.INTERDIRE_INSCRIPTION_ETUDES_CONTINGENTES_POUR_NON_RESIDENT
                and proposition.est_non_resident_au_sens_decret is True
            ):
                raise ResidenceAuSensDuDecretNonDisponiblePourInscriptionException()

    @classmethod
    def verifier_formation_contingentee_ouvert(
        cls,
        sigle: str,
        proposition: Optional['Proposition'],
        annee: int,
        pool_ouverts: List[Tuple[str, int]],
    ):
        """Si le candidat s'inscrit dans une formation contingentée et ne tombe pas dans la bonne période."""
        if (
            est_formation_contingentee_et_non_resident(sigle, proposition)
            # hors periode
            and (AdmissionPoolNonResidentQuotaCalendar.event_reference, annee) not in pool_ouverts
        ):
            raise PoolNonResidentContingenteNonOuvertException()

    @classmethod
    def get_pool_ouverts(cls) -> List[Tuple[str, int]]:
        raise NotImplementedError

    @classmethod
    def get_annees_academiques_pour_calcul(cls, type_formation: TrainingType) -> Tuple[List[int], List[int]]:
        """
        Retourne un tuple contenant les deux listes des années académiques utilisées dans le calcul des pots, la
        première pour les pots prioritaires et la seconde pour les autres pots.
        """
        raise NotImplementedError

    @classmethod
    def est_ue_plus_5(
        cls,
        identification: 'IdentificationDTO',
        situation_assimilation: TypeSituationAssimilation = None,
    ) -> bool:
        raise NotImplementedError

    @classmethod
    def eligible_a_la_reorientation(
        cls,
        program: str,
        sigle: str,
        proposition: Optional[Union['Proposition', 'PropositionDTO']],
        pool_ouverts: List[Tuple[str, int]],
    ):
        """Retourne si le candidat est éligible à la réorientation"""
        return (
            program == TrainingType.BACHELOR.name
            and not est_formation_contingentee_et_non_resident(sigle, proposition)
            and AdmissionPoolExternalReorientationCalendar.event_reference in [pool for (pool, annee) in pool_ouverts]
        )

    @classmethod
    def eligible_a_la_modification(
        cls,
        program: str,
        sigle: str,
        proposition: Optional[Union['Proposition', 'PropositionDTO']],
        pool_ouverts: List[Tuple[str, int]],
    ):
        """Retourne si le candidat est éligible à la modification"""
        return (
            program == TrainingType.BACHELOR.name
            and not est_formation_contingentee_et_non_resident(sigle, proposition)
            and AdmissionPoolExternalEnrollmentChangeCalendar.event_reference
            in [pool for (pool, annee) in pool_ouverts]
        )

    @classmethod
    def inscrit_formation_contingentee(cls, sigle: str):
        """Retourne si le candidat s'inscrit dans une formation contingentée"""
        return sigle in SIGLES_WITH_QUOTA
