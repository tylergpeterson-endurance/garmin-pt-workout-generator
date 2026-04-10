/**
 * FIT Binary Writer v5
 *
 * Exact structural match to Tyler's generate_pt_workout.py output:
 * - auto_define behavior: new definition record whenever field set changes
 * - 4 distinct WorkoutStep shapes: active(9f), rest(6f), repeat(4f)
 * - REPEAT_UNTIL_STEPS_CMPLT loops (not flat unrolling)
 * - wkt_step_name + notes + exercise_category + exercise_name on active steps
 * - One ExerciseTitle per exercise (not per step)
 * - 12-byte header, protocol 2.3, profile 2160
 */

import {
  BT, MSG, FileType, Manuf, Sport, SubSport,
  Intensity, ExCat, WktDur, WktTarget, CFG,
  HDR_SIZE, PROTOCOL, PROFILE, FIT_EPOCH, CRC_TABLE,
} from './fit-constants.js';

// ── CRC ─────────────────────────────────────────────────────────────────────

function crc16(c, b) {
  let t = CRC_TABLE[c & 0xF];
  c = (c >> 4) & 0xFFF; c = c ^ t ^ CRC_TABLE[b & 0xF];
  t = CRC_TABLE[c & 0xF];
  c = (c >> 4) & 0xFFF; c = c ^ t ^ CRC_TABLE[(b >> 4) & 0xF];
  return c;
}
function crcArr(a, init = 0) { let c = init; for (let i = 0; i < a.length; i++) c = crc16(c, a[i]); return c; }

// ── Binary Buffer ───────────────────────────────────────────────────────────

const ENC = new TextEncoder();
function strSz(s) { return ENC.encode(String(s)).length + 1; }

class B {
  constructor(n = 8192) { this.ab = new ArrayBuffer(n); this.dv = new DataView(this.ab); this.u8 = new Uint8Array(this.ab); this.p = 0; }
  _g(n) { if (this.p+n<=this.ab.byteLength) return; const s=Math.max(this.ab.byteLength*2,this.p+n),b=new ArrayBuffer(s); new Uint8Array(b).set(this.u8); this.ab=b; this.dv=new DataView(b); this.u8=new Uint8Array(b); }
  w8(v)  { this._g(1); this.dv.setUint8(this.p,v);       this.p+=1; }
  w16(v) { this._g(2); this.dv.setUint16(this.p,v,true);  this.p+=2; }
  w32(v) { this._g(4); this.dv.setUint32(this.p,v,true);  this.p+=4; }
  wS(s,n){ this._g(n); const e=ENC.encode(s),m=Math.min(e.length,n-1); for(let i=0;i<m;i++)this.u8[this.p+i]=e[i]; for(let i=m;i<n;i++)this.u8[this.p+i]=0; this.p+=n; }
  out()  { return new Uint8Array(this.ab, 0, this.p); }
}

// ── Record writers ──────────────────────────────────────────────────────────
// fit-tool uses auto_define=True: emits a definition before each data record
// when the field set changes. We replicate this by writing def+data pairs.

function writeDef(b, gm, fields) {
  b.w8(0x40); b.w8(0); b.w8(0); b.w16(gm); b.w8(fields.length);
  for (const f of fields) { b.w8(f.dn); b.w8(f.sz); b.w8(f.bt); }
}

function writeVal(b, bt, sz, v) {
  if (bt === BT.ENUM)   return b.w8(v);
  if (bt === BT.UINT16) return b.w16(v);
  if (bt === BT.UINT32 || bt === BT.UINT32Z) return b.w32(v);
  if (bt === BT.STRING) return b.wS(String(v), sz);
}

function writeData(b, fields) {
  b.w8(0x00); // data record, local type 0
  for (const f of fields) writeVal(b, f.bt, f.sz, f.v);
}

/** Write definition + data record pair (auto_define pattern). */
function writeMsg(b, gm, fields) {
  writeDef(b, gm, fields);
  writeData(b, fields);
}

// ── Workout step builders ───────────────────────────────────────────────────
// 4 step shapes matching the Python script's output.

/** Active exercise step — 9 fields: index, name, dur_type, dur_val, target_type, intensity, notes, ex_cat, ex_name */
function activeStep(b, idx, name, durType, durVal, notes, exId) {
  const nameSz = strSz(name);
  const notesSz = strSz(notes);
  writeMsg(b, MSG.WORKOUT_STEP, [
    { dn:254, bt:BT.UINT16, sz:2,       v:idx },
    { dn:0,   bt:BT.STRING, sz:nameSz,  v:name },
    { dn:1,   bt:BT.ENUM,   sz:1,       v:durType },
    { dn:2,   bt:BT.UINT32, sz:4,       v:durVal },
    { dn:3,   bt:BT.ENUM,   sz:1,       v:WktTarget.OPEN },
    { dn:7,   bt:BT.ENUM,   sz:1,       v:Intensity.ACTIVE },
    { dn:8,   bt:BT.STRING, sz:notesSz, v:notes },
    { dn:10,  bt:BT.UINT16, sz:2,       v:ExCat.UNKNOWN },
    { dn:11,  bt:BT.UINT16, sz:2,       v:exId },
  ]);
}

/** Rest/Recover/Transition step — 6 fields: index, name, dur_type, dur_val, target_type, intensity */
function restStep(b, idx, name, durVal) {
  const nameSz = strSz(name);
  writeMsg(b, MSG.WORKOUT_STEP, [
    { dn:254, bt:BT.UINT16, sz:2,      v:idx },
    { dn:0,   bt:BT.STRING, sz:nameSz, v:name },
    { dn:1,   bt:BT.ENUM,   sz:1,      v:WktDur.TIME },
    { dn:2,   bt:BT.UINT32, sz:4,      v:durVal },
    { dn:3,   bt:BT.ENUM,   sz:1,      v:WktTarget.OPEN },
    { dn:7,   bt:BT.ENUM,   sz:1,      v:Intensity.REST },
  ]);
}

/** Repeat step — 4 fields: index, dur_type(REPEAT), dur_value(step to loop to), target_value(iterations) */
function repeatStep(b, idx, loopToStep, iterations) {
  writeMsg(b, MSG.WORKOUT_STEP, [
    { dn:254, bt:BT.UINT16, sz:2, v:idx },
    { dn:1,   bt:BT.ENUM,   sz:1, v:WktDur.REPEAT },
    { dn:2,   bt:BT.UINT32, sz:4, v:loopToStep },
    { dn:4,   bt:BT.UINT32, sz:4, v:iterations },
  ]);
}

// ── Public API ──────────────────────────────────────────────────────────────

export function generateWorkoutFit({ workoutName, exercises }) {
  const d = new B(8192);

  // ── FILE_ID ──
  const ts = Math.floor((Date.now() - FIT_EPOCH) / 1000);
  writeMsg(d, MSG.FILE_ID, [
    { dn:0, bt:BT.ENUM,    sz:1, v:FileType.WORKOUT },
    { dn:1, bt:BT.UINT16,  sz:2, v:Manuf.DEVELOPMENT },
    { dn:2, bt:BT.UINT16,  sz:2, v:0 },
    { dn:3, bt:BT.UINT32Z, sz:4, v:0x12345678 },
    { dn:4, bt:BT.UINT32,  sz:4, v:ts },
  ]);

  // ── Build steps (matching Python logic exactly) ──

  let si = 0; // step index
  const titles = [];

  for (let ei = 0; ei < exercises.length; ei++) {
    const ex = exercises[ei];
    const sets = ex.sets;
    const reps = ex.reps;
    const hold = ex.holdSeconds;
    const useTimed = hold >= CFG.HOLD_THRESH;
    const stepName = hold > 0 ? `${ex.name} (${hold}s hold)` : ex.name;
    const notes = ex.notes || (hold > 0 ? `Hold ${hold}s each rep` : '');

    // One ExerciseTitle per exercise
    titles.push({ idx: titles.length, exId: ei, name: stepName });

    if (useTimed) {
      // ── TIMED: unroll sets, REPEAT reps within each set ──
      for (let s = 0; s < sets; s++) {
        const repStepIdx = si;

        // Timed active step (one rep)
        activeStep(d, si, stepName, WktDur.TIME, hold * 1000, notes, ei);
        si++;

        // Brief rest between reps
        restStep(d, si, 'Recover', hold < 20 ? 5000 : CFG.REST_REPS_MS);
        si++;

        // Repeat loop for reps (if > 1)
        if (reps > 1) {
          repeatStep(d, si, repStepIdx, reps);
          si++;
        }

        // Rest between sets (not after last set)
        if (s < sets - 1) {
          restStep(d, si, 'Rest', CFG.REST_SETS_MS);
          si++;
        }
      }
    } else {
      // ── REP-BASED ──
      if (sets > 1) {
        const firstStepOfSet = si;

        activeStep(d, si, stepName, WktDur.REPS, reps, notes, ei);
        si++;

        restStep(d, si, 'Rest', CFG.REST_SETS_MS);
        si++;

        repeatStep(d, si, firstStepOfSet, sets);
        si++;
      } else {
        activeStep(d, si, stepName, WktDur.REPS, reps, notes, ei);
        si++;
      }
    }

    // Rest between exercises
    if (ei < exercises.length - 1) {
      restStep(d, si, 'Next Exercise', CFG.REST_EX_MS);
      si++;
    }
  }

  const totalSteps = si;

  // ── WORKOUT message (written AFTER file_id but BEFORE steps in Python,
  //    but fit-tool builder adds it in order; we need it before steps) ──
  // Actually looking at the byte dump: FILE_ID → WORKOUT → steps → titles.
  // But we already wrote FILE_ID and steps... we need to insert WORKOUT before steps.
  //
  // Let me restructure: collect step bytes separately, then assemble in order.

  // OOPS — I wrote steps already. Need to restructure.
  // Let me use a two-buffer approach.

  // Actually, the simplest fix: rebuild. Steps go into a separate buffer.
  // Sorry — let me redo this properly.

  const final = new B(8192);

  // 1) FILE_ID
  writeMsg(final, MSG.FILE_ID, [
    { dn:0, bt:BT.ENUM,    sz:1, v:FileType.WORKOUT },
    { dn:1, bt:BT.UINT16,  sz:2, v:Manuf.DEVELOPMENT },
    { dn:2, bt:BT.UINT16,  sz:2, v:0 },
    { dn:3, bt:BT.UINT32Z, sz:4, v:0x12345678 },
    { dn:4, bt:BT.UINT32,  sz:4, v:ts },
  ]);

  // 2) WORKOUT
  const wktNameSz = strSz(workoutName);
  writeMsg(final, MSG.WORKOUT, [
    { dn:4,  bt:BT.ENUM,   sz:1,         v:Sport.TRAINING },
    { dn:6,  bt:BT.UINT16, sz:2,         v:totalSteps },
    { dn:8,  bt:BT.STRING, sz:wktNameSz, v:workoutName },
    { dn:11, bt:BT.ENUM,   sz:1,         v:SubSport.STRENGTH_TRAINING },
  ]);

  // 3) Replay step generation into final buffer
  si = 0;
  for (let ei = 0; ei < exercises.length; ei++) {
    const ex = exercises[ei];
    const sets = ex.sets;
    const reps = ex.reps;
    const hold = ex.holdSeconds;
    const useTimed = hold >= CFG.HOLD_THRESH;
    const stepName = hold > 0 ? `${ex.name} (${hold}s hold)` : ex.name;
    const notes = ex.notes || (hold > 0 ? `Hold ${hold}s each rep` : '');

    if (useTimed) {
      for (let s = 0; s < sets; s++) {
        const repStepIdx = si;
        activeStep(final, si, stepName, WktDur.TIME, hold * 1000, notes, ei); si++;
        restStep(final, si, 'Recover', hold < 20 ? 5000 : CFG.REST_REPS_MS); si++;
        if (reps > 1) { repeatStep(final, si, repStepIdx, reps); si++; }
        if (s < sets - 1) { restStep(final, si, 'Rest', CFG.REST_SETS_MS); si++; }
      }
    } else {
      if (sets > 1) {
        const first = si;
        activeStep(final, si, stepName, WktDur.REPS, reps, notes, ei); si++;
        restStep(final, si, 'Rest', CFG.REST_SETS_MS); si++;
        repeatStep(final, si, first, sets); si++;
      } else {
        activeStep(final, si, stepName, WktDur.REPS, reps, notes, ei); si++;
      }
    }

    if (ei < exercises.length - 1) { restStep(final, si, 'Next Exercise', CFG.REST_EX_MS); si++; }
  }

  // 4) Exercise Titles — one per exercise, string padded to max
  const maxTitleSz = Math.max(...titles.map(t => strSz(t.name)));

  // Write one definition, then all data records (matching Python output)
  writeDef(final, MSG.EXERCISE_TITLE, [
    { dn:254, bt:BT.UINT16, sz:2 },
    { dn:0,   bt:BT.UINT16, sz:2 },
    { dn:1,   bt:BT.UINT16, sz:2 },
    { dn:2,   bt:BT.STRING, sz:maxTitleSz },
  ]);
  for (const t of titles) {
    writeData(final, [
      { bt:BT.UINT16, sz:2,          v:t.idx },
      { bt:BT.UINT16, sz:2,          v:ExCat.UNKNOWN },
      { bt:BT.UINT16, sz:2,          v:t.exId },
      { bt:BT.STRING, sz:maxTitleSz, v:t.name },
    ]);
  }

  // ── Assemble FIT file ─────────────────────────────────────────────────

  const dataBytes = final.out();
  const dataSize = dataBytes.length;

  const h = new B(HDR_SIZE);
  h.w8(HDR_SIZE); h.w8(PROTOCOL); h.w16(PROFILE); h.w32(dataSize);
  h.w8(0x2E); h.w8(0x46); h.w8(0x49); h.w8(0x54);
  const hb = h.out();

  let fc = crcArr(hb);
  fc = crcArr(dataBytes, fc);

  const tot = HDR_SIZE + dataSize + 2;
  const out = new Uint8Array(tot);
  out.set(hb, 0);
  out.set(dataBytes, HDR_SIZE);
  out[tot-2] = fc & 0xFF;
  out[tot-1] = (fc >> 8) & 0xFF;
  return out;
}

export function downloadFitFile(fitBytes, filename = 'pt_workout.fit') {
  const blob = new Blob([fitBytes], { type: 'application/octet-stream' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click();
  document.body.removeChild(a); URL.revokeObjectURL(url);
}
