# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional

import attr

from admission.ddd import REGIMES_LINGUISTIQUES_SANS_TRADUCTION
from admission.ddd.admission.domain.model.formation import Formation
from admission.ddd.admission.formation_generale.domain.model.enums import CHOIX_DIPLOME_OBTENU
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    EtudesSecondairesNonCompleteesException,
    EtudesSecondairesNonCompleteesPourAlternativeException,
    EtudesSecondairesNonCompleteesPourDiplomeBelgeException,
    EtudesSecondairesNonCompleteesPourDiplomeEtrangerException,
)
from base.ddd.utils.business_validator import BusinessValidator
from base.models.enums.got_diploma import GotDiploma
from ddd.logic.shared_kernel.profil.dtos.etudes_secondaires import (
    DiplomeBelgeEtudesSecondairesDTO,
    DiplomeEtrangerEtudesSecondairesDTO,
    AlternativeSecondairesDTO,
)
from osis_profile.models.enums.education import Equivalence, ForeignDiplomaTypes


@attr.dataclass(frozen=True, slots=True)
class ShouldSpecifieSiDiplomeEtudesSecondaires(BusinessValidator):
    diplome_etudes_secondaires: str
    annee_diplome_etudes_secondaires: Optional[int]

    def validate(self, *args, **kwargs):
        if (
            not self.diplome_etudes_secondaires
            or self.diplome_etudes_secondaires in CHOIX_DIPLOME_OBTENU
            and not self.annee_diplome_etudes_secondaires
        ):
            raise EtudesSecondairesNonCompleteesException


@attr.dataclass(frozen=True, slots=True)
class ShouldSpecifieSiDiplomeEtudesSecondairesPourBachelier(BusinessValidator):
    diplome_belge: Optional[DiplomeBelgeEtudesSecondairesDTO]
    diplome_etranger: Optional[DiplomeEtrangerEtudesSecondairesDTO]
    alternative_secondaires: Optional[AlternativeSecondairesDTO]
    diplome_etudes_secondaires: str
    annee_diplome_etudes_secondaires: Optional[int]
    est_potentiel_vae: bool

    def validate(self, *args, **kwargs):
        if (
            not self.diplome_etudes_secondaires
            # doit renseigner les informations relatives à un diplôme
            or self.diplome_etudes_secondaires in CHOIX_DIPLOME_OBTENU
            and (not self.annee_diplome_etudes_secondaires or not (self.diplome_etranger or self.diplome_belge))
            # ou, si pas potentiel vae, doit renseigner les informations relatives à l'alternative aux secondaires
            or self.diplome_etudes_secondaires == GotDiploma.NO.name
            and not self.est_potentiel_vae
            and not self.alternative_secondaires
        ):
            raise EtudesSecondairesNonCompleteesException


@attr.dataclass(frozen=True, slots=True)
class ShouldDiplomeBelgesEtudesSecondairesEtreComplete(BusinessValidator):
    diplome_belge: Optional[DiplomeBelgeEtudesSecondairesDTO]
    diplome_etudes_secondaires: str

    def validate(self, *args, **kwargs):
        if not self.diplome_belge:
            return

        if not self.diplome_belge.diplome:
            raise EtudesSecondairesNonCompleteesPourDiplomeBelgeException


@attr.dataclass(frozen=True, slots=True)
class ShouldDiplomeEtrangerEtudesSecondairesEtreComplete(BusinessValidator):
    diplome_etranger: Optional[DiplomeEtrangerEtudesSecondairesDTO]
    diplome_etudes_secondaires: str
    formation: Formation

    def validate(self, *args, **kwargs):
        if not self.diplome_etranger:
            return

        traductions_requises = self.diplome_etranger.regime_linguistique not in REGIMES_LINGUISTIQUES_SANS_TRADUCTION
        equivalence_requise = self.diplome_etranger.type_diplome == ForeignDiplomaTypes.NATIONAL_BACHELOR.name

        if self.diplome_etranger.pays_membre_ue or self.formation.est_formation_medecine_ou_dentisterie:
            # UE ou MED/DENT
            # Equivalence
            if equivalence_requise and (
                not self.diplome_etranger.equivalence
                or self.diplome_etranger.equivalence == Equivalence.YES.name
                and not self.diplome_etranger.decision_final_equivalence_ue
                or self.diplome_etranger.equivalence == Equivalence.PENDING.name
                and not self.diplome_etranger.preuve_decision_equivalence
            ):
                raise EtudesSecondairesNonCompleteesPourDiplomeEtrangerException
        else:
            # Hors UE non MED/DENT
            if equivalence_requise and not self.diplome_etranger.decision_final_equivalence_hors_ue:
                raise EtudesSecondairesNonCompleteesPourDiplomeEtrangerException

        if not self.diplome_etranger.diplome:
            raise EtudesSecondairesNonCompleteesPourDiplomeEtrangerException

        if not self.diplome_etranger.releve_notes:
            raise EtudesSecondairesNonCompleteesPourDiplomeEtrangerException

        if traductions_requises and not (
            self.diplome_etranger.traduction_releve_notes and self.diplome_etranger.traduction_diplome
        ):
            raise EtudesSecondairesNonCompleteesPourDiplomeEtrangerException


@attr.dataclass(frozen=True, slots=True)
class ShouldAlternativeSecondairesEtreCompletee(BusinessValidator):
    alternative_secondaires: Optional[AlternativeSecondairesDTO]
    diplome_etudes_secondaires: str
    est_potentiel_vae: bool

    def validate(self, *args, **kwargs):
        if not self.alternative_secondaires or self.est_potentiel_vae:
            return

        if not self.alternative_secondaires.examen_admission_premier_cycle:
            raise EtudesSecondairesNonCompleteesPourAlternativeException
