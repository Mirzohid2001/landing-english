/**
 * Mock test admin — savol turi bo'yicha maydonlarni ko'rsatish/yashirish.
 */
(function () {
    'use strict';

    var MCQ_TYPES = ['mcq', 'true_false_not_given', 'yes_no_not_given'];
    var FILL_TYPES = [
        'fill_blank',
        'sentence_completion',
        'summary_completion',
        'summary_box',
        'notes_completion',
        'table_completion',
    ];
    var MULTI_MATCHING = [
        'matching_headings',
        'matching_features',
        'matching_info',
        'matching_sentences',
        'classification',
    ];

    function showMcq(qType) {
        return qType && MCQ_TYPES.indexOf(qType) >= 0;
    }

    function showFillBlock(qType) {
        if (!qType) return false;
        return (
            FILL_TYPES.indexOf(qType) >= 0 ||
            qType === 'matching' ||
            MULTI_MATCHING.indexOf(qType) >= 0 ||
            qType === 'essay'
        );
    }

    function getInlineContainer(el) {
        if (!el) return null;
        return (
            el.closest('.inline-related') ||
            el.closest('.js-inline-admin-formset') ||
            el.closest('form')
        );
    }

    function toggleFieldset(fieldset, show) {
        if (!fieldset) return;
        fieldset.style.display = show ? '' : 'none';
        fieldset.classList.toggle('question-type-mcq-hidden', !show);
        fieldset.classList.toggle('question-type-section-visible', show);
        fieldset.setAttribute('aria-hidden', show ? 'false' : 'true');
    }

    function toggleFieldRow(container, fieldName, show) {
        if (!container) return;
        var row = container.querySelector('.form-row.field-' + fieldName);
        if (row) {
            row.style.display = show ? '' : 'none';
            row.classList.toggle('question-type-row-hidden', !show);
        }
    }

    function toggleByField(container, fieldKey, show) {
        toggleFieldRow(container, fieldKey, show);
        container.querySelectorAll('[data-qt-field="' + fieldKey + '"]').forEach(function (inp) {
            var row = inp.closest('.form-row');
            if (row) {
                row.style.display = show ? '' : 'none';
                row.classList.toggle('question-type-row-hidden', !show);
            }
        });
    }

    function ensureShartDiv(container) {
        var select = container.querySelector('select[name$="-question_type"]');
        if (!select || !window.QUESTION_TYPE_RULES) return null;
        var shartDiv = container.querySelector('.question-type-shart-box');
        if (!shartDiv) {
            shartDiv = document.createElement('div');
            shartDiv.className = 'question-type-shart-box';
            var row = select.closest('.form-row');
            if (row && row.parentNode) {
                row.parentNode.insertBefore(shartDiv, row.nextSibling);
            } else {
                container.appendChild(shartDiv);
            }
        }
        return shartDiv;
    }

    function updateShart(container, qType) {
        var shartDiv = ensureShartDiv(container);
        if (!shartDiv || !window.QUESTION_TYPE_RULES) return;
        var text = window.QUESTION_TYPE_RULES[qType] || '';
        if (text) {
            shartDiv.textContent = '\uD83D\uDCCB ' + text;
            shartDiv.style.display = 'block';
        } else {
            shartDiv.style.display = 'none';
        }
    }

    function hideUntilTypeChosen(container) {
        ['order', 'part_number', 'question_type', 'points'].forEach(function (name) {
            toggleFieldRow(container, name, true);
        });
        [
            'instruction',
            'question_text',
            'option_a',
            'option_b',
            'option_c',
            'option_d',
            'correct_answer',
            'fill_answers',
            'matching_items',
            'matching_options_lines',
            'matching_correct',
            'word_list_lines',
            'explanation',
            'audio_timestamp',
            'correct_answers_json',
            'options_json',
        ].forEach(function (name) {
            toggleFieldRow(container, name, false);
        });
        container.querySelectorAll('fieldset.question-mcq-fields, fieldset.question-fill-fields').forEach(
            function (fs) {
                toggleFieldset(fs, false);
            }
        );
        var shart = container.querySelector('.question-type-shart-box');
        if (shart) shart.style.display = 'none';
    }

    function toggleByQuestionType(container) {
        if (!container) return;
        var select = container.querySelector('select[name$="-question_type"]');
        if (!select) return;

        var qType = (select.value || '').trim();
        if (!qType) {
            hideUntilTypeChosen(container);
            return;
        }

        updateShart(container, qType);

        var showMcqFields = showMcq(qType);
        var showFill = showFillBlock(qType);
        var isMatching = qType === 'matching';
        var isMultiMatching = MULTI_MATCHING.indexOf(qType) >= 0;
        var isSummaryBox = qType === 'summary_box';
        var isFill =
            FILL_TYPES.indexOf(qType) >= 0 && qType !== 'summary_box';
        var isEssay = qType === 'essay';

        ['instruction', 'question_text', 'explanation', 'part_number', 'points'].forEach(
            function (name) {
                toggleFieldRow(container, name, true);
            }
        );
        var mcqFs = container.querySelector('fieldset.question-mcq-fields');
        var fillFs = container.querySelector('fieldset.question-fill-fields');
        toggleFieldset(mcqFs, showMcqFields);
        toggleFieldset(fillFs, showFill);

        toggleFieldRow(container, 'option_a', showMcqFields);
        toggleFieldRow(container, 'option_b', showMcqFields);
        toggleFieldRow(container, 'option_c', showMcqFields && (qType === 'mcq' || qType.indexOf('not_given') >= 0));
        toggleFieldRow(container, 'option_d', showMcqFields && qType === 'mcq');

        toggleFieldRow(container, 'fill_answers', isFill || isSummaryBox || qType === 'notes_completion' || qType === 'table_completion');
        toggleFieldRow(container, 'matching_items', isMultiMatching);
        toggleFieldRow(container, 'matching_options_lines', isMatching || isMultiMatching);
        toggleFieldRow(container, 'matching_correct', isMultiMatching);
        toggleFieldRow(container, 'word_list_lines', isSummaryBox);
        toggleFieldRow(container, 'audio_timestamp', !isEssay);
        toggleFieldRow(
            container,
            'correct_answer',
            showMcqFields || isMatching || (isFill && !isMultiMatching) || isSummaryBox
        );

        if (isEssay || isSpeaking) {
            toggleFieldRow(container, 'fill_answers', false);
            toggleFieldRow(container, 'matching_items', false);
            toggleFieldRow(container, 'matching_options_lines', false);
            toggleFieldRow(container, 'matching_correct', false);
            toggleFieldRow(container, 'word_list_lines', false);
            toggleFieldRow(container, 'correct_answer', false);
            toggleFieldRow(container, 'audio_timestamp', false);
        }
        if (isMultiMatching) {
            toggleFieldRow(container, 'correct_answer', false);
        }

        if (showMcqFields && qType === 'true_false_not_given') {
            autofillIfEmpty(container, 'option_a', 'True');
            autofillIfEmpty(container, 'option_b', 'False');
            autofillIfEmpty(container, 'option_c', 'Not Given');
        }
        if (showMcqFields && qType === 'yes_no_not_given') {
            autofillIfEmpty(container, 'option_a', 'Yes');
            autofillIfEmpty(container, 'option_b', 'No');
            autofillIfEmpty(container, 'option_c', 'Not Given');
        }

        toggleFieldRow(container, 'correct_answers_json', false);
        toggleFieldRow(container, 'options_json', false);
        refreshRowCollapse(container);
    }

    function autofillIfEmpty(container, field, value) {
        var el = container.querySelector('[name$="-' + field + '"]');
        if (el && !String(el.value || '').trim()) el.value = value;
    }

    function initQuestionForm(container) {
        if (!container) return;
        var select = container.querySelector('select[name$="-question_type"]');
        if (!select) return;

        if (!select.dataset.mockQtBound) {
            select.dataset.mockQtBound = '1';
            select.addEventListener('change', function () {
                toggleByQuestionType(container);
            });
        }
        toggleByQuestionType(container);
    }

    function runInit() {
        initAll();
        setTimeout(initAll, 100);
        setTimeout(initAll, 400);
        setTimeout(initAll, 1000);
    }

    document.addEventListener(
        'change',
        function (e) {
            if (
                e.target &&
                e.target.matches &&
                e.target.matches('select[name$="-question_type"]')
            ) {
                var container = getInlineContainer(e.target);
                toggleByQuestionType(container);
            }
        },
        true
    );

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', runInit);
        window.addEventListener('load', runInit);
    } else {
        runInit();
    }

    var QUICK_TEMPLATES = {
        mcq: {
            question_type: 'mcq',
            question_text: 'Choose the correct answer.',
            option_a: 'Option A',
            option_b: 'Option B',
            option_c: 'Option C',
            option_d: 'Option D',
        },
        notes: {
            question_type: 'notes_completion',
            question_text: 'Name [1], from [2]',
            fill_answers: 'anna, london',
        },
        tfng: {
            question_type: 'true_false_not_given',
            question_text: 'Statement about the text.',
            option_a: 'True',
            option_b: 'False',
            option_c: 'Not Given',
        },
        ynng: {
            question_type: 'yes_no_not_given',
            question_text: 'Statement about the text.',
            option_a: 'Yes',
            option_b: 'No',
            option_c: 'Not Given',
        },
        fill: {
            question_type: 'fill_blank',
            question_text: 'Complete: The city is called ______.',
            fill_answers: 'london',
            correct_answer: 'london',
        },
        matching_h: {
            question_type: 'matching_headings',
            question_text: 'Match headings to paragraphs.',
            matching_items: '14|Paragraph A\n15|Paragraph B',
            matching_options_lines: 'i|First heading\nii|Second heading\niii|Third heading',
            matching_correct: '14:i\n15:ii',
        },
    };

    function getTestType() {
        if (window.MOCK_TEST_META && window.MOCK_TEST_META.type) {
            return window.MOCK_TEST_META.type;
        }
        var el = document.getElementById('id_test_type');
        return el && el.value ? el.value : 'reading';
    }

    function partFromOrder(order, testType) {
        var n = parseInt(order, 10);
        if (!n || isNaN(n)) return 1;
        if (testType === 'listening') {
            if (n <= 10) return 1;
            if (n <= 20) return 2;
            if (n <= 30) return 3;
            return 4;
        }
        if (testType === 'reading') {
            if (n <= 13) return 1;
            if (n <= 26) return 2;
            return 3;
        }
        if (testType === 'writing') {
            return n <= 1 ? 1 : 2;
        }
        return 1;
    }

    function defaultQuestionType(testType) {
        if (testType === 'listening') return 'notes_completion';
        if (testType === 'writing') return 'essay';
        return 'mcq';
    }

    function getMaxOrder(excludeInput) {
        var max = 0;
        document.querySelectorAll('input[name$="-order"]').forEach(function (inp) {
            if (excludeInput && inp === excludeInput) return;
            var v = parseInt(inp.value, 10);
            if (!isNaN(v) && v > max) max = v;
        });
        return max;
    }

    function suggestRowDefaults(container, force) {
        if (!container) return;
        var orderInp = container.querySelector('input[name$="-order"]');
        var partInp = container.querySelector('input[name$="-part_number"]');
        var typeSelect = container.querySelector('select[name$="-question_type"]');
        var deleteCheck = container.querySelector('input[name$="-DELETE"]');
        if (deleteCheck && deleteCheck.checked) return;

        var testType = getTestType();
        if (orderInp && (force || !orderInp.value)) {
            orderInp.value = getMaxOrder(orderInp) + 1;
        }
        var orderVal = orderInp ? parseInt(orderInp.value, 10) : 0;
        if (partInp && (force || !partInp.value) && orderVal) {
            partInp.value = partFromOrder(orderVal, testType);
        }
        if (typeSelect && (force || !typeSelect.value)) {
            typeSelect.value = defaultQuestionType(testType);
            typeSelect.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    function getInlineRows() {
        return Array.prototype.slice.call(
            document.querySelectorAll('#mockquestion_set-group .inline-related')
        ).filter(function (row) {
            return row.querySelector('select[name$="-question_type"]');
        });
    }

    function findPreviousRow(container) {
        var rows = getInlineRows();
        var idx = rows.indexOf(container);
        if (idx > 0) return rows[idx - 1];
        return null;
    }

    function fieldValue(row, suffix) {
        var el = row.querySelector('[name$="-' + suffix + '"]');
        if (!el) return '';
        if (el.type === 'checkbox') return el.checked;
        return el.value;
    }

    function setFieldValue(row, suffix, value) {
        var el = row.querySelector('[name$="-' + suffix + '"]');
        if (!el) return;
        if (el.type === 'checkbox') {
            el.checked = !!value;
        } else {
            el.value = value;
        }
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.dispatchEvent(new Event('input', { bubbles: true }));
    }

    function duplicateFromPrevious(container) {
        var prev = findPreviousRow(container);
        if (!prev) {
            window.alert('Oldingi savol yo\'q — avval bir savol qo\'shing.');
            return;
        }
        var testType = getTestType();
        var nextOrder = getMaxOrder(container.querySelector('input[name$="-order"]')) + 1;
        var copyFields = [
            'question_type', 'part_number', 'points', 'instruction',
            'option_a', 'option_b', 'option_c', 'option_d',
            'fill_answers', 'matching_items', 'matching_options_lines',
            'matching_correct', 'word_list_lines', 'explanation', 'audio_timestamp',
        ];
        copyFields.forEach(function (name) {
            setFieldValue(container, name, fieldValue(prev, name));
        });
        setFieldValue(container, 'order', nextOrder);
        setFieldValue(container, 'part_number', partFromOrder(nextOrder, testType));
        setFieldValue(container, 'question_text', '');
        setFieldValue(container, 'correct_answer', '');
        var typeSelect = container.querySelector('select[name$="-question_type"]');
        if (typeSelect) toggleByQuestionType(container);
        container.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function addInlineTools(container) {
        if (!container || container.querySelector('.mock-inline-tools')) return;
        var tools = document.createElement('div');
        tools.className = 'mock-inline-tools';

        var dupBtn = document.createElement('button');
        dupBtn.type = 'button';
        dupBtn.className = 'mock-dup-prev-btn button';
        dupBtn.textContent = 'Oldingisidan nusxa';
        dupBtn.addEventListener('click', function () {
            duplicateFromPrevious(container);
        });

        var suggestBtn = document.createElement('button');
        suggestBtn.type = 'button';
        suggestBtn.className = 'mock-suggest-order-btn button';
        suggestBtn.textContent = 'Order/Part avto';
        suggestBtn.addEventListener('click', function () {
            suggestRowDefaults(container, true);
        });

        tools.appendChild(dupBtn);
        tools.appendChild(suggestBtn);

        var anchor = container.querySelector('h3') || container.querySelector('.inline_label') || container.firstElementChild;
        if (anchor && anchor.parentNode) {
            anchor.parentNode.insertBefore(tools, anchor.nextSibling);
        } else {
            container.insertBefore(tools, container.firstChild);
        }
    }

    function updateQuestionStats() {
        var statsEl = document.getElementById('mock-admin-question-stats');
        if (!statsEl) return;
        var rows = getInlineRows();
        var parts = {};
        var count = 0;
        rows.forEach(function (row) {
            var del = row.querySelector('input[name$="-DELETE"]');
            if (del && del.checked) return;
            var order = fieldValue(row, 'order');
            if (!order) return;
            count += 1;
            var part = fieldValue(row, 'part_number') || '?';
            parts[part] = (parts[part] || 0) + 1;
        });
        if (!count) {
            statsEl.textContent = 'Hali savol qatorlari bo\'sh — «Yana bir Savol qo\'shish» bosing.';
            return;
        }
        var partText = Object.keys(parts).sort().map(function (p) {
            return 'Part ' + p + ': ' + parts[p] + ' ta';
        }).join(' · ');
        statsEl.textContent = 'Jami ' + count + ' ta savol qatori · ' + partText;
    }

    function applyTemplateToRow(container, templateKey) {
        var tpl = QUICK_TEMPLATES[templateKey];
        if (!tpl || !container) return;
        Object.keys(tpl).forEach(function (key) {
            setFieldValue(container, key, tpl[key]);
        });
        suggestRowDefaults(container, true);
        var typeSelect = container.querySelector('select[name$="-question_type"]');
        if (typeSelect) toggleByQuestionType(container);
        container.classList.add('mock-inline-expanded');
        container.classList.remove('mock-inline-collapsed');
        container.scrollIntoView({ behavior: 'smooth', block: 'center' });
        var qt = container.querySelector('[name$="-question_text"]');
        if (qt) qt.focus();
    }

    function clickAddQuestion() {
        var link = document.querySelector('#mockquestion_set-group .add-row a');
        if (link) link.click();
    }

    function addFromTemplate(templateKey) {
        clickAddQuestion();
        setTimeout(function () {
            var rows = getInlineRows();
            var row = rows[rows.length - 1];
            if (row) applyTemplateToRow(row, templateKey);
            updateQuestionStats();
        }, 220);
    }

    function rowSummaryText(row) {
        var order = fieldValue(row, 'order') || '?';
        var qtype = fieldValue(row, 'question_type') || 'tur tanlanmagan';
        var text = fieldValue(row, 'question_text') || '';
        text = text.replace(/\s+/g, ' ').trim();
        if (text.length > 55) text = text.slice(0, 55) + '…';
        return '#' + order + ' · ' + qtype + (text ? ' — ' + text : '');
    }

    function refreshRowCollapse(row) {
        if (!row) return;
        var idInp = row.querySelector('input[name$="-id"]');
        var isSaved = idInp && idInp.value;
        var summary = row.querySelector('.mock-row-summary');
        if (!summary) {
            summary = document.createElement('button');
            summary.type = 'button';
            summary.className = 'mock-row-summary';
            row.insertBefore(summary, row.firstChild);
            summary.addEventListener('click', function () {
                row.classList.toggle('mock-inline-expanded');
                row.classList.toggle('mock-inline-collapsed');
            });
        }
        summary.textContent = rowSummaryText(row) + '  ▾ ochish';
        if (isSaved && !row.classList.contains('mock-inline-expanded')) {
            row.classList.add('mock-inline-collapsed');
        }
        if (!isSaved) {
            row.classList.add('mock-inline-expanded');
            row.classList.remove('mock-inline-collapsed');
        }
    }

    function collapseAllSaved() {
        getInlineRows().forEach(function (row) {
            var idInp = row.querySelector('input[name$="-id"]');
            if (idInp && idInp.value) {
                row.classList.add('mock-inline-collapsed');
                row.classList.remove('mock-inline-expanded');
            }
        });
    }

    function expandAllRows() {
        getInlineRows().forEach(function (row) {
            row.classList.add('mock-inline-expanded');
            row.classList.remove('mock-inline-collapsed');
        });
    }

    function injectQuickToolbar() {
        var group = document.getElementById('mockquestion_set-group');
        if (!group || group.querySelector('.mock-quick-toolbar')) return;

        var bar = document.createElement('div');
        bar.className = 'mock-quick-toolbar';
        bar.innerHTML =
            '<span class="mock-quick-label">Tez qo\'shish:</span>' +
            '<button type="button" class="button mock-tpl-btn" data-tpl="mcq">+ MCQ</button>' +
            '<button type="button" class="button mock-tpl-btn" data-tpl="notes">+ Notes</button>' +
            '<button type="button" class="button mock-tpl-btn" data-tpl="tfng">+ T/F/NG</button>' +
            '<button type="button" class="button mock-tpl-btn" data-tpl="ynng">+ Y/N/NG</button>' +
            '<button type="button" class="button mock-tpl-btn" data-tpl="fill">+ Bo\'sh joy</button>' +
            '<button type="button" class="button mock-tpl-btn" data-tpl="matching_h">+ Headings</button>' +
            '<span class="mock-quick-spacer"></span>' +
            '<button type="button" class="button mock-collapse-btn" id="mock-collapse-all">Yig\'ish</button>' +
            '<button type="button" class="button mock-collapse-btn" id="mock-expand-all">Hammasini ochish</button>';

        group.insertBefore(bar, group.firstChild);

        bar.querySelectorAll('.mock-tpl-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                addFromTemplate(btn.getAttribute('data-tpl'));
            });
        });
        bar.querySelector('#mock-collapse-all').addEventListener('click', collapseAllSaved);
        bar.querySelector('#mock-expand-all').addEventListener('click', expandAllRows);
    }

    function injectListeningAudio() {
        var meta = window.MOCK_TEST_META;
        if (!meta || meta.type !== 'listening' || !meta.audioUrl) return;
        var group = document.getElementById('mockquestion_set-group');
        if (!group || group.querySelector('.mock-admin-audio-bar')) return;

        var wrap = document.createElement('div');
        wrap.className = 'mock-admin-audio-bar';
        wrap.innerHTML =
            '<strong>Listening audio</strong>' +
            '<audio controls preload="metadata" class="mock-admin-audio-el" src="' + meta.audioUrl + '"></audio>' +
            '<span class="mock-admin-audio-tip">Audio vaqtini (soniya) tinglab yozing — har savolda «Audio vaqti» maydoni.</span>';
        var toolbar = group.querySelector('.mock-quick-toolbar');
        if (toolbar) {
            group.insertBefore(wrap, toolbar.nextSibling);
        } else {
            group.insertBefore(wrap, group.firstChild);
        }
    }

    function enhanceInlineRow(container) {
        initQuestionForm(container);
        addInlineTools(container);
        suggestRowDefaults(container, false);
        refreshRowCollapse(container);
    }

    function initAll() {
        injectQuickToolbar();
        injectListeningAudio();
        document
            .querySelectorAll('#mockquestion_set-group .inline-related, #content-main .inline-related')
            .forEach(function (el) {
                if (el.querySelector('select[name$="-question_type"]')) {
                    enhanceInlineRow(el);
                }
            });
        var qForm = document.getElementById('mockquestion_form');
        if (qForm) initQuestionForm(qForm);
        updateQuestionStats();
    }

    if (typeof django !== 'undefined' && django.jQuery) {
        django.jQuery(document).on('formset:added', function (event, $row, name) {
            if (String(name).indexOf('question') >= 0 && $row && $row[0]) {
                enhanceInlineRow($row[0]);
            }
        });
    }

    document.addEventListener('input', function (e) {
        if (!e.target || !e.target.matches) return;
        if (e.target.matches('input[name$="-order"], input[name$="-part_number"], textarea[name$="-question_text"]')) {
            updateQuestionStats();
            var row = getInlineContainer(e.target);
            if (row) refreshRowCollapse(row);
        }
    });

    if (window.MutationObserver) {
        var timer;
        var group = document.getElementById('mockquestion_set-group');
        if (group) {
            new MutationObserver(function () {
                clearTimeout(timer);
                timer = setTimeout(initAll, 150);
            }).observe(group, { childList: true, subtree: true });
        }
    }
})();
