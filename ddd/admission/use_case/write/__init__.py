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
from .annuler_reclamation_emplacement_document_service import annuler_reclamation_emplacement_document
from .initialiser_emplacement_document_a_reclamer_service import initialiser_emplacement_document_a_reclamer
from .initialiser_emplacement_document_libre_a_reclamer_service import initialiser_emplacement_document_libre_a_reclamer
from .initialiser_emplacement_document_libre_non_reclamable import initialiser_emplacement_document_libre_non_reclamable
from .modifier_reclamation_emplacement_document_service import modifier_reclamation_emplacement_document
from .remplacer_emplacement_document_service import remplacer_emplacement_document
from .remplir_emplacement_document_par_gestionnaire_service import remplir_emplacement_document_par_gestionnaire
from .specifier_experience_en_tant_que_titre_acces_service import specifier_experience_en_tant_que_titre_acces
from .supprimer_emplacement_document_service import supprimer_emplacement_document
