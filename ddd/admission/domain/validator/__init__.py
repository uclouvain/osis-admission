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
from ._should_comptabilite_etre_completee import (
    ShouldAbsenceDeDetteEtreCompletee,
    ShouldAssimilationEtreCompletee,
    ShouldAutreFormatCarteBancaireRemboursementEtreCompletee,
    ShouldIBANCarteBancaireRemboursementEtreCompletee,
    ShouldTypeCompteBancaireRemboursementEtreComplete,
)
from ._should_coordonnees_candidat_etre_completees import (
    ShouldAdresseCorrespondanceEtreCompleteeSiSpecifiee,
    ShouldAdresseDomicileLegalCandidatEtreCompletee,
    ShouldAdresseEmailPriveeEtreCompletee,
    ShouldCoordonneesCandidatEtreCompletees,
)
from ._should_curriculum_etre_complete import (
    ShouldAnneesCVRequisesCompletees,
    ShouldExperiencesAcademiquesEtreCompletees,
    ShouldExperiencesAcademiquesEtreCompleteesApresSoumission,
)
from ._should_documents_etre_completes import ShouldCompleterTousLesDocumentsReclames
from ._should_identification_candidat_etre_completee import (
    ShouldCandidatAuthentiquerIdentite,
    ShouldCandidatAuthentiquerPasseport,
    ShouldCandidatBelgeSpecifierNumeroRegistreNationalBelge,
    ShouldCandidatSpecifierDateOuAnneeNaissance,
    ShouldCandidatSpecifierNOMASiDejaInscrit,
    ShouldCandidatSpecifierNomOuPrenom,
    ShouldCandidatSpecifierNumeroIdentite,
    ShouldSignaletiqueCandidatEtreCompletee,
)

__all__ = [
    "ShouldSignaletiqueCandidatEtreCompletee",
    "ShouldCandidatSpecifierNumeroIdentite",
    "ShouldCandidatBelgeSpecifierNumeroRegistreNationalBelge",
    "ShouldCandidatSpecifierDateOuAnneeNaissance",
    "ShouldCandidatSpecifierNOMASiDejaInscrit",
    "ShouldCandidatSpecifierNomOuPrenom",
    "ShouldCandidatAuthentiquerIdentite",
    "ShouldCandidatAuthentiquerPasseport",
    "ShouldCompleterTousLesDocumentsReclames",
    "ShouldAdresseDomicileLegalCandidatEtreCompletee",
    "ShouldAdresseCorrespondanceEtreCompleteeSiSpecifiee",
    "ShouldAnneesCVRequisesCompletees",
    "ShouldAdresseEmailPriveeEtreCompletee",
    "ShouldAssimilationEtreCompletee",
    "ShouldAbsenceDeDetteEtreCompletee",
    "ShouldAutreFormatCarteBancaireRemboursementEtreCompletee",
    "ShouldIBANCarteBancaireRemboursementEtreCompletee",
    "ShouldExperiencesAcademiquesEtreCompletees",
    "ShouldExperiencesAcademiquesEtreCompleteesApresSoumission",
    "ShouldTypeCompteBancaireRemboursementEtreComplete",
    "ShouldCoordonneesCandidatEtreCompletees",
]
