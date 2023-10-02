;(function ($) {
    if (window.__dal__initListenerIsSetForTag)
        return;

    $(document).on('autocompleteLightInitialize', '[data-autocomplete-light-function=select2_tag]', function() {
        /*
         * We override the default select2 initialization:
         * - to prevent the overriding of the option value with the option label when the tags are used ("processResults" in the original file)
         * - to insert the tag option only if there is no other result ("insertTag" in this file)
         *
         * Note that to simplify the code, the part related to the creation of objects in Django has been removed.
         */
        var element = $(this);

        // Templating helper
        function template(text, is_html) {
            if (is_html) {
                var $result = $('<span>');
                $result.html(text);
                return $result;
            } else {
                return text;
            }
        }

        function result_template(item) {
            return template(item.text,
                element.attr('data-html') !== undefined || element.attr('data-result-html') !== undefined
            );
        }

        function selected_template(item) {
            if (item.selected_text !== undefined) {
                return template(item.selected_text,
                    element.attr('data-html') !== undefined || element.attr('data-selected-html') !== undefined
                );
            } else {
                return result_template(item);
            }
        }

        var ajax = null;
        if ($(this).attr('data-autocomplete-light-url')) {
            ajax = {
                url: $(this).attr('data-autocomplete-light-url'),
                dataType: 'json',
                delay: 250,

                data: function (params) {
                    var data = {
                        q: params.term, // search term
                        page: params.page,
                        forward: yl.getForwards(element)
                    };

                    return data;
                },
                cache: true
            };
        }

        $(this).select2({
            tokenSeparators: element.attr('data-tags') ? [','] : null,
            debug: true,
            containerCssClass: ':all:',
            placeholder: element.attr('data-placeholder') || '',
            language: element.attr('data-autocomplete-light-language'),
            minimumInputLength: element.attr('data-minimum-input-length') || 0,
            allowClear: ! $(this).is('[required]'),
            templateResult: result_template,
            templateSelection: selected_template,
            ajax: ajax,
            tags: Boolean(element.attr('data-tags')),
            insertTag: function (data, tag) {
                // Insert the tag only if there is no result
                if (data.length === 0) {
                    data.push(tag);
                }
            }
        });
    });
    window.__dal__initListenerIsSetForTag = true;
    $('[data-autocomplete-light-function=select2_tag]:not([id*="__prefix__"])').each(function() {
        window.__dal__initialize(this);
    });
})(yl.jQuery);
