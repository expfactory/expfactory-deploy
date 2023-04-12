var jsPoldracklabStopSignal = (function (jspsych) {
  "use strict";

  const info = {
    name: "poldracklab-stop-signal",
    parameters: {
      response_ends_trial: {
        type: jspsych.ParameterType.BOOL,
        default: false
      },
	    stimulus: {
        type: jspsych.COMPLEX,
        default: undefined
      },
	    SS_stimulus: {
        type: jspsych.COMPLEX,
        default: undefined
      },
      SS_trial_type: {
        type: jspsych.STRING,
        default: undefined
      },
      stimulus_duration: {
        type: jspsych.INT,
        default: -1
      },
      SS_duration: {
        type: jspsych.INT,
        default: -1
      },
      trial_duration: {
        type: jspsych.INT,
        default: -1
      },
      SSD: {
        type: jspsych.INT,
        default: undefined
      },
      post_trial_gap: {
        type: jspsych.INT,
        default: 1000
      },
      prompt: {
        type: jspsych.STRING,
        default: ""
      },
      choices: {
        type: jspsych.KEYS
      },
      correct_choice: {
        type: jspsych.KEY,
        default: null
      },
    }
  }

  /**
   * **poldracklab-stop-signal**
   *
   * @author
   * @see
   */
  class PoldracklabStopSignalPlugin {
    constructor(jsPsych) {
      this.jsPsych = jsPsych;
    }

    trial(display_element, trial) {
      // this array holds handlers from setTimeout calls
      // that need to be cleared if the trial ends early
      var setTimeoutHandlers = [];

      // display stimulus
      const elemId = 'jspsych-stop-signal-stimulus'
      const elemType = 'div'
      display_element.innerHTML = `<${elemType} id='${elemId}'>${trial.stimulus}</${elemType}>${trial.prompt}`

      // store response
      var response = {rt: null, key: null};

      // function to end trial when it is time
      var end_trial = function() {
        // kill any remaining setTimeout handlers
        for (var i = 0; i < setTimeoutHandlers.length; i++) {
          clearTimeout(setTimeoutHandlers[i]);
        }

        // kill keyboard listeners
        if(typeof keyboardListener !== 'undefined'){
          jsPsych.pluginAPI.cancelKeyboardResponse(keyboardListener);
        }

        // gather the data to store for the trial
        console.log(response.key)
        var trial_data = {
          "rt": response.rt,
          "response": response.key,
          "correct": response.key === trial.correct_choice
        };

        // clear the display
        display_element.innerHTML = ''

        if (trial.save_trial_parameters === undefined) {
          trial.save_trial_parameters = {
            response_ends_trial: true,
            stimulus: true,
            SS_stimulus: true,
            SS_trial_type: true,
            stimulus_duration: true,
            SS_duration: true,
            trial_duration: true,
            SSD: true,
            choices: true,
            correct_choice: true
          }
        }


        // move on to the next trial
        jsPsych.finishTrial(trial_data);
      };

      // function to handle responses by the subject
      var after_response = function(info) {

        // after a valid response, the stimulus will have the CSS class 'responded'
        // which can be used to provide visual feedback that a response was recorded
        $("#jspsych-stop-signal-stimulus").addClass('responded');

        // only record the first response
        if(response.key == null){
          response = info;
        }

        if (trial.response_ends_trial) {
          end_trial();
        }
      };

      // start the response listener
      var keyboardListener = jsPsych.pluginAPI.getKeyboardResponse({
        callback_function: after_response,
        valid_responses: trial.choices,
        rt_method: 'performance',
        persist: false,
        allow_held_key: false
      });

      // hide image if timing is set
      if (trial.stimulus_duration > 0) {
        var t1 = setTimeout(function() {
          document.getElementById('jspsych-stop-signal-stimulus').setAttribute('hidden', 'foo');
        }, trial.stimulus_duration);
        setTimeoutHandlers.push(t1);
      }

      // end trial if time limit is set
      if (trial.trial_duration > 0) {
        var t2  = setTimeout(function() {
          end_trial();
        }, trial.trial_duration );
        setTimeoutHandlers.push(t2);
      }

      if (trial.SS_trial_type.toLowerCase() == 'stop') {
        if (trial.SSD >= 0) {
          const SS_stimulus = `<div id='jspsych-stop-signal-SS'>${trial.SS_stimulus}</div>`
          var t3 = setTimeout(function() {
            display_element.innerHTML += SS_stimulus
          }, trial.SSD);
          setTimeoutHandlers.push(t3);
        }

        // hide SS after a fixed interval (or when stimulus ends)
        if (trial.SS_duration > 0) {
          var t4 = setTimeout(function() {
            document.getElementById('jspsych-stop-signal-SS').setAttribute('hidden', 'foo');
          }, trial.SS_duration+trial.SSD);
          setTimeoutHandlers.push(t4);
        }
      }
    }
  }
  PoldracklabStopSignalPlugin.info = info
  return PoldracklabStopSignalPlugin;
})(jsPsychModule);
