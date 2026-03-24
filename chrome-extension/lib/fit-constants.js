/**
 * FIT Protocol Constants — matched to fit-tool library (Python) values.
 */

export const BT = {
  ENUM:    0x00,
  UINT16:  0x84,
  UINT32:  0x86,
  STRING:  0x07,
  UINT32Z: 0x8C,
};

export const MSG        = { FILE_ID: 0, WORKOUT: 26, WORKOUT_STEP: 27, EXERCISE_TITLE: 264 };
export const FileType   = { WORKOUT: 5 };
export const Manuf      = { DEVELOPMENT: 255 };  // fit-tool uses DEVELOPMENT, not GARMIN
export const Sport      = { TRAINING: 10 };
export const SubSport   = { STRENGTH_TRAINING: 20 };
export const Intensity  = { ACTIVE: 0, REST: 1 };
export const ExCat      = { UNKNOWN: 65534 };

export const WktDur = {
  TIME:   0,
  REPEAT: 6,   // REPEAT_UNTIL_STEPS_CMPLT — duration_value = step to loop to
  REPS:   29,
};

export const WktTarget  = { OPEN: 2 };  // NOT 0 (that's SPEED)

export const HDR_SIZE   = 12;  // no header CRC
export const PROTOCOL   = 0x23;
export const PROFILE    = 2160;
export const FIT_EPOCH  = Date.UTC(1989, 11, 31, 0, 0, 0);

export const CRC_TABLE = [
  0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
  0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400,
];

export const CFG = {
  REST_REPS_MS: 10000,
  REST_SETS_MS: 30000,
  REST_EX_MS:   45000,
  HOLD_THRESH:  5,
};
