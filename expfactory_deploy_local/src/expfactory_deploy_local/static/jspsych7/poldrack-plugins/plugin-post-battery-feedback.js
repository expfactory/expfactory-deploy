var PostBatteryFeedback = (function (jspsych) {
  "use strict";

  const info = {
    name: "post-battery-feedback",
    parameters: {
      choices: {
        type: jspsych.ParameterType.KEYS,
        pretty_name: "Choices",
        default: "ALL_KEYS",
      },
      prompt: {
        type: jspsych.ParameterType.HTML_STRING,
        pretty_name: "Prompt",
        default: null,
      },
      html: {
        type: jspsych.ParameterType.HTML_STRING,
        pretty_name: "HTML",
        default: null,
      },
      trial_duration: {
        type: jspsych.ParameterType.INT,
        pretty_name: "Trial duration",
        default: null,
      },
      response_ends_trial: {
        type: jspsych.ParameterType.BOOL,
        pretty_name: "Response ends trial",
        default: true,
      },
    },
  };
  /**
   * PostBatteryFeedback plugin
   *
   * jsPsych plugin for presenting post battery feedback.
   * We needed our own plugin since you can't set trial_duration in default html survey plugin.
   *
   * @author Logan Bennett
   */

  class PostBatteryFeedback {
    constructor(jsPsych) {
      this.jsPsych = jsPsych;
    }
    trial(display_element, trial) {
      var html = "";
      // add prompt
      if (trial.prompt !== null) {
        html += trial.prompt;
      }

      if (trial.html !== null) {
        html += trial.html;
      }

      // add submit button
      html +=
        '<button id="jspsych-my-plugin-submit-button" class="jspsych-btn">Submit</button>';

      // draw
      display_element.innerHTML = html;

      // function to end trial when it is time
      const end_trial = () => {
        // kill any remaining setTimeout handlers
        this.jsPsych.pluginAPI.clearAllTimeouts();
        // kill keyboard listeners
        if (typeof keyboardListener !== "undefined") {
          this.jsPsych.pluginAPI.cancelKeyboardResponse(keyboardListener);
        }

        const response =
          display_element.querySelector("#feedback_response").value;

        var endTime = performance.now();
        var rt = Math.round(endTime - startTime);

        // gather the data to store for the trial
        var trial_data = {
          response,
          rt,
        };
        // clear the display
        display_element.innerHTML = "";
        // move on to the next trial
        this.jsPsych.finishTrial(trial_data);
      };

      const buttonElement = display_element.querySelector(
        "#jspsych-my-plugin-submit-button"
      );
      buttonElement.addEventListener("click", end_trial);

      // end trial if trial_duration is set
      if (trial.trial_duration !== null) {
        this.jsPsych.pluginAPI.setTimeout(end_trial, trial.trial_duration);
      }
      var startTime = performance.now();
    }
  }
  PostBatteryFeedback.info = info;

  return PostBatteryFeedback;
})(jsPsychModule);
