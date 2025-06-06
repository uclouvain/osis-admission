# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from ._should_comptabilite_etre_completee import (
    ShouldAffiliationsEtreCompletees,
    ShouldReductionDesDroitsInscriptionEtreCompletee,
)
from ._should_curriculum_etre_complete import (
    ShouldCurriculumFichierEtreSpecifie,
    ShouldEquivalenceEtreSpecifiee,
)
from ._should_etudes_secondaires_etre_completees import (
    ShouldAlternativeSecondairesEtreCompletee,
    ShouldDiplomeBelgesEtudesSecondairesEtreComplete,
    ShouldDiplomeEtrangerEtudesSecondairesEtreComplete,
    ShouldSpecifieSiDiplomeEtudesSecondaires,
    ShouldSpecifieSiDiplomeEtudesSecondairesPourBachelier,
)
from ._should_informations_checklist_etre_completees import (
    ShouldChecklistEtreDansEtatCorrectPourApprouverInscription,
    ShouldComplementsFormationEtreVidesSiPasDeComplementsFormation,
    ShouldConditionAccesEtreSelectionne,
    ShouldDemandeEtreTypeAdmission,
    ShouldDemandeEtreTypeInscription,
    ShouldFacPeutDonnerDecision,
    ShouldFacPeutSoumettreAuSicLorsDeLaDecisionFacultaire,
    ShouldPeutSpecifierInformationsDecisionFacultaire,
    ShouldPropositionEtreInscriptionTardiveAvecConditionAcces,
    ShouldPropositionEtreReorientationExterneAvecConditionAcces,
    ShouldSelectionnerTitreAccesPourEnvoyerASIC,
    ShouldSICPeutSoumettreAFacLorsDeLaDecisionFacultaire,
    ShouldSicPeutSoumettreAuSicLorsDeLaDecisionFacultaire,
    ShouldSpecifierInformationsAcceptationFacultaire,
    ShouldSpecifierInformationsAcceptationFacultaireInscription,
    ShouldSpecifierMotifRefusFacultaire,
    ShouldStatutsChecklistExperiencesEtreValidees,
    ShouldTitreAccesEtreSelectionne,
)
from ._should_informations_complementaires_etre_completes import ShouldVisaEtreComplete
from ._should_informations_onglet_choix_formation_etre_completees import (
    ShouldRenseignerBoursesEtudesSelonFormation,
)
