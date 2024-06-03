##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################
from .annuler_proposition_service import annuler_proposition
from .annuler_reclamation_documents_au_candidat_service import annuler_reclamation_documents_au_candidat
from .approuver_par_fac_service import approuver_par_fac
from .cloturer_proposition_service import cloturer_proposition
from .completer_curriculum_service import completer_curriculum
from .completer_emplacements_documents_par_candidat_service import completer_emplacements_documents_par_candidat
from .completer_questions_specifiques_par_gestionnaire_service import completer_questions_specifiques_par_gestionnaire
from .completer_questions_specifiques_service import completer_questions_specifiques
from .initier_proposition_service import initier_proposition
from .mettre_en_attente_service import mettre_en_attente
from .modifier_choix_formation_service import modifier_choix_formation
from .modifier_choix_formation_service_par_gestionnaire import modifier_choix_formation_par_gestionnaire
from .recalculer_emplacements_documents_non_libres_proposition_service import (
    recalculer_emplacements_documents_non_libres_proposition,
)
from .reclamer_documents_au_candidat_par_service import reclamer_documents_au_candidat
from .refuser_proposition_service import refuser_proposition
from .retyper_document_service import retyper_document
from .soumettre_proposition_service import soumettre_proposition
from .supprimer_proposition_service import supprimer_proposition
from .valider_proposition_service import valider_proposition
