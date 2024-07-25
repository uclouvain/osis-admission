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
from .approuver_proposition_par_pdf_service import approuver_proposition_par_pdf
from .approuver_proposition_service import approuver_proposition
from .completer_comptabilite_proposition_service import completer_comptabilite_proposition
from .completer_curriculum_service import completer_curriculum
from .completer_emplacements_documents_par_candidat_service import completer_emplacements_documents_par_candidat
from .completer_proposition_service import completer_proposition
from .definir_cotutelle_service import definir_cotutelle
from .demander_signatures_service import demander_signatures
from .designer_promoteur_reference_service import designer_promoteur_reference
from .identifier_membre_CA_service import identifier_membre_ca
from .identifier_promoteur_service import identifier_promoteur
from .initier_proposition_service import initier_proposition
from .modifier_choix_formation_par_gestionnaire_service import modifier_choix_formation_par_gestionnaire
from .modifier_membre_supervision_externe_service import modifier_membre_supervision_externe
from .modifier_type_admission_service import modifier_type_admission
from .recalculer_emplacements_documents_non_libres_proposition_service import (
    recalculer_emplacements_documents_non_libres_proposition,
)
from .reclamer_documents_au_candidat_service import reclamer_documents_au_candidat
from .refuser_proposition_service import refuser_proposition
from .renvoyer_invitation_signature_externe_service import renvoyer_invitation_signature_externe
from .retyper_document_service import retyper_document
from .soumettre_proposition_service import soumettre_proposition
from .supprimer_membre_CA_service import supprimer_membre_CA
from .supprimer_promoteur_service import supprimer_promoteur
from .supprimer_proposition_service import supprimer_proposition
