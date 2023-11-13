attention_check_accuracy__threshold = 0.5

# - Decided not to tailor accuracy by condition, instead just doing around random-chance accuracy threholds for all tasks
mean_accuracy__thresholds = {
    "ax_cpt": {"AX": 0.6, "BX": 0.6, "AY": 0.6, "BY": 0.6},
    "cued_ts": {
        ("switch", "switch"): 0.6,
        ("switch", "stay"): 0.6,
        ("stay", "stay"): 0.6,
    },
    "flanker": {"congruent": 0.6, "incongruent": 0.6},
    "go_nogo": {"go": 0.6, "nogo": 0.6},
    "n_back": {1.0: 0.6, 2.0: 0.6},
    "span": {"response": 0.2, "processing": 0.6},
    "spatial_cueing": {"valid": 0.6, "invalid": 0.6, "nocue": 0.6, "doublecue": 0.6},
    "spatial_ts": {"tswitch_cswitch": 0.6, "tstay_cstay": 0.6, "tstay_cswitch": 0.6},
    "stop_signal": 0.5,
    "stroop": {"congruent": 0.6, "incongruent": 0.6},
    "visual_search": {
        ("conjunction", 8.0): 0.6,
        ("conjunction", 24.0): 0.6,
        ("feature", 8.0): 0.6,
        ("feature", 24.0): 0.6,
    },
}

mean_rt__thresholds = {
    "ax_cpt": {"AX": 1000, "BX": 1000, "AY": 1000, "BY": 1000},
    "cued_ts": {
        ("switch", "switch"): 1000,
        ("switch", "stay"): 1000,
        ("stay", "stay"): 1000,
    },
    "flanker": {"congruent": 1000, "incongruent": 1000},
    "go_nogo": {"go": 1000},
    "n_back": {1.0: 1000, 2.0: 1000},
    "span": {"response": 1000, "processing": 1000},
    "spatial_cueing": {
        "valid": 1000,
        "invalid": 1000,
        "nocue": 1000,
        "doublecue": 1000,
    },
    "spatial_ts": {"tswitch_cswitch": 1000, "tstay_cstay": 1000, "tstay_cswitch": 1000},
    "stop_signal": 1000,
    "stroop": {"congruent": 1000, "incongruent": 1000},
    "visual_search": {
        ("conjunction", 8.0): 1500,
        ("conjunction", 24.0): 1500,
        ("feature", 8.0): 1500,
        ("feature", 24.0): 1500,
    },
}

omission_rate__thresholds = {
    "ax_cpt": 0.2,
    "cued_ts": {
        ("switch", "switch"): 0.2,
        ("switch", "stay"): 0.2,
        ("stay", "stay"): 0.2,
    },
    "flanker": 0.2,
    "go_nogo": {"go": 0.2},
    "n_back": {1.0: 0.2, 2.0: 0.2},
    "span": {"response": 0.2, "processing": 0.2},
    "spatial_cueing": {"valid": 0.2, "invalid": 0.2, "nocue": 0.2, "doublecue": 0.2},
    "spatial_ts": {"tswitch_cswitch": 0.2, "tstay_cstay": 0.2, "tstay_cswitch": 0.2},
    "stop_signal": 0.2,
    "stroop": 0.2,
    "visual_search": {
        ("conjunction", 8.0): 0.2,
        ("conjunction", 24.0): 0.2,
        ("feature", 8.0): 0.2,
        ("feature", 24.0): 0.2,
    },
}

# Define the stopping task thresholds
mean_stopping__thresholds = {
    "stop_signal": {
        "stop_acc": 0.5,
        "go_acc": 0.5,
        "avg_go_rt": 1000,
        "stop_success": 0.5,
        "stop_fail": 0.5,
        "go_success": 0.5,
        "stop_omission_rate": 0.6,
        "go_omission_rate": 0.2,
    }
}

# Define the 'span' task thresholds outside of the function
# - Decided to include partial_response accuracy to capture accuracy for select responses, regardless of order. e.g., subject chooses
# [1,2,3] but correct response is [2,5,9,14] they would get .25 proportion accuracy on this trial. This helps us determine
# if they were actually trying to do the task
mean_span__thresholds = {
    "accuracy": {"same-domain": 0.2, "storage-only": 0.2, "partial_response": 0.25},
    "rt": {
        "same-domain": 1250,
    },
    "omission": {
        "omission_rate_empty_response_trials": 0.2,
        "omission_rate_incomplete_response_trials": 0.2,
        "omission_rate_processing_trials": 0.2,
    },
}

# Define the 'span' task thresholds outside of the function
mean_same_response__thresholds = {
    "ax_cpt": None,
    "cued_ts": None,
    "flanker": None,
    "go_nogo": {"go": 0.9, "nogo": None},
    "n_back": {"mismatch": 0.9, "match": None},
    "span": None,
    "spatial_cueing": None,
    "spatial_ts": None,
    "stop_signal": {"go": 0.9},
    "stroop": None,
    "visual_search": None,
}


def feedback_generator(
    task,
    accuracies=None,
    rts=None,
    omissions=None,
    attention_check_accuracy=None,
    factorial_condition=False,
    stopping_data=None,
    same_response=None,
    partial_accuracy=None,
):
    feedbacks = []

    def get_threshold(thresholds, condition, factorial_condition):
        if factorial_condition and isinstance(thresholds, dict):
            # For factorial conditions, we expect a dictionary with tuple keys
            return thresholds.get(condition)
        elif not factorial_condition and isinstance(thresholds, dict):
            # For non-factorial conditions, we extract the value using the condition as the key
            return thresholds.get(condition)
        else:
            # When thresholds is not a dictionary, it means it's a direct value applicable to all conditions
            return thresholds

    if accuracies:
        if task not in mean_accuracy__thresholds:
            return ["Invalid task name."]
        for condition, value in accuracies.items():
            threshold = mean_accuracy__thresholds[task]
            target = get_threshold(threshold, condition, factorial_condition)
            if target is None:
                # feedbacks.append(f"Invalid condition {condition} for the task {task}.")
                continue
            if value < target:
                condition_label = (
                    " and ".join(condition) if factorial_condition else condition
                )
                feedback = f"Your accuracy of {value*100:.2f}% is low for the {condition_label} condition of {task}."
                feedbacks.append(feedback)

    if omissions:
        if task not in omission_rate__thresholds:
            return ["Invalid task name."]
        for condition, value in omissions.items():
            threshold = omission_rate__thresholds[task]
            target = get_threshold(threshold, condition, factorial_condition)
            if target is None:
                # feedbacks.append(f"Invalid condition {condition} for the task {task}.")
                continue
            if value > target:
                condition_label = (
                    " and ".join(condition) if factorial_condition else condition
                )
                feedback = f"Your omission rate of {value*100:.2f}% is high for the {condition_label} condition of {task}."
                feedbacks.append(feedback)

    if rts:
        if task not in mean_rt__thresholds:
            return ["Invalid task name."]
        for condition, value in rts.items():
            threshold = mean_rt__thresholds[task]
            target = get_threshold(threshold, condition, factorial_condition)
            if target is None:
                # feedbacks.append(f"Invalid condition {condition} for the task {task}.")
                continue
            if value > target:
                condition_label = (
                    " and ".join(condition) if factorial_condition else condition
                )
                feedback = f"Your average RT of {value:.2f}ms is high for the {condition_label} condition of {task}."
                feedbacks.append(feedback)

    if attention_check_accuracy is not None:
        if attention_check_accuracy < attention_check_accuracy__threshold:
            feedback = f"Your attention check accuracy of {attention_check_accuracy*100:.2f}% is below the required threshold of {attention_check_accuracy__threshold*100:.2f}%. Please ensure you are remaining attentive throughout the tasks."
            feedbacks.append(feedback)

    if stopping_data and task == "stop_signal":
        stopping_thresholds = mean_stopping__thresholds[task]
        for metric, value in stopping_data.items():
            threshold = stopping_thresholds.get(metric)
            if threshold is not None:
                if "acc" in metric and value < threshold:
                    feedback = f"Your {metric.replace('_', ' ')} of {value*100:.2f}% is below the threshold of {threshold*100:.2f}%."
                    feedbacks.append(feedback)
                elif "rt" in metric and value > threshold:
                    feedback = f"Your {metric.replace('_', ' ')} of {value:.2f}ms is above the threshold of {threshold:.2f}ms."
                    feedbacks.append(feedback)
                elif "omission_rate" in metric and value > threshold:
                    feedback = f"Your {metric.replace('_', ' ')} of {value*100:.2f}% is above the threshold of {threshold*100:.2f}%."
                    feedbacks.append(feedback)

    if same_response:
        if task not in mean_same_response__thresholds:
            return ["Invalid task name."]
        for response, value in same_response.items():
            threshold = mean_same_response__thresholds[task]
            target = get_threshold(threshold, response, factorial_condition)
            if target is None:
                # feedbacks.append(f"Invalid condition {condition} for the task {task}.")
                continue
            if task == "n_back":
                condition_label = "match"
            elif task == "go_nogo":
                condition_label = "go"
            else:
                condition_label = None
            if value > target:
                feedback = f"Your average proportions of responses of {value:.2f} is high for {condition_label} condition of {task}."
                feedbacks.append(feedback)

    # Section to handle 'span' task feedback
    if task == "span":
        span_accuracy_thresholds = mean_span__thresholds["accuracy"]
        span_rt_thresholds = mean_span__thresholds["rt"]
        span_omission_thresholds = mean_span__thresholds["omission"]

        # Process accuracies for 'span'
        if accuracies:
            for condition, value in accuracies.items():
                threshold = span_accuracy_thresholds.get(condition)
                if threshold is None:
                    # feedbacks.append(f"Invalid condition {condition} for the task {task}.")
                    continue
                if value < threshold:
                    feedback = f"Your accuracy for {condition} is low at {value*100:.2f}%, below the threshold of {threshold*100:.2f}%."
                    feedbacks.append(feedback)

        if partial_accuracy:
            value = partial_accuracy
            threshold = span_accuracy_thresholds["partial_response"]
            if value < span_accuracy_thresholds["partial_response"]:
                feedback = f"Your partial response accuracy for span is low at {value*100:.2f}%, below the threshold of {threshold*100:.2f}%."
                feedbacks.append(feedback)

        # Process RTs for 'span'
        if rts:
            for condition, value in rts.items():
                threshold = span_rt_thresholds.get(condition)
                if threshold is None:
                    # feedbacks.append(f"Invalid condition {condition} for the task {task}.")
                    continue
                if value > threshold:
                    feedback = f"Your reaction time for {condition} is high at {value:.2f}ms, above the threshold of {threshold:.2f}ms."
                    feedbacks.append(feedback)

        # Process omissions for 'span'
        if omissions:
            for metric, value in omissions.items():
                threshold = span_omission_thresholds.get(metric)
                if threshold is None:
                    feedbacks.append(f"Invalid metric {metric} for the task {task}.")
                    continue
                if value > threshold:
                    feedback = f"Your {metric.replace('_', ' ')} is high at {value*100:.2f}%, above the threshold of {threshold*100:.2f}%."
                    feedbacks.append(feedback)

    return feedbacks
