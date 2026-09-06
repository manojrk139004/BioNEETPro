/**
 * BioNEETPro V2 — School & College Assessment Ecosystem Client Controller
 * Powers:
 * 1. Role-aware authentication & portal routing (SUPER_ADMIN, TEACHER, STUDENT)
 * 2. Canonical Class 11 & Class 12 cascading curriculum selector
 * 3. Teacher Portal (Assessment Lifecycle, Builder Wizard, AI MCQ generation, Results)
 * 4. Student Upcoming Tests & Live Scheduled Exam Taking Hall
 * 5. Admin Teacher Management (Onboard, status update, governance)
 * 6. Global Floating Multi-Role AI Assistant Widget
 */

(function() {
  'use strict';

  window.V2 = window.V2 || {};

  // Resolve backend base URL
  function getBackendUrl() {
    if (window.BIONEET_AI_BACKEND_URL) return window.BIONEET_AI_BACKEND_URL;
    var host = window.location.hostname || '';
    if (host === 'localhost' || host === '127.0.0.1' || !host) {
      return 'http://' + (host || '127.0.0.1') + ':5000';
    }
    return window.location.origin;
  }

  // Unified authenticated API fetch
  async function apiFetch(path, options) {
    options = options || {};
    options.headers = options.headers || {};
    if (!options.headers['Content-Type'] && !(options.body instanceof FormData)) {
      options.headers['Content-Type'] = 'application/json';
    }
    try {
      if (window.auth && window.auth.currentUser && window.auth.currentUser.getIdToken) {
        var idTok = await window.auth.currentUser.getIdToken();
        if (idTok) options.headers['Authorization'] = 'Bearer ' + idTok;
      }
    } catch (e) {
      console.warn("Could not attach auth token:", e);
    }
    var base = getBackendUrl();
    var url = path.startsWith('http') ? path : (base + path);
    return fetch(url, options);
  }
  V2.apiFetch = apiFetch;

  // =========================================================================
  // 1. CANONICAL CURRICULUM CONTROLLER
  // =========================================================================
  window.CURRICULUM_DATA = null;

  async function fetchCurriculum() {
    if (window.CURRICULUM_DATA) return window.CURRICULUM_DATA;
    try {
      var res = await apiFetch('/api/curriculum');
      if (res.ok) {
        var data = await res.json();
        window.CURRICULUM_DATA = data;
        return data;
      }
    } catch (e) {
      console.warn("Error loading curriculum:", e);
    }
    return null;
  }
  V2.fetchCurriculum = fetchCurriculum;

  async function populateCurriculumSelectors(classSelId, unitSelId, chapSelId, onSelectCb) {
    var classSel = document.getElementById(classSelId);
    var unitSel = document.getElementById(unitSelId);
    var chapSel = document.getElementById(chapSelId);
    if (!classSel) return;

    var cur = await fetchCurriculum();
    if (!cur || !cur.classes) return;

    // Populate classes
    classSel.innerHTML = '<option value="">-- Select Class --</option>' +
      cur.classes.map(function(c) {
        return '<option value="' + c.id + '">' + c.name + '</option>';
      }).join('');

    classSel.onchange = function() {
      var selectedClassId = classSel.value;
      if (unitSel) {
        unitSel.innerHTML = '<option value="">-- Select Unit --</option>';
        if (selectedClassId) {
          var cls = cur.classes.find(function(c) { return c.id === selectedClassId; });
          if (cls && cls.units) {
            cls.units.forEach(function(u) {
              unitSel.innerHTML += '<option value="' + u.id + '">' + u.name + '</option>';
            });
          }
        }
      }
      if (chapSel) {
        chapSel.innerHTML = '<option value="">-- Select Chapter --</option>';
        if (selectedClassId) {
          var filteredChaps = cur.chapters_flat.filter(function(ch) { return ch.class_id === selectedClassId; });
          filteredChaps.forEach(function(ch) {
            chapSel.innerHTML += '<option value="' + ch.id + '">' + ch.name + '</option>';
          });
        }
      }
      if (onSelectCb) onSelectCb();
    };

    if (unitSel && chapSel) {
      unitSel.onchange = function() {
        var selectedClassId = classSel.value;
        var selectedUnitId = unitSel.value;
        chapSel.innerHTML = '<option value="">-- Select Chapter --</option>';
        if (selectedClassId) {
          var cls = cur.classes.find(function(c) { return c.id === selectedClassId; });
          if (cls) {
            if (selectedUnitId) {
              var u = cls.units.find(function(item) { return item.id === selectedUnitId; });
              if (u && u.chapters) {
                u.chapters.forEach(function(ch) {
                  chapSel.innerHTML += '<option value="' + ch.id + '">' + ch.name + '</option>';
                });
              }
            } else {
              var filtered = cur.chapters_flat.filter(function(ch) { return ch.class_id === selectedClassId; });
              filtered.forEach(function(ch) {
                chapSel.innerHTML += '<option value="' + ch.id + '">' + ch.name + '</option>';
              });
            }
          }
        }
        if (onSelectCb) onSelectCb();
      };

      chapSel.onchange = function() {
        if (onSelectCb) onSelectCb();
      };
    }
  }
  V2.populateCurriculumSelectors = populateCurriculumSelectors;

  // =========================================================================
  // 2. STUDENT UPCOMING & ACTIVE TESTS
  // =========================================================================
  var upcomingTimerHandle = null;

  async function loadStudentUpcomingTests() {
    var box = document.getElementById('studentUpcomingContainer');
    if (!box) return;

    box.innerHTML = '<div style="text-align:center;padding:24px;color:var(--muted)">⏳ Checking for upcoming & active assessments...</div>';

    try {
      var res = await apiFetch('/api/assessments/upcoming');
      if (!res.ok) throw new Error("Could not fetch upcoming tests");
      var data = await res.json();
      var upcoming = data.upcoming_assessments || [];

      // Also get all published tests to show live tests
      var allRes = await apiFetch('/api/assessments');
      var allTests = [];
      if (allRes.ok) {
        var allData = await allRes.json();
        allTests = allData.assessments || [];
      }

      // Merge and deduplicate by ID
      var testMap = {};
      allTests.forEach(function(t) { testMap[t.id] = t; });
      upcoming.forEach(function(t) { testMap[t.id] = t; });
      var mergedList = Object.values(testMap);

      // Filter to relevant for student: LIVE, UPCOMING, RESULTS_AVAILABLE, or recent CLOSED
      var visible = mergedList.filter(function(t) {
        return t.status !== 'DRAFT';
      });

      if (visible.length === 0) {
        box.innerHTML = '<div style="text-align:center;padding:32px 16px;color:var(--muted)">' +
          '<div style="font-size:2rem;margin-bottom:8px">🎉</div>' +
          '<p style="font-weight:700;margin-bottom:4px">No scheduled tests right now</p>' +
          '<p style="font-size:0.8rem">Check back soon or practice with instant Mock Tests!</p>' +
          '</div>';
        return;
      }

      renderUpcomingCards(box, visible);

      // Start live countdown ticker
      if (upcomingTimerHandle) clearInterval(upcomingTimerHandle);
      upcomingTimerHandle = setInterval(function() {
        updateUpcomingCountdowns();
      }, 1000);

    } catch (e) {
      console.warn("Error loading upcoming tests:", e);
      box.innerHTML = '<div style="text-align:center;padding:20px;color:var(--red)">' +
        'Unable to load scheduled assessments right now. <button class="btn btn-outline btn-sm" onclick="loadStudentUpcomingTests()">Retry</button>' +
        '</div>';
    }
  }
  window.loadStudentUpcomingTests = loadStudentUpcomingTests;

  function renderUpcomingCards(box, tests) {
    var html = '<div class="grid g2" style="gap:16px">';
    tests.forEach(function(t) {
      var statusBadge = getStatusBadge(t.status);
      var typeLabel = (t.type || 'TEST').replace(/_/g, ' ');
      var chapName = t.chapter_name || (t.chapter_id ? t.chapter_id.toUpperCase() : 'NEET Biology');
      var qCount = (t.questions || []).length;
      var duration = t.duration_minutes || 30;

      var actionBtn = '';
      if (t.has_submitted) {
        actionBtn = '<button class="btn btn-sm btn-outline" onclick="viewMyAssessmentResult(\'' + t.id + '\')">✅ Result: ' + (t.my_score !== undefined ? t.my_score + ' pts' : 'Submitted') + '</button>';
      } else if (t.status === 'LIVE') {
        actionBtn = '<button class="btn btn-sm btn-primary" onclick="startScheduledAssessment(\'' + t.id + '\')">▶️ Start Live Test</button>';
      } else if (t.status === 'UPCOMING') {
        actionBtn = '<button class="btn btn-sm btn-ghost" disabled>⏳ Starts Soon</button>';
      } else if (t.status === 'RESULTS_AVAILABLE') {
        actionBtn = '<button class="btn btn-sm btn-outline" onclick="viewMyAssessmentResult(\'' + t.id + '\')">📊 View Results</button>';
      } else {
        actionBtn = '<button class="btn btn-sm btn-ghost" disabled>Closed</button>';
      }

      html += '<div class="card" style="border:1px solid var(--bdr);border-left:4px solid ' + getStatusColor(t.status) + ';padding:16px;display:flex;flex-direction:column;justify-content:space-between">' +
        '<div>' +
          '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">' +
            '<span class="badge" style="background:#f3f4f6;color:var(--ink);font-weight:700;font-size:0.7rem">' + typeLabel + '</span>' +
            statusBadge +
          '</div>' +
          '<h4 style="font-weight:800;font-size:0.95rem;margin-bottom:4px">' + escapeHtml(t.title) + '</h4>' +
          '<p style="font-size:0.75rem;color:var(--muted);margin-bottom:8px">📖 ' + escapeHtml(chapName) + ' • ' + qCount + ' Questions • ' + duration + ' mins</p>' +
        '</div>' +
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;padding-top:10px;border-top:1px solid #eee">' +
          '<div class="v2-countdown-badge" data-start="' + (t.start_at || '') + '" data-end="' + (t.end_at || '') + '" data-status="' + t.status + '" style="font-size:0.75rem;font-weight:700">--:--</div>' +
          '<div>' + actionBtn + '</div>' +
        '</div>' +
      '</div>';
    });
    html += '</div>';
    box.innerHTML = html;
    updateUpcomingCountdowns();
  }

  function getStatusBadge(status) {
    var s = (status || '').toUpperCase();
    if (s === 'LIVE') return '<span class="badge" style="background:#dcfce7;color:#15803d;font-weight:800;animation:pulse 2s infinite">🟢 LIVE NOW</span>';
    if (s === 'UPCOMING') return '<span class="badge" style="background:#fef9c3;color:#a16207;font-weight:700">⏳ UPCOMING</span>';
    if (s === 'PUBLISHED') return '<span class="badge" style="background:#e0e7ff;color:#4338ca;font-weight:700">📅 SCHEDULED</span>';
    if (s === 'RESULTS_AVAILABLE') return '<span class="badge" style="background:#e0f2fe;color:#0369a1;font-weight:700">📊 RESULTS OUT</span>';
    if (s === 'CLOSED') return '<span class="badge" style="background:#f3f4f6;color:#6b7280;font-weight:700">🔒 CLOSED</span>';
    return '<span class="badge" style="background:#f3f4f6;color:#6b7280">' + s + '</span>';
  }

  function getStatusColor(status) {
    var s = (status || '').toUpperCase();
    if (s === 'LIVE') return 'var(--green)';
    if (s === 'UPCOMING') return 'var(--y)';
    if (s === 'PUBLISHED') return 'var(--blue)';
    if (s === 'RESULTS_AVAILABLE') return 'var(--purple)';
    return '#9ca3af';
  }

  function updateUpcomingCountdowns() {
    var elements = document.querySelectorAll('.v2-countdown-badge');
    var now = Date.now();
    elements.forEach(function(el) {
      var start = el.getAttribute('data-start');
      var end = el.getAttribute('data-end');
      var status = el.getAttribute('data-status');

      if (status === 'LIVE' && end) {
        var endMs = new Date(end).getTime();
        var diff = endMs - now;
        if (diff > 0) {
          el.innerHTML = '<span style="color:var(--green)">Ends in ' + formatDuration(diff) + '</span>';
        } else {
          el.innerHTML = '<span style="color:var(--muted)">Ending soon</span>';
        }
      } else if (status === 'UPCOMING' && start) {
        var startMs = new Date(start).getTime();
        var diff = startMs - now;
        if (diff > 0) {
          el.innerHTML = '<span style="color:var(--orange)">Starts in ' + formatDuration(diff) + '</span>';
        } else {
          el.innerHTML = '<span style="color:var(--green)">Starting now...</span>';
        }
      } else if (status === 'RESULTS_AVAILABLE') {
        el.innerHTML = '<span style="color:var(--blue)">Score Available</span>';
      } else {
        el.innerHTML = '<span style="color:var(--muted)">Scheduled</span>';
      }
    });
  }

  function formatDuration(ms) {
    var totalSecs = Math.max(0, Math.floor(ms / 1000));
    var hours = Math.floor(totalSecs / 3600);
    var mins = Math.floor((totalSecs % 3600) / 60);
    var secs = totalSecs % 60;
    if (hours > 24) {
      var days = Math.floor(hours / 24);
      return days + 'd ' + (hours % 24) + 'h';
    }
    if (hours > 0) {
      return hours + 'h ' + (mins < 10 ? '0' : '') + mins + 'm';
    }
    return mins + 'm ' + (secs < 10 ? '0' : '') + secs + 's';
  }

  // =========================================================================
  // 3. LIVE SCHEDULED ASSESSMENT TAKING HALL
  // =========================================================================
  var activeExam = null;
  var examTimerInterval = null;

  async function startScheduledAssessment(assessmentId) {
    try {
      var res = await apiFetch('/api/assessments/' + assessmentId);
      if (!res.ok) {
        var err = await res.json();
        alert(err.error || "Cannot access this test right now.");
        return;
      }
      var data = await res.json();
      var asmt = data.assessment;

      if (!asmt || !asmt.questions || asmt.questions.length === 0) {
        alert("This assessment has no questions configured.");
        return;
      }

      if (asmt.has_submitted) {
        alert("You have already submitted this assessment.");
        viewMyAssessmentResult(assessmentId);
        return;
      }

      if (!confirm("Are you ready to begin " + asmt.title + "?\nDuration: " + asmt.duration_minutes + " mins. Timer starts immediately!")) {
        return;
      }

      activeExam = {
        asmt: asmt,
        currentIdx: 0,
        answers: {},
        marked: {},
        startTime: Date.now(),
        durationSeconds: (asmt.duration_minutes || 30) * 60,
        remainingSeconds: (asmt.duration_minutes || 30) * 60,
      };

      // Open live assessment page
      if (typeof window.go === 'function') {
        window.go('assessment-take');
      }

      renderExamUI();

      if (examTimerInterval) clearInterval(examTimerInterval);
      examTimerInterval = setInterval(function() {
        if (!activeExam) return;
        activeExam.remainingSeconds--;
        updateExamTimerDisplay();
        if (activeExam.remainingSeconds <= 0) {
          clearInterval(examTimerInterval);
          alert("Time is up! Submitting your answers automatically...");
          submitActiveExam(true);
        }
      }, 1000);

    } catch (e) {
      console.warn("Failed to start assessment:", e);
      alert("Error starting assessment: " + e.message);
    }
  }
  window.startScheduledAssessment = startScheduledAssessment;

  function renderExamUI() {
    if (!activeExam) return;
    var asmt = activeExam.asmt;

    document.getElementById('examTitleHeader').textContent = asmt.title;
    document.getElementById('examMetaHeader').textContent = (asmt.type || 'ASSESSMENT').replace(/_/g, ' ') + ' • ' + (asmt.chapter_name || 'NEET Biology');

    renderExamQuestion(activeExam.currentIdx);
    renderExamPalette();
    updateExamTimerDisplay();
  }

  function renderExamQuestion(idx) {
    if (!activeExam) return;
    activeExam.currentIdx = idx;
    var q = activeExam.asmt.questions[idx];
    var total = activeExam.asmt.questions.length;

    document.getElementById('examQIndexText').textContent = 'Question ' + (idx + 1) + ' of ' + total;
    document.getElementById('examQuestionText').textContent = q.question;

    var optsBox = document.getElementById('examOptionsContainer');
    optsBox.innerHTML = '';

    var selectedOpt = activeExam.answers[idx];

    q.options.forEach(function(optText, optIdx) {
      var isChecked = selectedOpt === optIdx;
      var optDiv = document.createElement('div');
      optDiv.className = 'exam-opt-item ' + (isChecked ? 'selected' : '');
      optDiv.style.cssText = 'padding:14px 18px;margin-bottom:10px;border-radius:var(--rs);border:2px solid ' + (isChecked ? 'var(--blue)' : 'var(--bdr)') + ';background:' + (isChecked ? '#eff6ff' : '#fff') + ';cursor:pointer;display:flex;align-items:center;gap:12px;transition:all .15s';
      optDiv.innerHTML = '<div style="width:24px;height:24px;border-radius:50%;border:2px solid ' + (isChecked ? 'var(--blue)' : '#cbd5e1') + ';background:' + (isChecked ? 'var(--blue)' : '#fff') + ';display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.75rem;color:' + (isChecked ? '#fff' : 'var(--muted)') + '">' +
        String.fromCharCode(65 + optIdx) +
        '</div>' +
        '<div style="font-size:0.92rem;font-weight:500">' + escapeHtml(optText) + '</div>';

      optDiv.onclick = function() {
        activeExam.answers[idx] = optIdx;
        renderExamQuestion(idx);
        renderExamPalette();
      };
      optsBox.appendChild(optDiv);
    });

    // Update button states
    var prevBtn = document.getElementById('examPrevBtn');
    var nextBtn = document.getElementById('examNextBtn');
    if (prevBtn) prevBtn.disabled = (idx === 0);
    if (nextBtn) nextBtn.textContent = (idx === total - 1) ? 'Review & Submit' : 'Next Question →';

    var markBtn = document.getElementById('examMarkBtn');
    if (markBtn) {
      var isMarked = activeExam.marked[idx];
      markBtn.textContent = isMarked ? '★ Marked for Review' : '☆ Mark for Review';
      markBtn.style.color = isMarked ? 'var(--orange)' : 'var(--muted)';
    }

    renderExamPalette();
  }

  function renderExamPalette() {
    if (!activeExam) return;
    var pal = document.getElementById('examQuestionPalette');
    if (!pal) return;

    pal.innerHTML = '';
    var total = activeExam.asmt.questions.length;

    for (var i = 0; i < total; i++) {
      var isCur = (i === activeExam.currentIdx);
      var isAns = (activeExam.answers[i] !== undefined);
      var isMarked = Boolean(activeExam.marked[i]);

      var bg = '#f3f4f6';
      var col = '#6b7280';
      var border = '#e5e7eb';

      if (isAns && isMarked) {
        bg = '#a855f7'; col = '#fff'; border = '#9333ea';
      } else if (isAns) {
        bg = '#22c55e'; col = '#fff'; border = '#16a34a';
      } else if (isMarked) {
        bg = '#f97316'; col = '#fff'; border = '#ea580c';
      }

      if (isCur) {
        border = '2px solid var(--ink)';
      } else {
        border = '1px solid ' + border;
      }

      var b = document.createElement('button');
      b.style.cssText = 'width:36px;height:36px;border-radius:8px;font-weight:700;font-size:0.8rem;background:' + bg + ';color:' + col + ';border:' + border + ';cursor:pointer';
      b.textContent = (i + 1);
      (function(targetIdx) {
        b.onclick = function() { renderExamQuestion(targetIdx); };
      })(i);

      pal.appendChild(b);
    }
  }

  function updateExamTimerDisplay() {
    var timerEl = document.getElementById('examTimerDisplay');
    if (!timerEl || !activeExam) return;
    var rem = Math.max(0, activeExam.remainingSeconds);
    var mins = Math.floor(rem / 60);
    var secs = rem % 60;
    var str = (mins < 10 ? '0' : '') + mins + ':' + (secs < 10 ? '0' : '') + secs;
    timerEl.textContent = str;
    if (rem < 300) {
      timerEl.style.color = 'var(--red)';
      timerEl.style.animation = 'pulse 1s infinite';
    } else {
      timerEl.style.color = 'var(--ink)';
      timerEl.style.animation = 'none';
    }
  }

  window.examPrevQuestion = function() {
    if (!activeExam || activeExam.currentIdx <= 0) return;
    renderExamQuestion(activeExam.currentIdx - 1);
  };

  window.examNextQuestion = function() {
    if (!activeExam) return;
    if (activeExam.currentIdx >= activeExam.asmt.questions.length - 1) {
      confirmAndSubmitExam();
    } else {
      renderExamQuestion(activeExam.currentIdx + 1);
    }
  };

  window.examClearResponse = function() {
    if (!activeExam) return;
    delete activeExam.answers[activeExam.currentIdx];
    renderExamQuestion(activeExam.currentIdx);
    renderExamPalette();
  };

  window.examToggleMark = function() {
    if (!activeExam) return;
    var cur = activeExam.currentIdx;
    activeExam.marked[cur] = !activeExam.marked[cur];
    renderExamQuestion(cur);
    renderExamPalette();
  };

  window.confirmAndSubmitExam = function() {
    if (!activeExam) return;
    var total = activeExam.asmt.questions.length;
    var answered = Object.keys(activeExam.answers).length;
    var unanswered = total - answered;

    var msg = "Assessment Summary:\n" +
      "• Total Questions: " + total + "\n" +
      "• Answered: " + answered + "\n" +
      "• Unanswered: " + unanswered + "\n\n" +
      "Are you sure you want to submit?";

    if (confirm(msg)) {
      submitActiveExam(false);
    }
  };

  async function submitActiveExam(isAuto) {
    if (!activeExam) return;
    if (examTimerInterval) clearInterval(examTimerInterval);

    var asmtId = activeExam.asmt.id;
    var answers = activeExam.answers;
    var timeSpent = Math.floor((Date.now() - activeExam.startTime) / 1000);

    try {
      var res = await apiFetch('/api/assessments/' + asmtId + '/submit', {
        method: 'POST',
        body: JSON.stringify({
          answers: answers,
          time_spent_seconds: timeSpent
        })
      });

      var data = await res.json();
      if (!res.ok) {
        alert(data.error || "Submission failed. Please check network connection.");
        return;
      }

      var maxM = data.max_marks || data.total_marks || data.totalMarks || (data.result && data.result.total_marks) || 0;
      alert("Test submitted successfully!\nScore: " + data.score + " / " + maxM + " (" + data.percentage + "%)\nYour mastery has been synced to your adaptive learner profile!");

      activeExam = null;
      if (typeof window.go === 'function') {
        window.go('dashboard');
        loadStudentUpcomingTests();
      }

    } catch (e) {
      console.warn("Submit error:", e);
      alert("Error submitting assessment: " + e.message);
    }
  }

  async function viewMyAssessmentResult(asmtId) {
    try {
      var res = await apiFetch('/api/assessments/' + asmtId + '/my-result');
      if (!res.ok) {
        alert("Result not yet released or submission not found.");
        return;
      }
      var data = await res.json();
      var r = data.result;
      var totalM = r.max_marks || r.total_marks || r.totalMarks || 0;

      var html = "Assessment Result for " + asmtId + ":\n" +
        "• Score: " + r.score + " / " + totalM + " (" + r.percentage + "%)\n" +
        "• Correct: " + (r.correct_count !== undefined ? r.correct_count : r.correct) + "\n" +
        "• Incorrect: " + (r.incorrect_count !== undefined ? r.incorrect_count : r.incorrect) + "\n" +
        "• Unattempted: " + (r.unattempted_count !== undefined ? r.unattempted_count : r.unattempted) + "\n" +
        "• Status: " + (r.passed ? "PASSED ✅" : "NEEDS REMEDIATION ⚠️") + "\n" +
        "• Rank: #" + (r.rank || 1);

      alert(html);
    } catch (e) {
      alert("Could not load result: " + e.message);
    }
  }
  window.viewMyAssessmentResult = viewMyAssessmentResult;

  // =========================================================================
  // 4. TEACHER PORTAL & ASSESSMENT BUILDER
  // =========================================================================
  var builderQuestions = [];

  function switchTeacherTab(tab) {
    ['assessments', 'builder', 'analytics'].forEach(function(t) {
      var navEl = document.getElementById('tNav' + capitalize(t));
      var viewEl = document.getElementById('tView' + capitalize(t));
      if (navEl) navEl.classList.toggle('active', t === tab);
      if (viewEl) viewEl.classList.toggle('hidden', t !== tab);
    });

    if (tab === 'assessments') loadTeacherAssessments();
    if (tab === 'builder') initAssessmentBuilder();
    if (tab === 'analytics') initTeacherAnalytics();
  }
  window.switchTeacherTab = switchTeacherTab;

  async function loadTeacherAssessments() {
    var listEl = document.getElementById('teacherAssessmentsList');
    if (!listEl) return;
    listEl.innerHTML = '<div style="text-align:center;padding:24px;color:var(--muted)">Loading assessments...</div>';

    try {
      var res = await apiFetch('/api/assessments');
      if (!res.ok) throw new Error("Could not load teacher assessments");
      var data = await res.json();
      var asmts = data.assessments || [];

      if (asmts.length === 0) {
        listEl.innerHTML = '<div style="text-align:center;padding:40px;color:var(--muted)">' +
          '<div style="font-size:2rem;margin-bottom:8px">📝</div>' +
          '<h3 style="font-weight:700">No assessments created yet</h3>' +
          '<p style="font-size:0.85rem;margin-bottom:16px">Use the Assessment Builder to craft your first test!</p>' +
          '<button class="btn btn-primary" onclick="switchTeacherTab(\'builder\')">+ Create Assessment</button>' +
          '</div>';
        return;
      }

      var html = '<table class="table" style="width:100%">' +
        '<thead><tr>' +
        '<th>Title</th><th>Type</th><th>Chapter / Unit</th><th>Questions</th><th>Status</th><th>Window</th><th>Actions</th>' +
        '</tr></thead><tbody>';

      asmts.forEach(function(a) {
        var statusBadge = getStatusBadge(a.status);
        var qCount = (a.questions || []).length;
        var chap = a.chapter_name || (a.chapter_id ? a.chapter_id.toUpperCase() : 'General');
        var typeStr = (a.type || '').replace(/_/g, ' ');

        var actionBtns = '';
        if (a.status === 'DRAFT') {
          actionBtns += '<button class="btn btn-sm btn-primary" style="margin-right:4px" onclick="transitionAssessmentStatus(\'' + a.id + '\', \'PUBLISHED\')">Publish</button>';
        } else if (a.status === 'PUBLISHED' || a.status === 'UPCOMING') {
          actionBtns += '<button class="btn btn-sm btn-outline" style="margin-right:4px" onclick="transitionAssessmentStatus(\'' + a.id + '\', \'LIVE\')">Go Live</button>';
        } else if (a.status === 'LIVE') {
          actionBtns += '<button class="btn btn-sm btn-outline" style="margin-right:4px" onclick="transitionAssessmentStatus(\'' + a.id + '\', \'CLOSED\')">Close Test</button>';
        } else if (a.status === 'CLOSED') {
          actionBtns += '<button class="btn btn-sm btn-primary" style="margin-right:4px" onclick="transitionAssessmentStatus(\'' + a.id + '\', \'RESULTS_AVAILABLE\')">Release Results</button>';
        }
        actionBtns += '<button class="btn btn-sm btn-ghost" onclick="viewTeacherAssessmentAnalytics(\'' + a.id + '\')">Analytics</button>';

        html += '<tr>' +
          '<td><strong>' + escapeHtml(a.title) + '</strong></td>' +
          '<td>' + typeStr + '</td>' +
          '<td>' + escapeHtml(chap) + '</td>' +
          '<td>' + qCount + '</td>' +
          '<td>' + statusBadge + '</td>' +
          '<td style="font-size:0.75rem">' + (a.start_at ? new Date(a.start_at).toLocaleDateString() : 'Immediate') + '</td>' +
          '<td>' + actionBtns + '</td>' +
          '</tr>';
      });

      html += '</tbody></table>';
      listEl.innerHTML = html;

    } catch (e) {
      listEl.innerHTML = '<div style="color:var(--red);padding:20px">Error loading assessments: ' + e.message + '</div>';
    }
  }
  window.loadTeacherAssessments = loadTeacherAssessments;

  async function transitionAssessmentStatus(asmtId, nextStatus) {
    if (!confirm("Confirm changing status of this test to " + nextStatus + "?")) return;
    try {
      var res = await apiFetch('/api/assessments/' + asmtId + '/status', {
        method: 'POST',
        body: JSON.stringify({ status: nextStatus })
      });
      var data = await res.json();
      if (!res.ok) {
        alert(data.error || "Status update failed.");
        return;
      }
      alert("Assessment status updated to " + nextStatus + "!");
      loadTeacherAssessments();
    } catch (e) {
      alert("Error: " + e.message);
    }
  }
  window.transitionAssessmentStatus = transitionAssessmentStatus;

  // Builder Wizard logic
  function initAssessmentBuilder() {
    populateCurriculumSelectors('bClassSelect', 'bUnitSelect', 'bChapSelect');
    builderQuestions = [];
    renderBuilderQuestions();

    // Default start/end dates
    var now = new Date();
    var tomorrow = new Date(now.getTime() + 24 * 3600 * 1000);
    var startInput = document.getElementById('bStartAt');
    var endInput = document.getElementById('bEndAt');
    if (startInput && !startInput.value) {
      startInput.value = now.toISOString().slice(0, 16);
    }
    if (endInput && !endInput.value) {
      endInput.value = tomorrow.toISOString().slice(0, 16);
    }
  }

  async function generateAiAssessmentQuestions() {
    var chapSel = document.getElementById('bChapSelect');
    var diffSel = document.getElementById('bDiffSelect');
    var countInput = document.getElementById('bCountInput');
    var promptInput = document.getElementById('bCustomPrompt');

    var chapter = chapSel ? chapSel.value : '';
    var difficulty = diffSel ? diffSel.value : 'medium';
    var count = countInput ? parseInt(countInput.value, 10) || 5 : 5;
    var customPrompt = promptInput ? promptInput.value.trim() : '';

    if (!chapter) {
      alert("Please select a canonical Chapter before generating questions.");
      return;
    }

    var btn = document.getElementById('bGenerateAiBtn');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Curating MCQs...'; }

    try {
      var res = await apiFetch('/api/mcqs/ai-generate', {
        method: 'POST',
        body: JSON.stringify({
          chapter: chapter,
          difficulty: difficulty,
          count: count,
          custom_prompt: customPrompt
        })
      });

      var data = await res.json();
      if (!res.ok) {
        alert(data.error || "Failed to generate questions.");
        return;
      }

      var incoming = data.questions || [];
      incoming.forEach(function(q) {
        builderQuestions.push(q);
      });

      renderBuilderQuestions();
      alert("Added " + incoming.length + " curated questions to your draft. Please review and edit before publishing!");

    } catch (e) {
      alert("Error generating questions: " + e.message);
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '🤖 Generate with AI'; }
    }
  }
  window.generateAiAssessmentQuestions = generateAiAssessmentQuestions;

  function renderBuilderQuestions() {
    var container = document.getElementById('builderQuestionsList');
    var countBadge = document.getElementById('builderQuestionsCount');
    if (!container) return;

    if (countBadge) {
      countBadge.textContent = builderQuestions.length + ' Questions (' + (builderQuestions.length * 4) + ' Marks)';
    }

    if (builderQuestions.length === 0) {
      container.innerHTML = '<div style="text-align:center;padding:32px;color:var(--muted);background:#fafafa;border:1px dashed var(--bdr);border-radius:var(--rs)">' +
        '<p style="font-weight:700">No questions added to this test yet</p>' +
        '<p style="font-size:0.8rem">Click "Generate with AI" or "+ Add Custom Question" above.</p>' +
        '</div>';
      return;
    }

    var html = '';
    builderQuestions.forEach(function(q, qIdx) {
      var isPending = (q.status === 'PENDING_REVIEW');
      var statusTag = isPending
        ? '<span class="badge" style="background:#fef3c7;color:#b45309">Pending Review</span>'
        : '<span class="badge" style="background:#dcfce7;color:#15803d">Approved</span>';

      html += '<div class="card" style="margin-bottom:12px;padding:16px;border:1px solid ' + (isPending ? 'var(--orange)' : 'var(--bdr)') + '">' +
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">' +
          '<div style="display:flex;align-items:center;gap:8px">' +
            '<span style="font-weight:800;font-size:0.85rem">Q' + (qIdx + 1) + '.</span>' +
            statusTag +
            '<span class="badge" style="background:#f3f4f6;font-size:0.7rem">' + (q.difficulty || 'medium') + '</span>' +
          '</div>' +
          '<div style="display:flex;gap:6px">' +
            (isPending ? '<button class="btn btn-sm btn-outline" onclick="approveSingleBuilderQuestion(' + qIdx + ')">✓ Approve</button>' : '') +
            '<button class="btn btn-sm btn-ghost" style="color:var(--red)" onclick="deleteBuilderQuestion(' + qIdx + ')">✕ Remove</button>' +
          '</div>' +
        '</div>' +
        '<textarea class="ft" style="width:100%;margin-bottom:8px;font-size:0.88rem" onchange="updateBuilderQuestionText(' + qIdx + ', this.value)">' + escapeHtml(q.question) + '</textarea>' +
        '<div class="grid g2" style="gap:8px;margin-bottom:8px">';

      q.options.forEach(function(optText, optIdx) {
        var isCorrect = (q.correct_index === optIdx);
        html += '<div style="display:flex;align-items:center;gap:6px;background:' + (isCorrect ? '#f0fdf4' : '#fff') + ';padding:6px;border:1px solid ' + (isCorrect ? 'var(--green)' : '#e5e7eb') + ';border-radius:var(--rs)">' +
          '<input type="radio" name="bCorrOpt_' + qIdx + '" ' + (isCorrect ? 'checked' : '') + ' onchange="updateBuilderQuestionCorrect(' + qIdx + ', ' + optIdx + ')">' +
          '<span style="font-weight:700;font-size:0.75rem">' + String.fromCharCode(65 + optIdx) + ':</span>' +
          '<input type="text" class="fi" style="flex:1;padding:4px 8px;font-size:0.82rem" value="' + escapeHtml(optText) + '" onchange="updateBuilderQuestionOption(' + qIdx + ', ' + optIdx + ', this.value)">' +
          '</div>';
      });

      html += '</div>' +
        '<input type="text" class="fi" placeholder="NCERT Explanation..." style="font-size:0.8rem" value="' + escapeHtml(q.explanation || '') + '" onchange="updateBuilderQuestionExplanation(' + qIdx + ', this.value)">' +
        '</div>';
    });

    container.innerHTML = html;
  }

  window.updateBuilderQuestionText = function(idx, val) {
    if (builderQuestions[idx]) builderQuestions[idx].question = val;
  };
  window.updateBuilderQuestionOption = function(qIdx, optIdx, val) {
    if (builderQuestions[qIdx] && builderQuestions[qIdx].options) {
      builderQuestions[qIdx].options[optIdx] = val;
    }
  };
  window.updateBuilderQuestionCorrect = function(qIdx, optIdx) {
    if (builderQuestions[qIdx]) {
      builderQuestions[qIdx].correct_index = optIdx;
      renderBuilderQuestions();
    }
  };
  window.updateBuilderQuestionExplanation = function(idx, val) {
    if (builderQuestions[idx]) builderQuestions[idx].explanation = val;
  };
  window.deleteBuilderQuestion = function(idx) {
    builderQuestions.splice(idx, 1);
    renderBuilderQuestions();
  };
  window.approveSingleBuilderQuestion = function(idx) {
    if (builderQuestions[idx]) {
      builderQuestions[idx].status = 'APPROVED';
      renderBuilderQuestions();
    }
  };

  async function approveAllBuilderQuestions() {
    if (builderQuestions.length === 0) return;
    try {
      var res = await apiFetch('/api/mcqs/approve', {
        method: 'POST',
        body: JSON.stringify({ questions: builderQuestions })
      });
      if (res.ok) {
        builderQuestions.forEach(function(q) { q.status = 'APPROVED'; });
        renderBuilderQuestions();
        alert("All questions have been approved and validated!");
      }
    } catch (e) {
      alert("Approval error: " + e.message);
    }
  }
  window.approveAllBuilderQuestions = approveAllBuilderQuestions;

  function openCustomQuestionModal() {
    var qText = prompt("Enter question text:");
    if (!qText) return;
    var a = prompt("Option A:") || "";
    var b = prompt("Option B:") || "";
    var c = prompt("Option C:") || "";
    var d = prompt("Option D:") || "";
    var corrStr = prompt("Correct option letter (A, B, C, or D):", "A") || "A";
    var corrIdx = "ABCD".indexOf(corrStr.toUpperCase().trim());
    if (corrIdx === -1) corrIdx = 0;

    var chapSel = document.getElementById('bChapSelect');
    var chapter = chapSel ? chapSel.value : 'General Biology';

    builderQuestions.push({
      id: 'custom_' + Date.now(),
      question: qText,
      options: [a, b, c, d],
      correct_index: corrIdx,
      chapter: chapter,
      difficulty: 'medium',
      explanation: 'NCERT Reference',
      is_ai_generated: false,
      status: 'APPROVED'
    });
    renderBuilderQuestions();
  }
  window.openCustomQuestionModal = openCustomQuestionModal;

  async function saveAssessment(initialStatus) {
    var title = (document.getElementById('bTitleInput').value || '').trim();
    var type = document.getElementById('bTypeSelect').value;
    var classId = document.getElementById('bClassSelect').value;
    var chapterId = document.getElementById('bChapSelect').value;
    var duration = parseInt(document.getElementById('bDurationInput').value, 10) || 30;
    var startAt = document.getElementById('bStartAt').value;
    var endAt = document.getElementById('bEndAt').value;

    if (!title) {
      alert("Please enter a test title.");
      return;
    }
    if (builderQuestions.length === 0) {
      alert("Please add at least 1 question to this assessment.");
      return;
    }

    var chapName = '';
    if (window.CURRICULUM_DATA && window.CURRICULUM_DATA.chapters_flat) {
      var found = window.CURRICULUM_DATA.chapters_flat.find(function(ch) { return ch.id === chapterId; });
      if (found) chapName = found.name;
    }

    var payload = {
      title: title,
      type: type,
      class_id: classId,
      chapter_id: chapterId,
      chapter_name: chapName,
      duration_minutes: duration,
      start_at: startAt ? new Date(startAt).toISOString() : null,
      end_at: endAt ? new Date(endAt).toISOString() : null,
      total_marks: builderQuestions.length * 4,
      passing_marks: Math.floor(builderQuestions.length * 4 * 0.5),
      questions: builderQuestions,
      status: initialStatus || 'DRAFT'
    };

    try {
      var res = await apiFetch('/api/assessments', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      var data = await res.json();
      if (!res.ok) {
        alert(data.error || "Failed to save assessment.");
        return;
      }

      alert("Assessment successfully created as " + (initialStatus || 'DRAFT') + "!");
      switchTeacherTab('assessments');
    } catch (e) {
      alert("Error: " + e.message);
    }
  }
  window.saveAssessment = saveAssessment;

  // Analytics & Results
  async function initTeacherAnalytics() {
    var sel = document.getElementById('analyticsAsmtSelect');
    if (!sel) return;
    try {
      var res = await apiFetch('/api/assessments');
      if (res.ok) {
        var data = await res.json();
        var list = data.assessments || [];
        sel.innerHTML = '<option value="">-- Select Assessment --</option>' +
          list.map(function(a) {
            return '<option value="' + a.id + '">' + escapeHtml(a.title) + ' (' + (a.status) + ')</option>';
          }).join('');
      }
    } catch (e) {}
  }

  window.onTeacherAnalyticsSelect = function(asmtId) {
    if (asmtId) viewTeacherAssessmentAnalytics(asmtId);
  };

  async function viewTeacherAssessmentAnalytics(asmtId) {
    switchTeacherTab('analytics');
    var box = document.getElementById('teacherAnalyticsContent');
    if (!box) return;

    box.innerHTML = '<div style="text-align:center;padding:24px;color:var(--muted)">Loading class performance metrics...</div>';

    try {
      var res = await apiFetch('/api/assessments/' + asmtId + '/results');
      var data = await res.json();
      if (!res.ok) {
        box.innerHTML = '<div style="color:var(--red);padding:20px">' + (data.error || "Failed to load analytics.") + '</div>';
        return;
      }

      var stats = data.statistics || {};
      var subs = data.submissions || [];
      var qAnalysis = data.question_analysis || [];

      var html = '<div class="grid g4" style="margin-bottom:24px">' +
        '<div class="stat-card"><div class="stat-info"><h3 style="font-size:1.8rem">' + (stats.total_submissions || 0) + '</h3><p>Submissions</p></div></div>' +
        '<div class="stat-card"><div class="stat-info"><h3 style="font-size:1.8rem;color:var(--blue)">' + (stats.average_score || 0) + '</h3><p>Avg Score (pts)</p></div></div>' +
        '<div class="stat-card"><div class="stat-info"><h3 style="font-size:1.8rem;color:var(--green)">' + (stats.pass_percentage || 0) + '%</h3><p>Pass Rate</p></div></div>' +
        '<div class="stat-card"><div class="stat-info"><h3 style="font-size:1.8rem;color:var(--y)">' + (stats.highest_score || 0) + '</h3><p>Top Score</p></div></div>' +
        '</div>';

      // Student Leaderboard / Roster
      html += '<div class="card" style="margin-bottom:24px;padding:20px">' +
        '<h3 style="font-weight:800;font-size:1.1rem;margin-bottom:12px">🎓 Student Submissions Roster & Leaderboard</h3>';

      if (subs.length === 0) {
        html += '<p style="color:var(--muted);font-size:0.85rem">No student submissions yet for this test.</p>';
      } else {
        html += '<table class="table" style="width:100%">' +
          '<thead><tr><th>Rank</th><th>Student ID</th><th>Score</th><th>Percentage</th><th>Time Spent</th><th>Status</th></tr></thead><tbody>';
        subs.forEach(function(s) {
          html += '<tr>' +
            '<td><strong>#' + (s.rank || '-') + '</strong></td>' +
            '<td>' + escapeHtml(s.student_id) + '</td>' +
            '<td>' + s.score + ' / ' + s.max_marks + '</td>' +
            '<td>' + s.percentage + '%</td>' +
            '<td>' + Math.floor((s.time_spent_seconds || 0)/60) + 'm ' + ((s.time_spent_seconds || 0)%60) + 's</td>' +
            '<td>' + (s.passed ? '<span class="badge" style="background:#dcfce7;color:#15803d">Passed</span>' : '<span class="badge" style="background:#fee2e2;color:#b91c1c">Remediate</span>') + '</td>' +
            '</tr>';
        });
        html += '</tbody></table>';
      }
      html += '</div>';

      // Question breakdown
      if (qAnalysis.length > 0) {
        html += '<div class="card" style="padding:20px">' +
          '<h3 style="font-weight:800;font-size:1.1rem;margin-bottom:12px">🔬 Question-Level Misconception Analysis</h3>' +
          '<table class="table" style="width:100%">' +
          '<thead><tr><th>#</th><th>Question</th><th>% Correct</th><th>Class Mastery</th></tr></thead><tbody>';
        qAnalysis.forEach(function(qa) {
          var acc = qa.accuracy_pct || 0;
          var barColor = acc >= 70 ? 'var(--green)' : (acc >= 40 ? 'var(--y)' : 'var(--red)');
          html += '<tr>' +
            '<td>Q' + (qa.question_index + 1) + '</td>' +
            '<td style="font-size:0.85rem;max-width:400px">' + escapeHtml(qa.question_text) + '</td>' +
            '<td><strong>' + acc + '%</strong></td>' +
            '<td style="width:160px"><div class="pbar"><div class="pfill" style="width:' + acc + '%;background:' + barColor + '"></div></div></td>' +
            '</tr>';
        });
        html += '</tbody></table></div>';
      }

      box.innerHTML = html;

    } catch (e) {
      box.innerHTML = '<div style="color:var(--red);padding:20px">Error: ' + e.message + '</div>';
    }
  }
  window.viewTeacherAssessmentAnalytics = viewTeacherAssessmentAnalytics;

  // =========================================================================
  // 5. ADMIN TEACHER MANAGEMENT
  // =========================================================================
  async function loadAdminTeachers() {
    var box = document.getElementById('adminTeachersTableBody');
    if (!box) return;
    box.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--muted)">Loading faculty accounts...</td></tr>';

    try {
      var res = await apiFetch('/api/admin/teachers');
      if (!res.ok) throw new Error("Could not load teachers list");
      var data = await res.json();
      var teachers = data.teachers || [];

      var totalEl = document.getElementById('adminTotalTeachersCount');
      if (totalEl) totalEl.textContent = teachers.length;

      if (teachers.length === 0) {
        box.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:32px;color:var(--muted)">No teachers registered. Click "+ Onboard Teacher" to add your first faculty member.</td></tr>';
        return;
      }

      var html = '';
      teachers.forEach(function(t) {
        var statusColor = t.status === 'ACTIVE' ? '#15803d' : (t.status === 'SUSPENDED' ? '#b91c1c' : '#6b7280');
        var statusBg = t.status === 'ACTIVE' ? '#dcfce7' : (t.status === 'SUSPENDED' ? '#fee2e2' : '#f3f4f6');
        var statusBadge = '<span class="badge" style="background:' + statusBg + ';color:' + statusColor + ';font-weight:700">' + (t.status || 'ACTIVE') + '</span>';

        var toggleBtn = '';
        if (t.status === 'ACTIVE') {
          toggleBtn = '<button class="btn btn-sm btn-outline" style="margin-right:4px" onclick="setTeacherStatus(\'' + t.id + '\', \'INACTIVE\')">Deactivate</button>' +
            '<button class="btn btn-sm btn-ghost" style="color:var(--red)" onclick="setTeacherStatus(\'' + t.id + '\', \'SUSPENDED\')">Suspend</button>';
        } else {
          toggleBtn = '<button class="btn btn-sm btn-primary" onclick="setTeacherStatus(\'' + t.id + '\', \'ACTIVE\')">Activate</button>';
        }

        html += '<tr>' +
          '<td><strong>' + escapeHtml(t.name) + '</strong></td>' +
          '<td>' + escapeHtml(t.email) + '</td>' +
          '<td>' + escapeHtml(t.department || 'Biology') + '</td>' +
          '<td>' + escapeHtml((t.subjects || []).join(', ') || 'NEET Biology') + '</td>' +
          '<td>' + statusBadge + '</td>' +
          '<td>' + toggleBtn + '</td>' +
          '</tr>';
      });

      box.innerHTML = html;

    } catch (e) {
      box.innerHTML = '<tr><td colspan="6" style="color:var(--red);padding:16px">Error: ' + e.message + '</td></tr>';
    }
  }
  window.loadAdminTeachers = loadAdminTeachers;

  async function setTeacherStatus(teacherId, status) {
    if (!confirm("Are you sure you want to change this teacher's status to " + status + "?")) return;
    try {
      var res = await apiFetch('/api/admin/teachers/' + teacherId + '/status', {
        method: 'PATCH',
        body: JSON.stringify({ status: status })
      });
      if (res.ok) {
        alert("Teacher status updated to " + status);
        loadAdminTeachers();
      } else {
        var d = await res.json();
        alert(d.error || "Failed to update teacher status.");
      }
    } catch (e) {
      alert("Error: " + e.message);
    }
  }
  window.setTeacherStatus = setTeacherStatus;

  async function submitCreateTeacherModal() {
    var name = (document.getElementById('newTeacherName').value || '').trim();
    var email = (document.getElementById('newTeacherEmail').value || '').trim();
    var pass = (document.getElementById('newTeacherPassword').value || '').trim();
    var dept = (document.getElementById('newTeacherDept').value || '').trim();
    var sub = (document.getElementById('newTeacherSubjects').value || '').trim();
    var phone = (document.getElementById('newTeacherPhone').value || '').trim();

    if (!name || !email || !pass) {
      alert("Please enter Name, Email, and Password.");
      return;
    }

    var payload = {
      name: name,
      email: email,
      password: pass,
      department: dept || 'Biology',
      subjects: sub ? sub.split(',').map(function(s) { return s.trim(); }) : ['NEET Biology'],
      phone: phone
    };

    try {
      var res = await apiFetch('/api/admin/teachers', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      var data = await res.json();
      if (!res.ok) {
        alert(data.error || "Failed to create teacher account.");
        return;
      }

      alert("Teacher onboarded successfully!\nTeacher ID: " + data.teacher.id);
      if (typeof window.closeModal === 'function') window.closeModal('teacherCreateModal');
      loadAdminTeachers();

      // Clear fields
      document.getElementById('newTeacherName').value = '';
      document.getElementById('newTeacherEmail').value = '';
      document.getElementById('newTeacherPassword').value = '';

    } catch (e) {
      alert("Error: " + e.message);
    }
  }
  window.submitCreateTeacherModal = submitCreateTeacherModal;

  // =========================================================================
  // 6. GLOBAL FLOATING AI ASSISTANT WIDGET
  // =========================================================================
  var assistantHistory = [];
  var isAssistantOpen = false;

  function toggleFloatingAssistant() {
    var win = document.getElementById('floatingAssistantWindow');
    if (!win) return;
    isAssistantOpen = !isAssistantOpen;
    win.classList.toggle('hidden', !isAssistantOpen);
    if (isAssistantOpen) {
      updateAssistantRole();
      var input = document.getElementById('floatingAssistantInput');
      if (input) input.focus();
    }
  }
  window.toggleFloatingAssistant = toggleFloatingAssistant;

  function updateAssistantRole() {
    var role = (window.DB && window.DB.userRole) ? window.DB.userRole : (window.DB && window.DB.isAdmin ? 'SUPER_ADMIN' : 'STUDENT');
    var badge = document.getElementById('floatingAssistantRoleBadge');
    var title = document.getElementById('floatingAssistantTitle');
    var chips = document.getElementById('floatingAssistantChips');
    if (!badge || !title) return;

    if (role === 'TEACHER') {
      badge.textContent = 'Faculty Advisor';
      badge.style.background = '#dbeafe'; badge.style.color = '#1e40af';
      title.textContent = 'Prof. Sharma';
      if (chips) {
        chips.innerHTML = '<span class="v2-chip" onclick="sendFloatingChip(\'Suggest 5 high-yield MCQs for Class 11 Photosynthesis\')">Suggest 5 MCQs</span>' +
          '<span class="v2-chip" onclick="sendFloatingChip(\'How should I balance difficulty in a weekly test?\')">Test Balancing</span>' +
          '<span class="v2-chip" onclick="sendFloatingChip(\'What are common student traps in Genetics?\')">Genetics Traps</span>';
      }
    } else if (role === 'SUPER_ADMIN' || role === 'ADMIN') {
      badge.textContent = 'Operations Advisor';
      badge.style.background = '#fef3c7'; badge.style.color = '#92400e';
      title.textContent = 'BioNEETPro Ops';
      if (chips) {
        chips.innerHTML = '<span class="v2-chip" onclick="sendFloatingChip(\'Give me a summary of system governance policies\')">System Governance</span>' +
          '<span class="v2-chip" onclick="sendFloatingChip(\'How do teacher roles and assessment lifecycles work?\')">Teacher Lifecycle</span>' +
          '<span class="v2-chip" onclick="sendFloatingChip(\'What security guardrails protect student submissions?\')">Security Audit</span>';
      }
    } else {
      badge.textContent = 'NEET Mentor';
      badge.style.background = '#fef9c3'; badge.style.color = '#854d0e';
      title.textContent = 'Dr. Priya';
      if (chips) {
        chips.innerHTML = '<span class="v2-chip" onclick="sendFloatingChip(\'Explain the light reaction of photosynthesis simply\')">Light Reaction</span>' +
          '<span class="v2-chip" onclick="sendFloatingChip(\'What are my weak topics from recent tests?\')">My Weak Areas</span>' +
          '<span class="v2-chip" onclick="sendFloatingChip(\'High-yield NCERT facts for Cell Division\')">Cell Division Tips</span>';
      }
    }
  }
  window.updateAssistantRole = updateAssistantRole;

  window.sendFloatingChip = function(text) {
    var input = document.getElementById('floatingAssistantInput');
    if (input) input.value = text;
    sendFloatingAssistantMessage();
  };

  async function sendFloatingAssistantMessage() {
    var input = document.getElementById('floatingAssistantInput');
    var msgList = document.getElementById('floatingAssistantMessages');
    if (!input || !msgList) return;

    var text = input.value.trim();
    if (!text) return;
    input.value = '';

    // Append user bubble
    var userBubble = document.createElement('div');
    userBubble.style.cssText = 'align-self:flex-end;background:var(--ink);color:#fff;padding:10px 14px;border-radius:14px 14px 2px 14px;max-width:85%;font-size:0.85rem;margin-bottom:10px;line-height:1.4';
    userBubble.textContent = text;
    msgList.appendChild(userBubble);
    msgList.scrollTop = msgList.scrollHeight;

    // Typing bubble
    var typingBubble = document.createElement('div');
    typingBubble.style.cssText = 'align-self:flex-start;background:#f3f4f6;color:var(--muted);padding:8px 14px;border-radius:14px 14px 14px 2px;max-width:85%;font-size:0.82rem;margin-bottom:10px;font-style:italic';
    typingBubble.textContent = 'Thinking...';
    msgList.appendChild(typingBubble);
    msgList.scrollTop = msgList.scrollHeight;

    var role = (window.DB && window.DB.userRole) ? window.DB.userRole : 'STUDENT';

    try {
      var res = await apiFetch('/api/assistant/chat', {
        method: 'POST',
        body: JSON.stringify({
          message: text,
          role: role,
          history: assistantHistory.slice(-6)
        })
      });

      var data = await res.json();
      typingBubble.remove();

      var replyText = data.reply || "I am here to support your preparation!";
      assistantHistory.push({ role: 'user', content: text });
      assistantHistory.push({ role: 'assistant', content: replyText });

      var aiBubble = document.createElement('div');
      aiBubble.style.cssText = 'align-self:flex-start;background:#fff;border:1px solid #e5e7eb;color:var(--ink);padding:12px 14px;border-radius:14px 14px 14px 2px;max-width:90%;font-size:0.85rem;margin-bottom:10px;line-height:1.5;box-shadow:0 2px 8px rgba(0,0,0,0.04)';
      aiBubble.innerHTML = formatAssistantMarkdown(replyText);

      // Render interactive MCQ cards with clickable option badges if present
      if (data.mcqs && data.mcqs.length) {
        var mcqContainer = document.createElement('div');
        mcqContainer.style.cssText = 'margin-top:12px;display:flex;flex-direction:column;gap:10px';
        data.mcqs.forEach(function(q, qIdx) {
          var card = document.createElement('div');
          card.style.cssText = 'background:#f8fafc;border:1px solid #cbd5e1;border-radius:10px;padding:12px;font-size:0.82rem';
          var qTitle = document.createElement('div');
          qTitle.style.cssText = 'font-weight:700;color:#0f172a;margin-bottom:8px';
          qTitle.textContent = 'Q' + (qIdx + 1) + '. ' + q.question;
          card.appendChild(qTitle);

          var optGrid = document.createElement('div');
          optGrid.style.cssText = 'display:grid;grid-template-columns:1fr 1fr;gap:6px';
          (q.options || []).forEach(function(opt, optIdx) {
            var letter = String.fromCharCode(65 + optIdx);
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.style.cssText = 'background:#fff;border:1px solid #cbd5e1;border-radius:8px;padding:7px 10px;font-size:0.78rem;text-align:left;cursor:pointer;color:#1e293b;transition:all 0.15s ease;display:flex;gap:5px;align-items:flex-start';
            btn.innerHTML = '<strong style="color:#2563eb">(' + letter + ')</strong> <span>' + escapeHtml(opt) + '</span>';
            btn.onmouseover = function() { btn.style.background = '#eff6ff'; btn.style.borderColor = '#3b82f6'; };
            btn.onmouseout = function() { btn.style.background = '#fff'; btn.style.borderColor = '#cbd5e1'; };
            btn.onclick = function() {
              var queryText = (data.mcqs.length > 1 ? ('Q' + (qIdx + 1) + ': ') : 'Option ') + letter;
              sendFloatingChip(queryText);
            };
            optGrid.appendChild(btn);
          });
          card.appendChild(optGrid);
          mcqContainer.appendChild(card);
        });
        aiBubble.appendChild(mcqContainer);
      }

      // Interactive follow-up chips for 1-click cross-replies
      var followUpChips = data.chips || data.suggested_actions || [];
      if (followUpChips && followUpChips.length) {
        var chipsWrap = document.createElement('div');
        chipsWrap.style.cssText = 'display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;padding-top:8px;border-top:1px dashed #e5e7eb';
        followUpChips.forEach(function(c) {
          var chipBtn = document.createElement('button');
          chipBtn.type = 'button';
          chipBtn.style.cssText = 'background:#f9fafb;border:1px solid #d1d5db;border-radius:12px;padding:4px 9px;font-size:0.75rem;cursor:pointer;font-weight:700;color:var(--ink);transition:all .15s ease;display:inline-flex;align-items:center;gap:4px';
          var label = typeof c === 'string' ? c : (c.label || c.text);
          var q = typeof c === 'object' && c.query ? c.query : label;
          chipBtn.textContent = label;
          chipBtn.onmouseover = function() { chipBtn.style.background = '#fef08a'; chipBtn.style.borderColor = '#0a0a0a'; };
          chipBtn.onmouseout = function() { chipBtn.style.background = '#f9fafb'; chipBtn.style.borderColor = '#d1d5db'; };
          chipBtn.onclick = function() { sendFloatingChip(q); };
          chipsWrap.appendChild(chipBtn);
        });
        aiBubble.appendChild(chipsWrap);
      }

      msgList.appendChild(aiBubble);
      msgList.scrollTop = msgList.scrollHeight;

    } catch (e) {
      typingBubble.remove();
      var errBubble = document.createElement('div');
      errBubble.style.cssText = 'align-self:flex-start;background:#fee2e2;color:#991b1b;padding:8px 12px;border-radius:8px;font-size:0.82rem;margin-bottom:10px';
      errBubble.textContent = 'Could not connect to AI assistant. Please try again.';
      msgList.appendChild(errBubble);
    }
  }
  window.sendFloatingAssistantMessage = sendFloatingAssistantMessage;

  function formatAssistantMarkdown(text) {
    if (!text) return '';
    var escaped = escapeHtml(text);
    // Unescape safe tags for interactive collapsible sections
    escaped = escaped.replace(/&lt;(\/?(?:details|summary|b|strong|i|em))&gt;/gi, '<$1>');
    // Bold
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Italics
    escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Inline code
    escaped = escaped.replace(/`([^`\n]+)`/g, '<code style="background:#f1f5f9;padding:2px 5px;border-radius:4px;font-family:monospace;font-size:0.82em;color:#0f172a">$1</code>');

    // Parse Markdown tables and lists
    var lines = escaped.split('\n');
    var out = [];
    var i = 0;
    while (i < lines.length) {
      if (/^\s*\|.*\|\s*$/.test(lines[i])) {
        var tableRows = [];
        while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) {
          tableRows.push(lines[i]);
          i++;
        }
        if (tableRows.length >= 2) {
          var parseCells = function(rStr) {
            return rStr.trim().replace(/^\||\|$/g, '').split('|').map(function(c){ return c.trim(); });
          };
          var isDelim = function(rStr) {
            return /^\|\s*[-:]+[-| :]*\|\s*$/.test(rStr.trim());
          };
          var headers = parseCells(tableRows[0]);
          var bodyStart = (tableRows.length > 1 && isDelim(tableRows[1])) ? 2 : 1;
          var tHtml = '<div style="overflow-x:auto;margin:8px 0;border:1px solid #e2e8f0;border-radius:6px">';
          tHtml += '<table style="width:100%;border-collapse:collapse;font-size:0.78rem;text-align:left;background:#fff">';
          tHtml += '<thead><tr style="background:#f8fafc;border-bottom:2px solid #cbd5e1">';
          for (var h = 0; h < headers.length; h++) {
            tHtml += '<th style="padding:6px 8px;font-weight:700;color:#0f172a">' + headers[h] + '</th>';
          }
          tHtml += '</tr></thead><tbody>';
          for (var r = bodyStart; r < tableRows.length; r++) {
            if (isDelim(tableRows[r])) continue;
            var cells = parseCells(tableRows[r]);
            var bg = (r % 2 === 0) ? '#f8fafc' : '#ffffff';
            tHtml += '<tr style="background:' + bg + ';border-bottom:1px solid #f1f5f9">';
            for (var c = 0; c < headers.length; c++) {
              tHtml += '<td style="padding:6px 8px;color:#334155">' + (cells[c] || '') + '</td>';
            }
            tHtml += '</tr>';
          }
          tHtml += '</tbody></table></div>';
          out.push(tHtml);
          continue;
        }
      }
      if (/^\s*•\s+/.test(lines[i])) {
        out.push('<ul style="margin:4px 0 6px 16px;padding:0">');
        while (i < lines.length && /^\s*•\s+/.test(lines[i])) {
          out.push('<li>' + lines[i].replace(/^\s*•\s+/, '') + '</li>');
          i++;
        }
        out.push('</ul>');
        continue;
      }
      out.push(lines[i]);
      i++;
    }

    var joined = out.join('\n');
    joined = joined.replace(/>\n</g, '><');
    joined = joined.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
    return joined;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  // Hook into initial page load
  document.addEventListener('DOMContentLoaded', function() {
    fetchCurriculum();
    if (window.DB && window.DB.currentUser) {
      loadStudentUpcomingTests();
    }
    updateAssistantRole();
  });

})();
 
