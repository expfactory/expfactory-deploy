/* ************************************ */
/* fMRI UTILS */
/* ************************************ */
var check_index = {
  // Check key press for index finger.
  type: jsPsychHtmlKeyboardResponse,
  stimulus: "<div><h1>Please press your index finger.</h1></div>",
  choices: ["y"],
  post_trial_gap: 500,
  data: function () {
    return {
      trial_id: "check_index",
    };
  },
};

var check_middle = {
  // Check key press for middle finger.
  type: jsPsychHtmlKeyboardResponse,
  stimulus: "<div><h1>Please press your middle finger.</h1></div>",
  choices: ["g"],
  post_trial_gap: 500,
  data: function () {
    return {
      trial_id: "check_middle",
    };
  },
};

var check_fingers_node = {
  // Check key press for index and middle fingers.
  timeline: [check_index, check_middle],
};

var fmri_wait_block_initial = {
  // Wait block for scanner setup.
  type: jsPsychHtmlKeyboardResponse,
  stimulus:
    "<div><h1>Scanner setup.</h1><h1>Stay as still as possible.</h1><h1>Do not swallow.</h1></div>",
  choices: ["Enter"],
  data: function () {
    return {
      trial_id: "fmri_wait_block_initial",
    };
  },
  on_finish: function () {
    console.log("Finished fMRI initial wait block...");
  },
};

var fmri_wait_block_trigger_start = {
  // Wait block for task to start.
  type: jsPsychHtmlKeyboardResponse,
  stimulus:
    "<div><h1>Task about to start!</h1><h1>Stay as still as possible.</h1><h1>Do not swallow.</h1></div>",
  choices: ["t"],
  response_ends_trial: true,
  data: function () {
    return {
      trial_id: "fmri_wait_block_trigger_start",
    };
  },
  on_finish: function () {
    console.log("Finished fMRI initial trigger block...");
  },
};

var fmri_wait_block_trigger_end = {
  // Wait block for task to end.
  type: jsPsychHtmlKeyboardResponse,
  stimulus:
    "<div><h1>Task about to start!</h1><h1>Stay as still as possible.</h1><h1>Do not swallow.</h1></div>",
  choices: ["NO_KEYS"],
  trial_duration: 10430, // 1.49s/tr * 7trs * 1000
  response_ends_trial: false,
  data: function () {
    return {
      trial_id: "fmri_wait_block_trigger_end",
      block_duration: 10430,
    };
  },
  on_finish: function () {
    console.log("Finished fMRI trigger block...");
  },
};

var fmri_wait_block_trigger_node = {
  // Wait blocks for task to start and end.
  timeline: [fmri_wait_block_trigger_start, fmri_wait_block_trigger_end],
};

var fmri_wait_node = {
  // Wait blocks for scanner setup and task to start and end.
  timeline: [fmri_wait_block_initial, fmri_wait_block_trigger_node],
};

/**
 * NOTES
 *
 * The following objects are utilized in the experiment.js timeline variable for the tasks:
 *
 * - check_fingers_node: Ensures that the participant's fingers are positioned on the correct keys before the task begins. Also ensures that the
 *   participant's keypresses are recorded correctly.
 * - fmri_wait_node: Manages the waiting periods for scanner setup, as well as the start and end of the task.
 */
