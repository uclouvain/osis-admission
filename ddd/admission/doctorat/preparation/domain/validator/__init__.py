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

from ._should_comptabilite_etre_completee import ShouldAffiliationsEtreCompletees
from ._should_cotutelle_etre_completee import ShouldCotutelleEtreComplete
from ._should_curriculum_etre_complete import (
    ShouldCurriculumFichierEtreSpecifie,
)
from ._should_domaine_dependre_doctorat_realise import ShouldDomaineDependreDoctoratRealise
from ._should_groupe_de_supervision_a_approuve import (
    ShouldDemandeSignatureLancee,
    ShouldMembresCAOntApprouve,
    ShouldPromoteursOntApprouve,
)
from ._should_groupe_de_supervision_avoir_au_moins_un_membre_CA import ShouldGroupeDeSupervisionAvoirAuMoinsUnMembreCA
from ._should_groupe_de_supervision_avoir_un_promoteur_de_reference import (
    ShouldGroupeDeSupervisionAvoirUnPromoteurDeReference,
)
from ._should_groupe_de_supervision_non_complet_pour_membres_CA import ShouldGroupeDeSupervisionNonCompletPourMembresCA
from ._should_groupe_de_supervision_non_complet_pour_promoteurs import ShouldGroupeDeSupervisionNonCompletPourPromoteurs
from ._should_institution_dependre_doctorat_realise import ShouldInstitutionDependreDoctoratRealise
from ._should_justification_donnee_si_preadmission import ShouldJustificationDonneeSiPreadmission
from ._should_langues_connues_etre_completees import ShouldLanguesConnuesRequisesEtreSpecifiees
from ._should_membre_CA_etre_dans_groupe_de_supervision import ShouldMembreCAEtreDansGroupeDeSupervision
from ._should_premier_promoteur_renseigner_institut_these import ShouldPromoteurReferenceRenseignerInstitutThese
from ._should_projet_etre_complet import ShouldProjetEtreComplet
from ._should_promoteur_etre_dans_groupe_de_supervision import ShouldPromoteurEtreDansGroupeDeSupervision
from ._should_signataire_etre_dans_groupe_de_supervision import ShouldSignataireEtreDansGroupeDeSupervision
from ._should_signataire_etre_invite import ShouldSignataireEtreInvite
from ._should_signataire_pas_invite import ShouldSignatairePasDejaInvite
from ._should_type_contrat_travail_dependre_type_financement import ShouldTypeContratTravailDependreTypeFinancement
from ._should_membre_etre_interne_ou_externe import ShouldMembreEtreInterneOuExterne
from ._should_signatures_pas_etre_envoyees import ShouldSignaturesPasEtreEnvoyees

__all__ = [
    "ShouldInstitutionDependreDoctoratRealise",
    "ShouldDomaineDependreDoctoratRealise",
    "ShouldJustificationDonneeSiPreadmission",
    "ShouldMembreCAEtreDansGroupeDeSupervision",
    "ShouldPromoteurEtreDansGroupeDeSupervision",
    "ShouldSignataireEtreDansGroupeDeSupervision",
    "ShouldSignataireEtreInvite",
    "ShouldSignatairePasDejaInvite",
    "ShouldTypeContratTravailDependreTypeFinancement",
    "ShouldGroupeDeSupervisionNonCompletPourMembresCA",
    "ShouldGroupeDeSupervisionNonCompletPourPromoteurs",
    "ShouldCotutelleEtreComplete",
    "ShouldProjetEtreComplet",
    "ShouldGroupeDeSupervisionAvoirAuMoinsUnMembreCA",
    "ShouldLanguesConnuesRequisesEtreSpecifiees",
    "ShouldCurriculumFichierEtreSpecifie",
    "ShouldDemandeSignatureLancee",
    "ShouldPromoteursOntApprouve",
    "ShouldMembresCAOntApprouve",
    "ShouldPromoteurReferenceRenseignerInstitutThese",
    "ShouldGroupeDeSupervisionAvoirUnPromoteurDeReference",
    "ShouldAffiliationsEtreCompletees",
    "ShouldMembreEtreInterneOuExterne",
    "ShouldSignaturesPasEtreEnvoyees",
]
