/*
 *
 * OSIS stands for Open Student Information System. It's an application
 * designed to manage the core business of higher education institutions,
 * such as universities, faculties, institutes and professional schools.
 * The core business involves the administration of students, teachers,
 * courses, programs and so on.
 *
 * Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * A copy of this license - GNU General Public License - is available
 * at the root of the source code of this program.  If not,
 * see http://www.gnu.org/licenses/.
 *
 */
/*
With htmx 1.9, inline scripts ($.ready) could be executed but with htmx 2.0, this no longer works very well so
the old scripts are embedded in a function that is trigger after the dom is updated.
The function name must be specified in the data-init-function property of the elements and the associated functions
must be specified in the window.admission namespace.
*/
document.body.addEventListener('htmx:afterSettle', function (event) {
    const originalElt = event.detail.elt;
    const elementsToInitialize = Array.from(originalElt.querySelectorAll('[data-init-function]'));
    elementsToInitialize.push(originalElt);
    elementsToInitialize.forEach(function(elt) {
      const currentFunctionName = elt.dataset.initFunction;
      if (currentFunctionName && window.admission[currentFunctionName]) {
        window.admission[currentFunctionName](elt);
      }
    });
});
