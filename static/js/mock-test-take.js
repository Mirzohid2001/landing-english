(function () {
    const exam = document.getElementById('mock-exam');
    if (!exam) return;

    const takeUrl = exam.dataset.takeUrl;
    const testId = exam.dataset.testId;
    const totalQuestions = parseInt(exam.dataset.totalQuestions || '0', 10);
    const durationMinutes = parseInt(exam.dataset.duration || '60', 10);
    const csrfToken = exam.dataset.csrf || (document.cookie.match(/csrftoken=([^;]+)/) || [])[1];
    const savedDataEl = document.getElementById('saved-answers-data');
    let savedAnswers = {};
    if (savedDataEl) {
        try { savedAnswers = JSON.parse(savedDataEl.textContent); } catch (e) {}
    }

    let highlightMode = false;
    let isPaused = false;
    let secondsLeft = durationMinutes * 60;
    let timerInterval = null;
    let currentNavIndex = 0;
    const audioEl = document.getElementById('exam-audio');
    const navButtons = Array.from(exam.querySelectorAll('.mock-q-nav-btn, .q-num-btn'));
    const notesKey = 'reading_notes_test_' + testId;

    function collectAnswers() {
        const answers = {};
        exam.querySelectorAll('.mock-matching-select').forEach((sel) => {
            const qid = sel.dataset.questionId;
            const num = sel.dataset.matchNum;
            if (!qid || !num) return;
            if (!answers[qid] || typeof answers[qid] !== 'object') answers[qid] = {};
            if (sel.value) answers[qid][num] = sel.value;
        });
        exam.querySelectorAll('[data-question-id]').forEach((el) => {
            if (el.classList.contains('mock-matching-select')) return;
            const qid = el.dataset.questionId;
            if (el.classList.contains('mock-inline-input') && el.dataset.blank) {
                if (!answers[qid] || typeof answers[qid] !== 'object') answers[qid] = {};
                answers[qid][el.dataset.blank] = el.value.trim();
                return;
            }
            if (el.type === 'radio') {
                if (el.checked) answers[qid] = el.value;
            } else if (el.tagName === 'TEXTAREA') {
                answers[qid] = el.value.trim();
            } else if (el.tagName === 'INPUT') {
                answers[qid] = el.value.trim();
            }
        });
        return answers;
    }

    function isAnswered(value) {
        if (value == null) return false;
        if (typeof value === 'object') return Object.values(value).some(v => v && String(v).length > 0);
        return String(value).length > 0;
    }

    function countWords(text) {
        const t = (text || '').trim();
        return t ? t.split(/\s+/).filter(Boolean).length : 0;
    }

    function isNavAnswered(btn, answers) {
        const qid = btn.dataset.qid;
        if (btn.dataset.blank) {
            const val = answers[qid];
            if (val && typeof val === 'object') {
                return !!(val[btn.dataset.blank] && String(val[btn.dataset.blank]).length);
            }
            return false;
        }
        return isAnswered(answers[qid]);
    }

    function setActiveNavBtn(btn) {
        exam.querySelectorAll('.mock-q-nav-btn, .q-num-btn').forEach(b => {
            b.classList.toggle('active', b === btn);
        });
    }

    function countAnsweredSlots(answers) {
        const navBtns = exam.querySelectorAll('.mock-q-nav-btn, .q-num-btn');
        if (navBtns.length) {
            let n = 0;
            navBtns.forEach(btn => { if (isNavAnswered(btn, answers)) n++; });
            return n;
        }
        let count = 0;
        Object.values(answers).forEach(v => {
            if (typeof v === 'object' && v && !Array.isArray(v)) {
                Object.values(v).forEach(blank => {
                    if (blank && String(blank).trim().length) count++;
                });
            } else if (isAnswered(v)) {
                count++;
            }
        });
        return count;
    }

    function setAnsweredCounts(count) {
        document.querySelectorAll('#answered-count, #answered-count-top').forEach(el => {
            el.textContent = count;
        });
    }

    function updateCurrentQuestionLabel(order) {
        const qLabel = document.getElementById('current-q-label');
        if (qLabel && order != null) qLabel.textContent = order;
    }

    function getAllNavButtons() {
        return Array.from(exam.querySelectorAll('.mock-q-nav-btn, .q-num-btn'));
    }

    function getUnansweredSlotNums(answers) {
        const nums = [];
        getAllNavButtons().forEach(btn => {
            if (!isNavAnswered(btn, answers)) {
                const n = parseInt(btn.dataset.order, 10);
                nums.push(Number.isFinite(n) ? n : btn.textContent.trim());
            }
        });
        return nums.sort((a, b) => {
            const na = parseInt(a, 10);
            const nb = parseInt(b, 10);
            if (Number.isFinite(na) && Number.isFinite(nb)) return na - nb;
            return String(a).localeCompare(String(b));
        });
    }

    function updateProgress() {
        const answers = collectAnswers();
        const count = countAnsweredSlots(answers);
        setAnsweredCounts(count);
        const pct = totalQuestions ? Math.min(100, Math.round((count / totalQuestions) * 100)) : 0;
        ['progress-pct'].forEach(id => { const el = document.getElementById(id); if (el) el.textContent = pct + '%'; });
        const fillEl = document.getElementById('progress-fill');
        if (fillEl) fillEl.style.width = pct + '%';
        exam.querySelectorAll('.mock-q-nav-btn, .q-num-btn').forEach(btn => {
            btn.classList.toggle('answered', isNavAnswered(btn, answers));
        });
        maybeCelebrate(count);
    }

    function setAutosaveStatus(text, saved) {
        document.querySelectorAll('.mock-autosave-el').forEach(el => {
            el.textContent = text;
            el.classList.toggle('saved', !!saved);
        });
    }

    function toast(msg, type, title) {
        if (typeof showToast === 'function') showToast(msg, type || 'success', title || '');
    }

    let celebratedFull = false;
    function maybeCelebrate(count) {
        if (celebratedFull || !totalQuestions || count < totalQuestions) return;
        celebratedFull = true;
        toast('Barcha savollarga javob berdingiz — ajoyib!', 'success', 'Tayyor');
        document.querySelectorAll('.listening-answered-pill, .mock-answered-pill').forEach(p => {
            p.classList.add('mock-celebrate');
        });
    }

    function formatTimeLeft() {
        const m = Math.floor(secondsLeft / 60);
        const s = secondsLeft % 60;
        return m + ':' + String(s).padStart(2, '0');
    }

    function openSubmitModal(options) {
        const opts = options || {};
        updateProgress();
        const answers = collectAnswers();
        const count = countAnsweredSlots(answers);
        const unanswered = getUnansweredSlotNums(answers);
        const modal = document.getElementById('submit-modal');
        const answeredEl = document.getElementById('submit-answered');
        const warnEl = document.getElementById('submit-warn');
        const timeEl = document.getElementById('submit-time-left');
        const listWrap = document.getElementById('submit-unanswered-wrap');
        const listEl = document.getElementById('submit-unanswered-list');
        const timeUpEl = document.getElementById('submit-timeup');
        const titleEl = document.getElementById('submit-modal-title');
        if (answeredEl) answeredEl.textContent = count;
        if (timeEl) timeEl.textContent = formatTimeLeft();
        if (warnEl) warnEl.hidden = !unanswered.length;
        if (listWrap && listEl) {
            if (unanswered.length) {
                listWrap.hidden = false;
                listEl.innerHTML = unanswered.map(n =>
                    `<li><button type="button" class="mock-submit-goto" data-goto-order="${n}">${n}</button></li>`
                ).join('');
                listEl.querySelectorAll('.mock-submit-goto').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const order = btn.dataset.gotoOrder;
                        const target = getAllNavButtons().find(b => String(b.dataset.order) === String(order));
                        closeSubmitModal();
                        if (target) scrollToQuestion(target);
                    });
                });
            } else {
                listWrap.hidden = true;
                listEl.innerHTML = '';
            }
        }
        if (timeUpEl) timeUpEl.hidden = !opts.timeUp;
        if (titleEl) {
            titleEl.textContent = opts.timeUp ? 'Vaqt tugadi' : 'Testni yakunlaysizmi?';
        }
        if (modal) {
            modal.hidden = false;
            modal.setAttribute('aria-hidden', 'false');
            modal.classList.add('is-open');
            if (opts.timeUp) modal.classList.add('is-time-up');
            else modal.classList.remove('is-time-up');
        }
    }

    function closeSubmitModal() {
        const modal = document.getElementById('submit-modal');
        if (modal) {
            modal.hidden = true;
            modal.setAttribute('aria-hidden', 'true');
            modal.classList.remove('is-open', 'is-time-up');
        }
        const timeUpEl = document.getElementById('submit-timeup');
        const titleEl = document.getElementById('submit-modal-title');
        if (timeUpEl) timeUpEl.hidden = true;
        if (titleEl) titleEl.textContent = 'Testni yakunlaysizmi?';
    }

    function restoreAnswers() {
        Object.entries(savedAnswers).forEach(([qid, value]) => {
            if (value && typeof value === 'object' && !Array.isArray(value)) {
                Object.entries(value).forEach(([blankNum, blankVal]) => {
                    const sel = exam.querySelector(
                        `.mock-matching-select[data-question-id="${qid}"][data-match-num="${blankNum}"]`
                    );
                    if (sel) { sel.value = blankVal; return; }
                    const input = exam.querySelector(
                        `input.mock-inline-input[data-question-id="${qid}"][data-blank="${blankNum}"]`
                    );
                    if (input) input.value = blankVal;
                });
                return;
            }
            const radio = exam.querySelector(`input[type="radio"][data-question-id="${qid}"][value="${value}"]`);
            if (radio) { radio.checked = true; return; }
            const textarea = exam.querySelector(`textarea[data-question-id="${qid}"]`);
            if (textarea) { textarea.value = value; updateEssayCount(textarea); return; }
            const input = exam.querySelector(`input[data-question-id="${qid}"]`);
            if (input) input.value = value;
        });
        updateProgress();
    }

    function updateEssayCount(textarea) {
        const counter = exam.querySelector(`.essay-chars[data-for="${textarea.dataset.questionId}"]`);
        if (counter) counter.textContent = countWords(textarea.value);
    }

    async function saveProgress(manual) {
        setAutosaveStatus('Saqlanmoqda...', false);
        try {
            const res = await fetch(takeUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ action: 'save', answers: collectAnswers() }),
            });
            const data = await res.json();
            if (data.success) {
                const msg = manual ? 'Saqlangan' : 'Avtomatik saqlandi';
                setAutosaveStatus(msg, true);
                if (manual) toast('Javoblaringiz saqlandi', 'success');
            }
        } catch (e) {
            setAutosaveStatus('Saqlash xatosi', false);
            if (manual) toast('Saqlab bo\'lmadi. Internetni tekshiring.', 'error', 'Xatolik');
        }
    }

    let submitting = false;
    async function finishTest() {
        if (submitting) return;
        closeSubmitModal();
        submitting = true;
        const loader = document.getElementById('exam-loader');
        if (loader) { loader.hidden = false; loader.classList.add('is-visible'); }
        try {
            const res = await fetch(takeUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ action: 'finish', answers: collectAnswers() }),
            });
            const data = await res.json();
            if (data.success && data.redirect_url) window.location.href = data.redirect_url;
            else {
                submitting = false;
                if (loader) { loader.hidden = true; loader.classList.remove('is-visible'); }
                toast('Yuborib bo\'lmadi. Qayta urinib ko\'ring.', 'error', 'Xatolik');
            }
        } catch (e) {
            submitting = false;
            if (loader) { loader.hidden = true; loader.classList.remove('is-visible'); }
            toast('Xatolik yuz berdi. Qayta urinib ko\'ring.', 'error', 'Xatolik');
        }
    }

    function switchPart(part) {
        document.querySelectorAll('.mock-part-switch, .mock-part-tab, .mock-part-chip, .listening-part-chip').forEach(el => {
            el.classList.toggle('is-active', el.dataset.part === part);
        });
        document.querySelectorAll('.listening-part-ribbon-panel').forEach(r => {
            r.classList.toggle('is-active', r.dataset.partRibbon === part);
        });
        document.querySelectorAll('.mock-part-panel').forEach(p => {
            p.classList.toggle('is-active', p.dataset.partPanel === part);
        });
        document.querySelectorAll('.mock-left-panel').forEach(p => {
            p.classList.toggle('is-active', p.dataset.partLeft === part);
        });
        document.querySelectorAll('.dock-part-wrap').forEach(w => {
            w.classList.toggle('dock-active', w.dataset.partNumber === part);
        });
        const scroll = document.getElementById('questions-scroll');
        if (scroll) scroll.scrollTop = 0;
        const passageScroll = document.getElementById('reading-passage-scroll');
        if (passageScroll) passageScroll.scrollTop = 0;
        const activePanel = document.querySelector('.mock-part-panel.is-active .listening-part-content-box');
        if (activePanel) {
            activePanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    document.querySelectorAll('.mock-part-switch, .mock-part-tab, .mock-part-chip, .dock-part-summary, .listening-part-chip').forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            if (tab.dataset.part) switchPart(tab.dataset.part);
        });
    });

    document.querySelectorAll('.listening-dock-part').forEach(partEl => {
        const activate = (e) => {
            if (e.target.closest('.q-num-btn, .mock-q-nav-btn')) return;
            if (partEl.dataset.part) switchPart(partEl.dataset.part);
        };
        partEl.addEventListener('click', activate);
        partEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                activate(e);
            }
        });
    });

    function scrollToQuestion(btn) {
        if (!btn) return;
        switchPart(btn.dataset.part);
        setActiveNavBtn(btn);
        updateCurrentQuestionLabel(btn.dataset.order || btn.textContent.trim());
        if (btn.dataset.blank) {
            const sel = exam.querySelector(
                `.mock-matching-select[data-question-id="${btn.dataset.qid}"][data-match-num="${btn.dataset.blank}"]`
            );
            if (sel) {
                sel.focus();
                sel.scrollIntoView({ behavior: 'smooth', block: 'center' });
                return;
            }
            const input = exam.querySelector(
                `input.mock-inline-input[data-question-id="${btn.dataset.qid}"][data-blank="${btn.dataset.blank}"]`
            );
            if (input) {
                input.focus();
                input.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            return;
        }
        const card = document.getElementById('q-card-' + btn.dataset.qid);
        if (card) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function visibleNavButtons() {
        const activeWrap = document.querySelector('.dock-part-wrap.dock-active');
        if (activeWrap) {
            return Array.from(activeWrap.querySelectorAll('.mock-q-nav-btn, .q-num-btn'));
        }
        return navButtons;
    }

    navButtons.forEach((btn, idx) => {
        btn.addEventListener('click', () => {
            const btns = visibleNavButtons();
            currentNavIndex = btns.indexOf(btn);
            if (currentNavIndex < 0) currentNavIndex = idx;
            scrollToQuestion(btn);
        });
    });

    document.getElementById('nav-prev')?.addEventListener('click', () => {
        const btns = visibleNavButtons();
        if (!btns.length) return;
        currentNavIndex = Math.max(0, currentNavIndex - 1);
        scrollToQuestion(btns[currentNavIndex]);
    });

    document.getElementById('nav-next')?.addEventListener('click', () => {
        const btns = visibleNavButtons();
        if (!btns.length) return;
        currentNavIndex = Math.min(btns.length - 1, currentNavIndex + 1);
        scrollToQuestion(btns[currentNavIndex]);
    });

    function setHighlightMode(on) {
        highlightMode = on;
        document.querySelectorAll('[data-highlight="toggle"]').forEach(btn => btn.classList.toggle('active', highlightMode));
    }

    document.querySelectorAll('.mock-tool-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.dataset.highlight === 'toggle') { setHighlightMode(!highlightMode); return; }
            if (btn.dataset.font) {
                const panel = document.querySelector('.mock-left-panel.is-active');
                const text = panel && panel.querySelector('.mock-passage-text');
                if (!text) return;
                const size = parseFloat(getComputedStyle(text).fontSize);
                text.style.fontSize = (btn.dataset.font === 'inc' ? size + 1 : Math.max(12, size - 1)) + 'px';
            }
        });
    });

    document.querySelectorAll('.selectable-text').forEach(el => {
        el.addEventListener('mouseup', () => {
            if (!highlightMode) return;
            const sel = window.getSelection();
            if (!sel || sel.isCollapsed) return;
            const range = sel.getRangeAt(0);
            if (!el.contains(range.commonAncestorContainer)) return;
            const mark = document.createElement('mark');
            mark.className = 'mock-highlight';
            try { range.surroundContents(mark); } catch (e) {}
            sel.removeAllRanges();
        });
    });

    /* Reading notes */
    function renderNotes() {
        const panel = document.getElementById('reading-notes-panel');
        if (!panel) return;
        let notes = [];
        try { notes = JSON.parse(localStorage.getItem(notesKey) || '[]'); } catch (e) {}
        if (!notes.length) {
            panel.innerHTML = '<div class="mock-notes-empty">Hozircha note yo\'q.</div>';
            return;
        }
        panel.innerHTML = notes.map(n =>
            '<div class="mock-note-item"><strong>Text:</strong> ' + escapeHtml(n.text) +
            '<div class="mock-muted-small" style="margin-top:0.25rem">' + escapeHtml(n.note) + '</div></div>'
        ).join('');
    }

    function escapeHtml(s) {
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    document.getElementById('btn-add-note')?.addEventListener('click', () => {
        const pane = document.querySelector('.mock-passage-text');
        const sel = window.getSelection();
        if (!pane || !sel || !sel.toString().trim() || !pane.contains(sel.anchorNode)) {
            alert('Avval matndan so\'z yoki qismni tanlang.');
            return;
        }
        const note = window.prompt('Qisqa note yozing:');
        if (!note) return;
        let notes = [];
        try { notes = JSON.parse(localStorage.getItem(notesKey) || '[]'); } catch (e) {}
        notes.unshift({ text: sel.toString().trim().slice(0, 180), note: note.slice(0, 400), ts: Date.now() });
        localStorage.setItem(notesKey, JSON.stringify(notes.slice(0, 30)));
        renderNotes();
        setAutosaveStatus('Note saved', true);
    });
    renderNotes();

    /* Split resize */
    const handle = document.getElementById('mock-split-handle');
    const leftPane = document.getElementById('mock-pane-left');
    if (handle && leftPane) {
        handle.addEventListener('mousedown', (e) => {
            const startX = e.clientX, startW = leftPane.offsetWidth;
            const onMove = (ev) => { leftPane.style.flex = 'none'; leftPane.style.width = Math.max(240, startW + (ev.clientX - startX)) + 'px'; };
            const onUp = () => { document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp); };
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
        });
    }

    document.querySelectorAll('.mock-listen-from-here').forEach(btn => {
        btn.addEventListener('click', e => {
            e.preventDefault();
            if (!audioEl) return;
            let ts = parseFloat(btn.dataset.audioTs);
            if (isNaN(ts) && btn.dataset.part) {
                const panel = document.querySelector(`.mock-part-panel[data-part-panel="${btn.dataset.part}"]`);
                const card = panel && panel.querySelector('[data-audio-ts]');
                ts = card ? parseFloat(card.dataset.audioTs) : 0;
            }
            audioEl.currentTime = isNaN(ts) ? 0 : ts;
            audioEl.play().catch(function () {});
        });
    });

    if (audioEl) {
        const timeEl = document.getElementById('audio-time');
        const track = document.getElementById('audio-progress-track');
        const fill = document.getElementById('audio-progress-fill');
        const buffer = document.getElementById('audio-progress-buffer');
        const thumb = document.getElementById('audio-progress-thumb');
        const fmt = sec => {
            if (!isFinite(sec)) return '0:00';
            return Math.floor(sec / 60) + ':' + String(Math.floor(sec % 60)).padStart(2, '0');
        };
        const upd = () => {
            const dur = audioEl.duration || 0;
            const cur = audioEl.currentTime || 0;
            const pct = dur ? (cur / dur) * 100 : 0;
            if (fill) fill.style.width = pct + '%';
            if (thumb) thumb.style.left = pct + '%';
            if (track) track.setAttribute('aria-valuenow', String(Math.round(pct)));
            if (timeEl) timeEl.textContent = fmt(cur) + ' / ' + fmt(dur);
            if (buffer && audioEl.buffered.length && dur) {
                const end = audioEl.buffered.end(audioEl.buffered.length - 1);
                buffer.style.width = (end / dur) * 100 + '%';
            }
        };
        const seekFromClientX = (clientX) => {
            if (!track || !audioEl.duration) return;
            const rect = track.getBoundingClientRect();
            const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
            audioEl.currentTime = ratio * audioEl.duration;
            upd();
        };
        track?.addEventListener('click', (e) => seekFromClientX(e.clientX));
        track?.addEventListener('keydown', (e) => {
            if (!audioEl.duration) return;
            const step = 5;
            if (e.key === 'ArrowRight') audioEl.currentTime = Math.min(audioEl.duration, audioEl.currentTime + step);
            if (e.key === 'ArrowLeft') audioEl.currentTime = Math.max(0, audioEl.currentTime - step);
            upd();
        });
        let dragging = false;
        track?.addEventListener('mousedown', (e) => {
            dragging = true;
            seekFromClientX(e.clientX);
            e.preventDefault();
        });
        document.addEventListener('mousemove', (e) => {
            if (dragging) seekFromClientX(e.clientX);
        });
        document.addEventListener('mouseup', () => { dragging = false; });
        audioEl.addEventListener('loadedmetadata', upd);
        audioEl.addEventListener('timeupdate', upd);
        audioEl.addEventListener('progress', upd);
    }

    function initOnboarding() {
        const ONBOARDING_KEY = 'mock_onboarding_v1_done';
        try {
            if (localStorage.getItem(ONBOARDING_KEY)) return;
        } catch (e) { return; }

        const overlay = document.getElementById('mock-onboarding');
        const spotlight = document.getElementById('mock-onboarding-spotlight');
        const tooltip = document.getElementById('mock-onboarding-tooltip');
        const stepEl = document.getElementById('mock-onboarding-step');
        const titleEl = document.getElementById('mock-onboarding-title');
        const textEl = document.getElementById('mock-onboarding-text');
        const nextBtn = document.getElementById('mock-onboarding-next');
        const skipBtn = document.getElementById('mock-onboarding-skip');
        if (!overlay || !spotlight || !tooltip) return;

        const testType = exam.dataset.testType || 'reading';
        const isListening = testType === 'listening';
        const steps = [
            {
                target: () => document.getElementById('timer-container') || document.querySelector('.mock-topbar-card'),
                title: 'Vaqt kuzatiladi',
                text: 'Timer imtihon vaqtini sanaydi. Javoblaringiz avtomatik saqlanadi — xotirjam ishlang.',
            },
            isListening ? {
                target: () => document.querySelector('.listening-audio-zone') || document.querySelector('.listening-parts-strip'),
                title: 'Audio tinglang',
                text: 'Progress chizig\'ini bosib kerakli joyga o\'ting. Part tugmalari orqali savollar bo\'yicha harakatlaning.',
            } : {
                target: () => document.querySelector('.mock-topbar-progress') || document.getElementById('progress-fill'),
                title: 'Jarayonni kuzating',
                text: 'Yuqoridagi progress bar qancha savolga javob berganingizni ko\'rsatadi.',
            },
            {
                target: () => document.getElementById('finish-test-btn') || document.querySelector('.mock-btn-submit'),
                title: 'Testni yakunlang',
                text: 'Tayyor bo\'lsangiz Yuborish tugmasini bosing. Javobsiz savollar ro\'yxatini ko\'rasiz.',
            },
        ];

        let stepIndex = 0;
        let positioned = false;

        function finishOnboarding() {
            overlay.hidden = true;
            overlay.setAttribute('aria-hidden', 'true');
            overlay.classList.remove('is-open');
            document.querySelectorAll('.mock-onboarding-target').forEach(el => {
                el.classList.remove('mock-onboarding-target');
            });
            try { localStorage.setItem(ONBOARDING_KEY, '1'); } catch (e) {}
            window.removeEventListener('resize', positionStep);
            window.removeEventListener('scroll', positionStep, true);
        }

        function positionStep() {
            const step = steps[stepIndex];
            const el = step.target();
            if (!el) return;
            document.querySelectorAll('.mock-onboarding-target').forEach(n => n.classList.remove('mock-onboarding-target'));
            el.classList.add('mock-onboarding-target');
            el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            const rect = el.getBoundingClientRect();
            const pad = 8;
            spotlight.style.top = (rect.top - pad) + 'px';
            spotlight.style.left = (rect.left - pad) + 'px';
            spotlight.style.width = (rect.width + pad * 2) + 'px';
            spotlight.style.height = (rect.height + pad * 2) + 'px';

            const ttW = tooltip.offsetWidth || 300;
            const ttH = tooltip.offsetHeight || 160;
            let top = rect.bottom + 14;
            let left = rect.left + rect.width / 2 - ttW / 2;
            if (top + ttH > window.innerHeight - 12) top = rect.top - ttH - 14;
            left = Math.max(12, Math.min(left, window.innerWidth - ttW - 12));
            top = Math.max(12, top);
            tooltip.style.top = top + 'px';
            tooltip.style.left = left + 'px';
            positioned = true;
        }

        function showStep(idx) {
            stepIndex = idx;
            const step = steps[idx];
            if (stepEl) stepEl.textContent = (idx + 1) + ' / ' + steps.length;
            if (titleEl) titleEl.textContent = step.title;
            if (textEl) textEl.textContent = step.text;
            if (nextBtn) nextBtn.textContent = idx === steps.length - 1 ? 'Tushundim' : 'Keyingi';
            requestAnimationFrame(() => {
                positionStep();
                if (!positioned) setTimeout(positionStep, 120);
            });
        }

        showStep(0);
        overlay.hidden = false;
        overlay.setAttribute('aria-hidden', 'false');
        overlay.classList.add('is-open');
        window.addEventListener('resize', positionStep);
        window.addEventListener('scroll', positionStep, true);

        nextBtn?.addEventListener('click', () => {
            if (stepIndex >= steps.length - 1) finishOnboarding();
            else showStep(stepIndex + 1);
        });
        skipBtn?.addEventListener('click', finishOnboarding);
        document.getElementById('mock-onboarding-backdrop')?.addEventListener('click', finishOnboarding);
    }

    document.getElementById('exam-mode-btn')?.addEventListener('click', () => {
        document.body.classList.toggle('mock-exam-fullscreen');
    });

    document.getElementById('pause-btn')?.addEventListener('click', () => {
        isPaused = !isPaused;
        const icon = document.getElementById('pause-icon');
        const label = document.getElementById('pause-label');
        if (icon) icon.className = isPaused ? 'fas fa-play' : 'fas fa-pause';
        if (label) label.textContent = isPaused ? 'Davom ettirish' : "To'xtatish";
        if (audioEl) {
            if (isPaused) audioEl.pause();
            else audioEl.play().catch(() => {});
        }
    });

    exam.querySelectorAll('textarea[data-question-id]').forEach(ta => {
        ta.addEventListener('input', () => updateEssayCount(ta));
    });

    exam.addEventListener('change', updateProgress);
    exam.addEventListener('change', (e) => {
        if (e.target && e.target.classList && e.target.classList.contains('mock-matching-select')) {
            updateProgress();
        }
    });
    exam.addEventListener('input', () => {
        updateProgress();
        clearTimeout(window._mockSaveTimer);
        window._mockSaveTimer = setTimeout(() => saveProgress(false), 2000);
    });

    document.getElementById('finish-test-btn')?.addEventListener('click', openSubmitModal);
    document.getElementById('confirm-submit-btn')?.addEventListener('click', finishTest);
    document.querySelectorAll('[data-close-submit]').forEach(el => {
        el.addEventListener('click', closeSubmitModal);
    });
    document.addEventListener('keydown', (e) => {
        const modal = document.getElementById('submit-modal');
        if (e.key === 'Escape' && modal && !modal.hidden) closeSubmitModal();
    });

    document.getElementById('mock-tip-dismiss')?.addEventListener('click', () => {
        const bar = document.getElementById('mock-tip-bar');
        if (bar) bar.classList.add('is-dismissed');
        try { sessionStorage.setItem('mock_tip_dismissed_' + testId, '1'); } catch (err) {}
    });
    try {
        if (sessionStorage.getItem('mock_tip_dismissed_' + testId)) {
            document.getElementById('mock-tip-bar')?.classList.add('is-dismissed');
        }
    } catch (err) {}

    const timerEl = document.getElementById('exam-timer');
    const timerPill = document.getElementById('timer-container');
    let timeUpHandled = false;
    function tick() {
        if (isPaused) return;
        if (secondsLeft <= 0) {
            if (!timeUpHandled) {
                timeUpHandled = true;
                openSubmitModal({ timeUp: true });
            }
            return;
        }
        const m = Math.floor(secondsLeft / 60), s = secondsLeft % 60;
        if (timerEl) timerEl.textContent = m + ':' + String(s).padStart(2, '0');
        if (timerPill) {
            timerPill.classList.toggle('warning', secondsLeft <= 300 && secondsLeft > 60);
            timerPill.classList.toggle('danger', secondsLeft <= 60);
        }
        secondsLeft -= 1;
    }
    tick();
    timerInterval = setInterval(tick, 1000);

    restoreAnswers();

    const btns = getAllNavButtons();
    if (btns.length) {
        updateCurrentQuestionLabel(btns[0].dataset.order || '1');
    }

    const restoredCount = Object.values(savedAnswers).filter(v => isAnswered(v)).length;
    if (restoredCount > 0) {
        setTimeout(() => toast('Oldingi javoblaringiz tiklandi — qayerdan to\'xtagan bo\'lsangiz, shu yerdan davom eting.', 'info', 'Xush kelibsiz'), 600);
    } else {
        setTimeout(initOnboarding, 400);
    }
})();
