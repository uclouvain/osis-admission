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
from .annuler_reclamation_documents_au_candidat_service import annuler_reclamation_documents_au_candidat
from .approuver_admission_par_sic_service import approuver_admission_par_sic
from .approuver_inscription_par_sic_service import approuver_inscription_par_sic
from .approuver_proposition_par_faculte_service import approuver_proposition_par_faculte
from .approuver_proposition_par_pdf_service import approuver_proposition_par_pdf
from .approuver_proposition_service import approuver_proposition
from .completer_comptabilite_proposition_service import completer_comptabilite_proposition
from .completer_curriculum_service import completer_curriculum
from .completer_emplacements_documents_par_candidat_service import completer_emplacements_documents_par_candidat
from .completer_proposition_service import completer_proposition
from .definir_cotutelle_service import definir_cotutelle
from .demander_signatures_service import demander_signatures
from .designer_promoteur_reference_service import designer_promoteur_reference
from .envoyer_email_approbation_inscription_au_candidat_service import envoyer_email_approbation_inscription_au_candidat
from .envoyer_message_au_candidat_service import envoyer_message_au_candidat
from .envoyer_proposition_a_fac_lors_de_la_decision_facultaire_service import (
    envoyer_proposition_a_fac_lors_de_la_decision_facultaire,
)
from .envoyer_proposition_au_sic_lors_de_la_decision_facultaire_service import (
    envoyer_proposition_au_sic_lors_de_la_decision_facultaire,
)
from .identifier_membre_CA_service import identifier_membre_ca
from .identifier_promoteur_service import identifier_promoteur
from .initier_proposition_service import initier_proposition
from .modifier_authentification_experience_parcours_anterieur_service import (
    modifier_authentification_experience_parcours_anterieur,
)
from .modifier_checklist_choix_formation_service import modifier_checklist_choix_formation
from .modifier_choix_formation_par_gestionnaire_service import modifier_choix_formation_par_gestionnaire
from .modifier_membre_supervision_externe_service import modifier_membre_supervision_externe
from .modifier_statut_checklist_experience_parcours_anterieur_service import (
    modifier_statut_checklist_experience_parcours_anterieur,
)
from .modifier_statut_checklist_parcours_anterieur_service import modifier_statut_checklist_parcours_anterieur
from .modifier_type_admission_service import modifier_type_admission
from .notifier_candidat_derogation_financabilite_service import notifier_candidat_derogation_financabilite
from .recalculer_emplacements_documents_non_libres_proposition_service import (
    recalculer_emplacements_documents_non_libres_proposition,
)
from .reclamer_documents_au_candidat_service import reclamer_documents_au_candidat
from .refuser_admission_par_sic_service import refuser_admission_par_sic
from .refuser_inscription_par_sic_service import refuser_inscription_par_sic
from .refuser_proposition_par_faculte_service import refuser_proposition_par_faculte
from .refuser_proposition_service import refuser_proposition
from .renvoyer_invitation_signature_externe_service import renvoyer_invitation_signature_externe
from .retyper_document_service import retyper_document
from .soumettre_proposition_service import soumettre_proposition
from .specifier_besoin_de_derogation_service import specifier_besoin_de_derogation
from .specifier_condition_acces_proposition_service import specifier_condition_acces_proposition
from .specifier_derogation_financabilite_service import specifier_derogation_financabilite
from .specifier_equivalence_titre_acces_etranger_proposition_service import (
    specifier_equivalence_titre_acces_etranger_proposition,
)
from .specifier_financabilite_non_concernee_service import specifier_financabilite_non_concernee
from .specifier_financabilite_regle_service import specifier_financabilite_regle
from .specifier_financabilite_resultat_calcul_service import specifier_financabilite_resultat_calcul
from .specifier_informations_acceptation_inscription_par_sic_service import (
    specifier_informations_acceptation_inscription_par_sic,
)
from .specifier_informations_acceptation_proposition_par_faculte_service import (
    specifier_informations_acceptation_proposition_par_faculte,
)
from .specifier_informations_acceptation_proposition_par_sic_service import (
    specifier_informations_acceptation_proposition_par_sic,
)
from .specifier_motifs_refus_proposition_par_faculte_service import specifier_motifs_refus_proposition_par_faculte
from .specifier_motifs_refus_proposition_par_sic_service import specifier_motifs_refus_proposition_par_sic
from .supprimer_membre_CA_service import supprimer_membre_CA
from .supprimer_promoteur_service import supprimer_promoteur
from .supprimer_proposition_service import supprimer_proposition
