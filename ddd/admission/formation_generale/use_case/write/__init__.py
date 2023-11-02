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
from .initier_proposition_service import initier_proposition
from .modifier_choix_formation_service import modifier_choix_formation
from .supprimer_proposition_service import supprimer_proposition
from .soumettre_proposition_service import soumettre_proposition
from .completer_curriculum_service import completer_curriculum
from .completer_comptabilite_proposition_service import completer_comptabilite_proposition
from .completer_emplacements_documents_par_candidat_service import completer_emplacements_documents_par_candidat
from .completer_questions_specifiques_service import completer_questions_specifiques
from .completer_questions_specifiques_par_gestionnaire_service import completer_questions_specifiques_par_gestionnaire
from .envoyer_rappel_paiement_service import envoyer_rappel_paiement
from .payer_frais_dossier_proposition_suite_demande_service import payer_frais_dossier_proposition_suite_demande
from .payer_frais_dossier_proposition_suite_soumission_service import payer_frais_dossier_proposition_suite_soumission
from .specifier_paiement_necessaire_service import specifier_paiement_necessaire
from .specifier_paiement_plus_necessaire_service import specifier_paiement_plus_necessaire
from .recalculer_emplacements_documents_non_libres_proposition_service import (
    recalculer_emplacements_documents_non_libres_proposition,
)
from .reclamer_documents_au_candidat_par_fac_service import reclamer_documents_au_candidat_par_fac
from .reclamer_documents_au_candidat_par_sic_service import reclamer_documents_au_candidat_par_sic
from .envoyer_proposition_a_fac_lors_de_la_decision_facultaire_service import (
    envoyer_proposition_a_fac_lors_de_la_decision_facultaire,
)
from .refuser_proposition_par_faculte_service import refuser_proposition_par_faculte
from .refuser_proposition_par_faculte_avec_nouveaux_motifs_service import (
    refuser_proposition_par_faculte_avec_nouveaux_motifs,
)
from .specifier_motifs_refus_proposition_par_faculte_service import specifier_motifs_refus_proposition_par_faculte
from .specifier_informations_acceptation_proposition_par_faculte_service import (
    specifier_informations_acceptation_proposition_par_faculte,
)
from .approuver_proposition_par_faculte_service import approuver_proposition_par_faculte
from .approuver_proposition_par_faculte_avec_nouvelles_informations_service import (
    approuver_proposition_par_faculte_avec_nouvelles_informations,
)
from .modifier_checklist_choix_formation_service import modifier_checklist_choix_formation
from .specifier_paiement_va_etre_ouvert_par_candidat_service import specifier_paiement_va_etre_ouvert_par_candidat
from .modifier_choix_formation_par_gestionnaire_service import modifier_choix_formation_par_gestionnaire
from .envoyer_proposition_au_sic_lors_de_la_decision_facultaire_service import (
    envoyer_proposition_au_sic_lors_de_la_decision_facultaire,
)
