thresholds = {
    "ax_cpt_rdoc": {"accuracy": 0.6, "rt": 1000, "omissions": 0.2},
    "cued_task_switching_rdoc": {"accuracy": 0.6, "rt": 1000, "omissions": 0.2},
    "flanker_rdoc": {"accuracy": 0.6, "rt": 1000, "omissions": 0.2},
    "go_nogo_rdoc": {
        "accuracy": 0.6,
        "rt": 1000,
        "omissions": 0.2,
        "check_response": 0.9,
    },
    "n_back_rdoc": {
        "accuracy": 0.6,
        "rt": 1000,
        "omissions": 0.2,
        "check_response": 0.9,
    },
    "span_rdoc__behavioral": {"accuracy": 0.25, "rt": 1000, "omissions": 0.2},
    "simple_span_rdoc": {"accuracy": 0.25, "rt": 1000, "omissions": 0.2},
    "operation_span_rdoc": {"accuracy": 0.25, "rt": 1000, "omissions": 0.2},
    "color_discrimination_rdoc": {"accuracy": 0.8, "rt": 3000, "omissions": 0.2},
    "spatial_cueing_rdoc": {"accuracy": 0.6, "rt": 1000, "omissions": 0.2},
    "spatial_task_switching_rdoc": {"accuracy": 0.6, "rt": 1000, "omissions": 0.2},
    "stop_signal_rdoc": {"accuracy": 0.6, "rt": 1000, "omissions": 0.2},
    "stroop_rdoc": {"accuracy": 0.6, "rt": 1000, "omissions": 0.2},
    "visual_search_rdoc": {"accuracy": 0.6, "rt": 1500, "omissions": 0.2},
    "post_battery_feedback_rdoc": {"rt": 30_000, "feedback": ""},
    "race_ethnicity_RMR_survey_rdoc": {"rt": 120000, "omissions": 1},
    "demographics_survey_rdoc": {"rt": 600000, "omissions": 4},
    "dospert_rt_survey_rdoc": {"rt": 120000, "omissions": 0},
    "risq_survey_rdoc": {"rt": 600000, "omissions": 82},
    "dospert_eb_survey_rdoc": {"rt": 600000, "omissions": 0},
    "k6_survey_rdoc": {"rt": 600000, "omissions": 7},
    "childhood_trauma_survey_rdoc": {"rt": 600000, "omissions": 0},
    "dass21_survey_rdoc": {"rt": 600000, "omissions": 0},
    "fagerstrom_test_survey_rdoc": {"rt": 600000, "omissions": 0},
    "brief_self_control_survey_rdoc": {"rt": 600000, "omissions": 0},
    "dsm5_crosscutting_stanford_baseline_rdoc": {"rt": 600000, "omissions": 0},
    "three_factor_eating_questionnaire_r18__stanford_baseline_rdoc": {"rt": 600000, "omissions": 0},
    "psqi_survey_rdoc": {"rt": 600000, "omissions": 4},
    "upps_impulsivity_survey_rdoc": {"rt": 600000, "omissions": 0},
    "panas_last_two_weeks_survey_rdoc": {"rt": 600000, "omissions": 0},
    "dospert_rp_survey_rdoc": {"rt": 600000, "omissions": 0},
    "mcarthur_social_status_survey_rdoc": {'rt': 200000, 'omissions': 0},
    "l_cat_survey_rdoc": {"rt": 200000, "omissions": 0}
}

def apply_qa_funcs(task_name, task_df):
    metrics = {}
    error = None
    feedback = ""

    try:
        if "survey" not in task_name and "questionnaire" not in task_name and "dsm5" not in task_name and "feedback" not in task_name:
            metrics["attention_check_accuracy"] = get_attention_check_accuracy(task_df)

        if task_name != "stop_signal_rdoc" and "survey" not in task_name and "questionnaire" not in task_name and "dsm5" not in task_name and "feedback" not in task_name:
            metrics["accuracy"] = get_accuracy(task_df)

        span_tasks = ["simple_span_rdoc", "operation_span_rdoc", "span_rdoc__behavioral"]

        if task_name in span_tasks:
            average_rt, average_accuracy = get_span_processing(task_df)
            metrics["rt"] = average_rt
            metrics['processing_accuracy'] = average_accuracy
            metrics["omissions"] = get_span_omissions(task_df)
            metrics["accuracy"] = get_span_accuracy(task_df)
        elif task_name == "stop_signal_rdoc":
            metrics.update(**get_stopping(task_df))
            metrics['accuracy'] = metrics['go_accuracy']
        elif task_name == "post_battery_feedback_rdoc":
            feedback, rt = get_post_battery_feedback(task_df)
            metrics["rt"] = rt
            metrics['feedback'] = feedback
        elif "survey" in task_name or "questionnaire" in task_name or "dsm5" in task_name:
            average_rt, omissions, all_values_same = get_survey_metrics(task_df, task_name)
            metrics["rt"] = average_rt
            metrics["omissions"] = omissions
            metrics["all_values_same"] = all_values_same
        else:
            metrics["rt"] = get_average_rt(task_df)
            metrics["omissions"] = get_omissions(task_df)

        if task_name == "n_back_rdoc":
            metrics["check_response"] = check_n_back_responses(task_df)
        elif task_name == "go_nogo_rdoc":
            metrics["check_response"] = check_go_nogo_responses(task_df)
        else:
            metrics["check_response"] = None
    except Exception as e:
        return metrics, feedback, e
    try:
        feedback = feedback_generator(task_name, **metrics)
    except Exception as e:
        error = e
    return metrics, feedback, error


def feedback_generator(
    task_name,
    attention_check_accuracy=None,
    accuracy=None,
    rt=None,
    omissions=None,
    check_response=None,
    all_values_same=None,
    **kwargs,
):
    feedbacks = []
    threshold = thresholds[task_name]

    if task_name == "post_battery_feedback_rdoc":
        if rt > threshold["rt"]:
            feedback = f"Overall rt of {rt} is high for {task_name}."
            feedbacks.append(feedback)
        if kwargs['feedback'] != threshold['feedback']:
            feedback = f"Subject gave post-battery feedback."
            feedbacks.append(feedback)
        return feedbacks

    if "survey" in task_name or "questionnaire" in task_name or "dsm5" in task_name:
        if rt > threshold["rt"]:
            feedback = f"Overall rt of {rt} is high for {task_name}."
            feedbacks.append(feedback)
        if omissions > threshold["omissions"]:
            feedback = f"Subject did not answer all required questions."
            feedbacks.append(feedback)
        if all_values_same:
            feedback = f"Subject gave the same response for all questions."
            feedbacks.append(feedback)
        return feedbacks

    if attention_check_accuracy < 0.6:
        feedback = f"Overall attention check accuracy of {attention_check_accuracy*100:.2f}% is low for {task_name}."
        feedbacks.append(feedback)

    if accuracy < threshold["accuracy"]:
        feedback = (
            f"Overall task accuracy of {accuracy*100:.2f}% is low for {task_name}."
        )
        feedbacks.append(feedback)
    if rt > threshold["rt"]:
        feedback = f"Overall rt of {rt} is high for {task_name}."
        feedbacks.append(feedback)
    if omissions > threshold["omissions"]:
        feedback = f"Overall omissions of {omissions*100:.2f}% is high for {task_name}."
        feedbacks.append(feedback)

    if check_response is not None:
        if check_response > threshold["check_response"]:
            feedback = f"Single response proportion of {check_response} is high for {task_name}."
            feedbacks.append(feedback)

    if task_name == 'stop_signal_rdoc':
        stop_accuracy = kwargs['stop_accuracy']
        if stop_accuracy < 0.25:
            feedback = f"Stop accuracy of {stop_accuracy*100:.2f}% is too low for {task_name}."
            feedbacks.append(feedback)
        elif stop_accuracy > 0.75:
            feedback = f"Stop accuracy of {stop_accuracy*100:.2f}% is too high for {task_name}."
            feedbacks.append(feedback)

    if task_name == 'operation_span_rdoc':
        processing_accuracy = kwargs['processing_accuracy']
        if processing_accuracy < 0.6:
            feedback = f"Processing accuracy of {processing_accuracy*100:.2f}% is too low for {task_name}."
            feedbacks.append(feedback)
    return feedbacks


def get_attention_check_accuracy(df):
    attention_checks = df[(df["trial_id"] == "test_attention_check")]
    attention_check_accuracy = attention_checks["correct_trial"].mean()
    return attention_check_accuracy


def get_post_battery_feedback(df):
    df = df[df["trial_id"] == "post_battery_feedback"]
    feedback = df["response"].dropna().iloc[0]
    rt = df["rt"].dropna().iloc[0]
    return feedback, rt

def get_survey_metrics(df, task_name):
    total_omissions = 0
    all_values_same = True
    if "fagerstrom" not in task_name:
        df = df[df["trial_type"] == "survey"]
        average_rt = df["rt"].mean()
        for response in df["response"]:
            values = list(response.values())
            if len(values) <= 1 or not all(value == values[0] for value in values):
                all_values_same = False
            for value in values:
                if value == "":
                    total_omissions += 1
    else:
        average_rt = df["rt"].mean()
        for response in df["response"]:
            if df["response"].nunique() > 1:
                all_values_same = False
            if response == "":
                total_omissions += 1

    return average_rt, total_omissions, all_values_same

def get_span_processing(df):
    test_trials = df[df["trial_id"] == "test_inter-stimulus"]
    correct_test_trials = test_trials[test_trials["correct_trial"] == 1]
    average_rt = correct_test_trials["rt"].mean()

    average_accuracy = test_trials["correct_trial"].mean()
    return average_rt, average_accuracy

def get_span_omissions(df):
    test_trials = df[df["trial_id"] == "test_trial"]
    na_count = test_trials["response"].isna().sum()
    proportion = na_count / len(test_trials)
    return proportion


def get_average_rt(df):
    test_trials = df[df["trial_id"] == "test_trial"]
    correct_test_trials = test_trials[test_trials["correct_trial"] == 1]
    average_rt = correct_test_trials["rt"].mean()
    return average_rt


def get_accuracy(df):
    test_trials = df[df["trial_id"] == "test_trial"]
    average_accuracy = test_trials["correct_trial"].mean()
    return average_accuracy


def get_span_accuracy(df):
    test_trials = df[df["trial_id"] == "test_trial"]

    responses = test_trials["response"]
    correct_spatial_sequences = test_trials["spatial_sequence"]

    # Function to calculate the accuracy for each row
    def calculate_accuracy(response, correct_sequence):
        correct_responses = len(set(response).intersection(correct_sequence))
        return correct_responses / len(correct_sequence)

    # Calculating accuracies for each row
    accuracies = [
        calculate_accuracy(resp, corr_seq)
        for resp, corr_seq in zip(responses, correct_spatial_sequences)
    ]

    # Calculating the mean accuracy for the whole dataframe
    mean_accuracy = sum(accuracies) / len(accuracies)
    return mean_accuracy


def get_omissions(df):
    test_trials = df[df["trial_id"] == "test_trial"]
    average_omissions = test_trials["rt"].isna().mean()
    return average_omissions


def check_n_back_responses(df):
    test_trials = df[df["trial_id"] == "test_trial"]
    value_counts = test_trials["response"].value_counts()

    proportions = value_counts / test_trials["response"].count()
    mismatch_correct_response = df[
        (df["correct_trial"] == 1) & (df["condition"] == "mismatch")
    ]["response"].unique()[0]

    return proportions[mismatch_correct_response]


def check_go_nogo_responses(df):
    test_trials = df[df["trial_id"] == "test_trial"]
    space_bar_responses = test_trials[test_trials["response"] == " "]
    prop_resp_go = len(space_bar_responses) / len(test_trials)

    return prop_resp_go


def get_stopping(df):
    test_trials = df[df["trial_id"] == "test_trial"]
    go_trials = test_trials[test_trials["condition"] == "go"]
    correct_go_trials = go_trials[go_trials["correct_trial"] == 1]
    stop_trials = test_trials[test_trials["condition"] == "stop"]

    go_accuracy = go_trials["correct_trial"].mean()
    go_omissions = go_trials["rt"].isna().mean()
    stop_accuracy = stop_trials["correct_trial"].mean()
    go_rt = correct_go_trials["rt"].mean()

    max_SSD = test_trials["SSD"].max()
    min_SSD = test_trials["SSD"].min()
    mean_SSD = test_trials["SSD"].mean()

    return {
        "go_accuracy": go_accuracy,
        "omissions": go_omissions,
        "stop_accuracy": stop_accuracy,
        "rt": go_rt,
        "max_SSD": max_SSD,
        "min_SSD": min_SSD,
        "mean_SSD": mean_SSD,
    }
