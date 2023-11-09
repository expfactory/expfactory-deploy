attention_check_accuracy__threshold = 0.5

mean_accuracy__thresholds = {
    'ax_cpt': {'AX': 0.9, 'BX': 0.75, 'AY': 0.75, 'BY': 0.75},
    'cued_ts': {('switch', 'switch'): .85, ('switch', 'stay'): .9, ('stay', 'stay'): .9},
    'flanker': {'congruent': 0.9, 'incongruent': 0.75},
    'go_nogo': {'go': 0.9, 'nogo': 0.7},
    'n_back': {1.0: 0.8, 2.0: 0.7},
    'span': {'response': .5, 'processing': .5},
    'spatial_cueing': {'valid': 0.85, 'invalid': 0.75, 'nocue': 0.8, 'doublecue': 0.8},
    'spatial_ts': {'tswitch_cswitch': 0.85, 'tstay_cstay': 0.9, 'tstay_cswitch': .9},
    'stop_signal': 0.9,
    'stroop': {'congruent': 0.9, 'incongruent': 0.7},
    'visual_search':{
    ('conjunction', 8.0): 0.95,
    ('conjunction', 24.0): 0.85,
    ('feature', 8.0): 0.99,
    ('feature', 24.0): 0.95
    }
}

mean_rt__thresholds = {
    'ax_cpt': {'AX': 750, 'BX': 900, 'AY': 850, 'BY': 900},
    'cued_ts': {('switch', 'switch'): 900, ('switch', 'stay'): 700, ('stay', 'stay'): 700},
    'flanker': {'congruent': 600, 'incongruent': 800},
    'go_nogo': {'go': 700},
    'n_back': {1.0: 850, 2.0: 950},
    'span': {'response': 1000, 'processing': 1000},
    'spatial_cueing': {'valid': 650, 'invalid': 750, 'nocue': 700, 'doublecue': 700},
    'spatial_ts': {'tswitch_cswitch': 900, 'tstay_cstay': 700, 'tstay_cswitch': 700},
    'stop_signal': 650,
    'stroop': {'congruent': 650, 'incongruent': 900},
    'visual_search': {
    ('conjunction', 8.0): 1000,
    ('conjunction', 24.0): 1200,
    ('feature', 8.0): 600,
    ('feature', 24.0): 800
}
}

omission_rate__thresholds = {
    'ax_cpt': .1,
    'cued_ts': {('switch', 'switch'): .1, ('switch', 'stay'): .1, ('stay', 'stay'): .1},
    'flanker': 0.1,
    'go_nogo': {'go': 0.1},
    'n_back': {1.0: 0.1, 2.0: 0.15},
    'span': {'response': .2, 'processing': .2},
    'spatial_cueing': {'valid': 0.1, 'invalid': 0.1, 'nocue': 0.1, 'doublecue': 0.1},
    'spatial_ts': {'tswitch_cswitch': .1, 'tstay_cstay': .1, 'tstay_cswitch': .1},
    'stop_signal': 0.1,
    'stroop': 0.1,
    'visual_search': {
    ('conjunction', 8.0): 0.1,
    ('conjunction', 24.0): 0.15,
    ('feature', 8.0): 0.05,
    ('feature', 24.0): 0.1
}
}

# Define the stopping task thresholds
mean_stopping__thresholds = {
    'stop_signal': {
        'stop_acc': 0.7,
        'go_acc': 0.7,
        'avg_go_rt': 600,
        'stop_success': 0.5,
        'stop_fail': 0.5,
        'go_success': 0.5,
        'stop_omission_rate': 0.2,
        'go_omission_rate': 0.2
    }
}

# Define the 'span' task thresholds outside of the function
mean_span__thresholds = {
    'accuracy': {
        'same-domain': 0.7,
        'storage-only': 0.6,
    },
    'rt': {
        'same-domain': 700,
    },
    'omission': {
        'omission_rate_empty_response_trials': 0.2,
        'omission_rate_incomplete_response_trials': 0.1,
        'omission_rate_processing_trials': 0.3,
    }
}

def feedback_generator(task, accuracies=None, rts=None, omissions=None, attention_check_accuracy=None, factorial_condition=False, stopping_data=None):
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
                condition_label = ' and '.join(condition) if factorial_condition else condition
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
                condition_label = ' and '.join(condition) if factorial_condition else condition
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
                condition_label = ' and '.join(condition) if factorial_condition else condition
                feedback = f"Your average RT of {value:.2f}ms is high for the {condition_label} condition of {task}."
                feedbacks.append(feedback)

    if attention_check_accuracy is not None:
        if attention_check_accuracy < attention_check_accuracy__threshold:
            feedback = f"Your attention check accuracy of {attention_check_accuracy*100:.2f}% is below the required threshold of {attention_check_accuracy__threshold*100:.2f}%. Please ensure you are remaining attentive throughout the tasks."
            feedbacks.append(feedback)

    if stopping_data and task == 'stop_signal':
        stopping_thresholds = mean_stopping__thresholds[task]
        for metric, value in stopping_data.items():
            threshold = stopping_thresholds.get(metric)
            if threshold is not None:
                if 'acc' in metric and value < threshold:
                    feedback = f"Your {metric.replace('_', ' ')} of {value*100:.2f}% is below the threshold of {threshold*100:.2f}%."
                    feedbacks.append(feedback)
                elif 'rt' in metric and value > threshold:
                    feedback = f"Your {metric.replace('_', ' ')} of {value:.2f}ms is above the threshold of {threshold:.2f}ms."
                    feedbacks.append(feedback)
                elif 'omission_rate' in metric and value > threshold:
                    feedback = f"Your {metric.replace('_', ' ')} of {value*100:.2f}% is above the threshold of {threshold*100:.2f}%."
                    feedbacks.append(feedback)

    # Section to handle 'span' task feedback
    if task == 'span':
        span_accuracy_thresholds = mean_span__thresholds['accuracy']
        span_rt_thresholds = mean_span__thresholds['rt']
        span_omission_thresholds = mean_span__thresholds['omission']

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


