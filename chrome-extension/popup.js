/**
 * Popup Controller
 * Coordinates between programmatic script injection (DOM extraction) and the FIT writer.
 */

import { generateWorkoutFit, downloadFitFile } from './lib/fit-writer.js';

// ── Extraction function injected into the page via chrome.scripting ─────────
// Must be entirely self-contained (no imports, no closures over popup scope).

function extractExercisesOnPage() {
  try {
    function parseBadge(text) {
      const t = text.trim().toUpperCase();
      const setsMatch = t.match(/^(\d+)\s*SETS?$/);
      if (setsMatch) return { type: 'sets', value: parseInt(setsMatch[1], 10) };
      const repsMatch = t.match(/^(\d+)\s*REPS?$/);
      if (repsMatch) return { type: 'reps', value: parseInt(repsMatch[1], 10) };
      // "30 SECONDS HOLD" or "2-3 SECONDS HOLD" (take upper value of range)
      const holdMatch = t.match(/^(?:\d+[-–])?(\d+)\s*(?:SECONDS?|SECS?|S)\s*HOLD$/);
      if (holdMatch) return { type: 'hold', value: parseInt(holdMatch[1], 10) };
      const secMatch = t.match(/^(?:\d+[-–])?(\d+)\s*(?:SECONDS?|SECS?|S)$/);
      if (secMatch) return { type: 'hold', value: parseInt(secMatch[1], 10) };
      return null;
    }

    const exercises = [];
    const nameSpans = document.querySelectorAll(
      'span.text-xl.text-gray-800.font-medium.capitalize'
    );
    const candidates = nameSpans.length > 0
      ? nameSpans
      : document.querySelectorAll('span.text-xl.font-medium.capitalize');

    for (const nameSpan of candidates) {
      const name = nameSpan.textContent.trim();
      if (!name) continue;

      let container = nameSpan.closest('[class*="cursor-pointer"]')
        || nameSpan.parentElement?.parentElement?.parentElement
        || nameSpan.parentElement?.parentElement;
      if (!container) continue;

      const badgeDivs = container.querySelectorAll('.bg-primary-500');
      let sets = 1, reps = 1, holdSeconds = 0;

      for (const badge of badgeDivs) {
        const parsed = parseBadge(badge.textContent.trim());
        if (!parsed) continue;
        switch (parsed.type) {
          case 'sets': sets = parsed.value; break;
          case 'reps': reps = parsed.value; break;
          case 'hold': holdSeconds = parsed.value; break;
        }
      }
      exercises.push({ name, sets, reps, holdSeconds });
    }
    return { success: true, exercises };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

// ── DOM refs ────────────────────────────────────────────────────────────────

const statusEl       = document.getElementById('status');
const btnExtract     = document.getElementById('btn-extract');
const stepExtract    = document.getElementById('step-extract');
const stepReview     = document.getElementById('step-review');
const reviewStatusEl = document.getElementById('review-status');
const exerciseListEl = document.getElementById('exercise-list');
const filenameInput  = document.getElementById('filename');
const btnGenerate    = document.getElementById('btn-generate');
const btnReExtract   = document.getElementById('btn-re-extract');
const summaryEl      = document.getElementById('summary');

let currentExercises = [];

// ── Helpers ─────────────────────────────────────────────────────────────────

function setStatus(el, text, type = 'info') {
  el.className = `status ${type}`;
  el.textContent = text;
}

function formatExerciseMeta(ex) {
  const parts = [];
  parts.push(`${ex.sets}×${ex.reps}`);
  if (ex.holdSeconds > 0) parts.push(`${ex.holdSeconds}s hold`);
  return parts.join(', ');
}

function countTotalSteps(exercises) {
  // Matches REPEAT-loop logic in the FIT writer
  let count = 0;
  const HOLD_THRESHOLD = 5;
  for (let i = 0; i < exercises.length; i++) {
    const ex = exercises[i];
    const isTimed = ex.holdSeconds >= HOLD_THRESHOLD;
    if (isTimed) {
      // Per set: active + recover + repeat(if reps>1) + rest(if not last set)
      for (let s = 0; s < ex.sets; s++) {
        count += 2; // active + recover
        if (ex.reps > 1) count += 1; // repeat step
        if (s < ex.sets - 1) count += 1; // set rest
      }
    } else {
      if (ex.sets > 1) {
        count += 3; // exercise + rest + repeat
      } else {
        count += 1; // single exercise step
      }
    }
    if (i < exercises.length - 1) count += 1; // exercise rest
  }
  return count;
}

function generateFilename(exercises) {
  const date = new Date();
  const ymd = date.toISOString().slice(0, 10).replace(/-/g, '');
  return `pt_workout_${ymd}.fit`;
}

// ── Extract ─────────────────────────────────────────────────────────────────

async function doExtract() {
  btnExtract.disabled = true;
  setStatus(statusEl, 'Extracting exercises…', 'info');

  try {
    // Get the active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab) {
      setStatus(statusEl, 'No active tab found.', 'error');
      btnExtract.disabled = false;
      return;
    }

    // Check if we're on PT Wired
    const url = tab.url || '';
    if (!url.includes('ptwired.com')) {
      setStatus(statusEl, 'Not on a PT Wired page. Navigate there first.', 'warning');
      btnExtract.disabled = false;
      return;
    }

    // Programmatically inject and run extraction (no content script dependency)
    const injectionResults = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractExercisesOnPage,
    });

    const result = injectionResults?.[0]?.result;

    if (!result || !result.success) {
      setStatus(statusEl, `Extraction failed: ${result?.error || 'No response from page'}`, 'error');
      btnExtract.disabled = false;
      return;
    }

    currentExercises = result.exercises;

    if (currentExercises.length === 0) {
      setStatus(statusEl, 'No exercises found on this page. Make sure you\'re on an exercise list page.', 'warning');
      btnExtract.disabled = false;
      return;
    }

    // Show review step
    showReview();
  } catch (err) {
    setStatus(statusEl, `Error: ${err.message}`, 'error');
    btnExtract.disabled = false;
  }
}

// ── Review UI ───────────────────────────────────────────────────────────────

function showReview() {
  stepExtract.classList.add('hidden');
  stepReview.classList.remove('hidden');

  setStatus(reviewStatusEl, `Found ${currentExercises.length} exercise${currentExercises.length !== 1 ? 's' : ''}`, 'success');

  // Populate exercise list
  exerciseListEl.innerHTML = '';
  for (const ex of currentExercises) {
    const li = document.createElement('li');
    li.className = 'exercise-item';
    li.innerHTML = `
      <span class="exercise-name">${escapeHtml(ex.name)}</span>
      <span class="exercise-meta">${escapeHtml(formatExerciseMeta(ex))}</span>
    `;
    exerciseListEl.appendChild(li);
  }

  // Auto-generate filename
  filenameInput.value = generateFilename(currentExercises);

  // Summary
  const totalSteps = countTotalSteps(currentExercises);
  summaryEl.textContent = `${totalSteps} workout steps will be generated`;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ── Generate FIT ────────────────────────────────────────────────────────────

function doGenerate() {
  btnGenerate.disabled = true;

  try {
    const filename = filenameInput.value.trim() || 'pt_workout.fit';
    const workoutName = filename.replace(/\.fit$/i, '');

    const fitBytes = generateWorkoutFit({
      workoutName,
      exercises: currentExercises,
    });

    downloadFitFile(fitBytes, filename);

    setStatus(reviewStatusEl, `✓ Downloaded ${filename} (${fitBytes.length} bytes)`, 'success');
    summaryEl.textContent = 'Copy to Garmin\\GARMIN\\NewFiles\\ or use deploy.py';
  } catch (err) {
    setStatus(reviewStatusEl, `FIT generation failed: ${err.message}`, 'error');
  } finally {
    btnGenerate.disabled = false;
  }
}

// ── Re-Extract ──────────────────────────────────────────────────────────────

function doReExtract() {
  stepReview.classList.add('hidden');
  stepExtract.classList.remove('hidden');
  btnExtract.disabled = false;
  currentExercises = [];
  setStatus(statusEl, 'Navigate to your PT Wired exercise page, then click Extract.', 'info');
}

// ── Event Listeners ─────────────────────────────────────────────────────────

btnExtract.addEventListener('click', doExtract);
btnGenerate.addEventListener('click', doGenerate);
btnReExtract.addEventListener('click', doReExtract);
