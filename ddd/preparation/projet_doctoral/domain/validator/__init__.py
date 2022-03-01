from ._should_coordonnees_candidat_etre_completees import (
    ShouldAdresseDomicileLegalCandidatEtreCompletee,
    ShouldAdresseCorrespondanceEtreCompleteeSiSpecifiee,
)
from ._should_cotutelle_etre_completee import ShouldCotutelleEtreComplete
from ._should_curriculum_etre_complete import ShouldAnneesCVRequisesCompletees, ShouldCurriculumFichierEtreSpecifie
from ._should_groupe_de_supervision_a_approuve import (
    ShouldDemandeSignatureLancee,
    ShouldMembresCAOntApprouve,
    ShouldPromoteursOntApprouve,
)
from ._should_langues_connues_etre_completees import ShouldLanguesConnuesRequisesEtreSpecifiees
from ._should_projet_etre_complet import ShouldProjetEtreComplet
from ._should_groupe_de_supervision_avoir_au_moins_un_membre_CA import ShouldGroupeDeSupervisionAvoirAuMoinsUnMembreCA
from ._should_groupe_de_supervision_non_complet_pour_membres_CA import ShouldGroupeDeSupervisionNonCompletPourMembresCA
from ._should_groupe_de_supervision_non_complet_pour_promoteurs import ShouldGroupeDeSupervisionNonCompletPourPromoteurs
from ._should_institution_dependre_doctorat_realise import ShouldInstitutionDependreDoctoratRealise
from ._should_justification_donnee_si_preadmission import ShouldJustificationDonneeSiPreadmission
from ._should_membre_CA_etre_dans_groupe_de_supervision import ShouldMembreCAEtreDansGroupeDeSupervision
from ._should_membre_CA_pas_deja_present_dans_groupe_de_supervision import (
    ShouldMembreCAPasDejaPresentDansGroupeDeSupervision,
)
from ._should_promoteur_etre_dans_groupe_de_supervision import ShouldPromoteurEtreDansGroupeDeSupervision
from ._should_promoteur_pas_deja_present_dans_groupe_de_supervision import (
    ShouldPromoteurPasDejaPresentDansGroupeDeSupervision,
)
from ._should_signataire_etre_dans_groupe_de_supervision import ShouldSignataireEtreDansGroupeDeSupervision
from ._should_signataire_etre_invite import ShouldSignataireEtreInvite
from ._should_signataire_pas_invite import ShouldSignatairePasDejaInvite
from ._should_type_contrat_travail_dependre_type_financement import ShouldTypeContratTravailDependreTypeFinancement
from ._should_identification_candidat_etre_completee import ShouldSignaletiqueCandidatEtreCompletee
from ._should_identification_candidat_etre_completee import (
    ShouldCandidatSpecifierNumeroIdentite,
    ShouldCandidatBelgeSpecifierNumeroRegistreNationalBelge,
    ShouldCandidatSpecifierDateOuAnneeNaissance,
    ShouldCandidatAuthentiquerIdentite,
    ShouldCandidatAuthentiquerPasseport,
)
from ._should_premier_promoteur_renseigner_institut_these import ShouldPremierPromoteurRenseignerInstitutThese

__all__ = [
    "ShouldInstitutionDependreDoctoratRealise",
    "ShouldJustificationDonneeSiPreadmission",
    "ShouldMembreCAEtreDansGroupeDeSupervision",
    "ShouldMembreCAPasDejaPresentDansGroupeDeSupervision",
    "ShouldPromoteurEtreDansGroupeDeSupervision",
    "ShouldPromoteurPasDejaPresentDansGroupeDeSupervision",
    "ShouldSignataireEtreDansGroupeDeSupervision",
    "ShouldSignataireEtreInvite",
    "ShouldSignatairePasDejaInvite",
    "ShouldTypeContratTravailDependreTypeFinancement",
    "ShouldGroupeDeSupervisionNonCompletPourMembresCA",
    "ShouldGroupeDeSupervisionNonCompletPourPromoteurs",
    "ShouldCotutelleEtreComplete",
    "ShouldProjetEtreComplet",
    "ShouldGroupeDeSupervisionAvoirAuMoinsUnMembreCA",
    "ShouldSignaletiqueCandidatEtreCompletee",
    "ShouldCandidatSpecifierNumeroIdentite",
    "ShouldCandidatBelgeSpecifierNumeroRegistreNationalBelge",
    "ShouldCandidatSpecifierDateOuAnneeNaissance",
    "ShouldCandidatAuthentiquerIdentite",
    "ShouldCandidatAuthentiquerPasseport",
    "ShouldAdresseDomicileLegalCandidatEtreCompletee",
    "ShouldAdresseCorrespondanceEtreCompleteeSiSpecifiee",
    "ShouldLanguesConnuesRequisesEtreSpecifiees",
    "ShouldAnneesCVRequisesCompletees",
    "ShouldCurriculumFichierEtreSpecifie",
    "ShouldDemandeSignatureLancee",
    "ShouldPromoteursOntApprouve",
    "ShouldMembresCAOntApprouve",
    "ShouldPremierPromoteurRenseignerInstitutThese",
]
