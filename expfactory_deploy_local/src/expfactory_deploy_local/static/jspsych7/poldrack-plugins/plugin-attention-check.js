/**
 ** Attention check plugin for RDoC **
 *** jsPsych plugin for presenting attention checks
 *** In RDoC, these attention checks occur between every test block.
 * @author Logan Bennett
 **/

var jsPsychAttentionCheckRdoc = (function (jspsych) {
  "use strict";

  const info = {
    name: "html-keyboard-response",
    parameters: {
      question: {
        type: jspsych.ParameterType.STRING,
        pretty_name: "Question",
        default: null,
        description: "The attention check questions to be displayed.",
      },
      key_answer: {
        type: jspsych.ParameterType.KEYCODE,
        pretty_name: "Key answer",
        default: null,
        description: "The correct key code for the attention check question.",
      },
      choices: {
        type: jspsych.ParameterType.KEYS,
        pretty_name: "Choices",
        default: "ALL_KEYS",
        description:
          "Available key press options (all keys enabled by default).",
      },
      trial_duration: {
        type: jspsych.ParameterType.INT,
        pretty_name: "Trial duration",
        default: null,
        description: "How long to show trial before it ends.",
      },
      stimulus_duration: {
        type: jspsych.ParameterType.INT,
        pretty_name: "Stimulus duration",
        default: null,
        description:
          "How long to show trial stimulus before it is removed from screen.",
      },
      response_ends_trial: {
        type: jspsych.ParameterType.BOOL,
        pretty_name: "Response ends trial",
        default: true,
        description:
          "If true, clicking any button will immediately end current trial.",
      },
    },
  };
  class AttentionCheckRdocPlugin {
    constructor(jsPsych) {
      this.jsPsych = jsPsych;
    }
    trial(display_element, trial) {
      var current_question = trial.question;
      var correct_key = trial.key_answer;

      var new_html = `<div id="jspsych-attention-check-rdoc-stimulus">${current_question}</div>`;
      display_element.innerHTML = new_html;
      var response = {
        rt: null,
        key: null,
      };
      // function to end trial when it is time
      const end_trial = () => {
        // kill any remaining setTimeout handlers
        this.jsPsych.pluginAPI.clearAllTimeouts();
        // kill keyboard listeners
        if (typeof keyboardListener !== "undefined") {
          this.jsPsych.pluginAPI.cancelKeyboardResponse(keyboardListener);
        }

        var correct_key_string = String.fromCharCode(correct_key).toLowerCase();

        // logging trial data
        var trial_data = {
          attention_check_question: current_question,
          correct_response: correct_key_string,
          correct_trial: correct_key_string === response.key ? 1 : 0,
          response: response.key,
          rt: response.rt,
        };

        display_element.innerHTML = "";
        this.jsPsych.finishTrial(trial_data);
      };
      var after_response = (info) => {
        display_element.querySelector(
          "#jspsych-attention-check-rdoc-stimulus"
        ).className += " responded";
        if (response.key == null) {
          response = info;
        }
        if (trial.response_ends_trial) {
          end_trial();
        }
      };
      if (trial.choices != "NO_KEYS") {
        var keyboardListener = this.jsPsych.pluginAPI.getKeyboardResponse({
          callback_function: after_response,
          valid_responses: trial.choices,
          rt_method: "performance",
          persist: false,
          allow_held_key: false,
        });
      }
      if (trial.stimulus_duration !== null) {
        this.jsPsych.pluginAPI.setTimeout(() => {
          display_element.querySelector(
            "#jspsych-attention-check-rdoc-stimulus"
          ).style.visibility = "hidden";
        }, trial.stimulus_duration);
      }
      if (trial.trial_duration !== null) {
        this.jsPsych.pluginAPI.setTimeout(end_trial, trial.trial_duration);
      }
    }
    simulate(trial, simulation_mode, simulation_options, load_callback) {
      if (simulation_mode == "data-only") {
        load_callback();
        this.simulate_data_only(trial, simulation_options);
      }
      if (simulation_mode == "visual") {
        this.simulate_visual(trial, simulation_options, load_callback);
      }
    }
    create_simulation_data(trial, simulation_options) {
      const default_data = {
        current_question: current_question,
        current_key_answer: current_key_answer,
        rt: this.jsPsych.randomization.sampleExGaussian(500, 50, 1 / 150, true),
        response: this.jsPsych.pluginAPI.getValidKey(trial.choices),
      };
      const data = this.jsPsych.pluginAPI.mergeSimulationData(
        default_data,
        simulation_options
      );
      this.jsPsych.pluginAPI.ensureSimulationDataConsistency(trial, data);
      return data;
    }
    simulate_data_only(trial, simulation_options) {
      const data = this.create_simulation_data(trial, simulation_options);
      this.jsPsych.finishTrial(data);
    }
    simulate_visual(trial, simulation_options, load_callback) {
      const data = this.create_simulation_data(trial, simulation_options);
      const display_element = this.jsPsych.getDisplayElement();
      this.trial(display_element, trial);
      load_callback();
      if (data.rt !== null) {
        this.jsPsych.pluginAPI.pressKey(data.response, data.rt);
      }
    }
  }
  AttentionCheckRdocPlugin.info = info;

  return AttentionCheckRdocPlugin;
})(jsPsychModule);
