"""
Pulled from:
https://github.com/Dev-Logan-Bennett/expfactory-experiments-rdoc/blob/main/analysis/qc_data.ipynb
"""


def get_stopping_data(df, split_by_block_num=False):
    """
    Extracts and calculates metrics related to 'stop' and 'go' conditions for test trials.

    The function processes data to compute key metrics, including accuracy, response time (rt),
    stop signal delay (SSD), and omission rates, for both 'stop' and 'go' trial conditions.
    The results can be grouped by block numbers if required.

    Input:
      df: DataFrame containing task data for a specific task for a single subject.
      split_by_block_num (optional): Boolean flag to determine if results should be grouped
      by block number (default is False).

    Output:
      Returns the computed metrics either grouped by block numbers or in an aggregated form.

    Metrics Calculated:
      - stop_acc: Mean accuracy for 'stop' trials.
      - go_acc: Mean accuracy for 'go' trials.
      - avg_go_rt: Average response time for correct 'go' trials.
      - max_SSD: Maximum stop signal delay.
      - min_SSD: Minimum stop signal delay.
      - mean_SSD: Average stop signal delay.
      - stop_success: Percentage of successful stops.
      - stop_fail: Percentage of failed stops.
      - go_success: Percentage of successful 'go' trials.
      - stop_omission_rate: Omission rate for 'stop' trials.
      - go_omission_rate: Omission rate for 'go' trials.
    """
    test_trials__df = df[(df["trial_id"] == "test_trial")]

    grouping_column = "block_num" if split_by_block_num else None

    # If we're splitting by block_num, group the data by block_num
    if split_by_block_num:
        stop_trials = test_trials__df[(test_trials__df["condition"] == "stop")].groupby(
            grouping_column
        )
        go_trials = test_trials__df[(test_trials__df["condition"] == "go")].groupby(
            grouping_column
        )
    else:
        stop_trials = test_trials__df[(test_trials__df["condition"] == "stop")]
        go_trials = test_trials__df[(test_trials__df["condition"] == "go")]

    # Define a helper function to calculate metrics for a given group
    def calculate_metrics(group):
        stop_acc = group[group["condition"] == "stop"]["stop_acc"].mean()
        go_acc = group[group["condition"] == "go"]["go_acc"].mean()

        go_correct_trials = group[(group["condition"] == "go") & (group["go_acc"] == 1)]
        avg_go_rt = go_correct_trials["rt"].mean()

        max_SSD = group["SSD"].max()
        min_SSD = group["SSD"].min()
        mean_SSD = group["SSD"].mean()

        stop_success = group[group["condition"] == "stop"]["stop_acc"].mean()
        stop_fail = 1 - stop_success

        go_success = group[group["condition"] == "go"]["go_acc"].mean()
        stop_omission_rate = group[group["condition"] == "stop"]["rt"].isna().mean()
        go_omission_rate = group[group["condition"] == "go"]["rt"].isna().mean()

        return {
            "stop_acc": stop_acc,
            "go_acc": go_acc,
            "avg_go_rt": avg_go_rt,
            "max_SSD": max_SSD,
            "min_SSD": min_SSD,
            "mean_SSD": mean_SSD,
            "stop_success": stop_success,
            "stop_fail": stop_fail,
            "go_success": go_success,
            "stop_omission_rate": stop_omission_rate,
            "go_omission_rate": go_omission_rate,
        }

    # If we're splitting by block_num, apply the helper function to each group
    if split_by_block_num:
        results = test_trials__df.groupby(grouping_column).apply(calculate_metrics)
    else:
        results = calculate_metrics(test_trials__df)
    return results


def calculate_attention_check_accuracy(df):
    """
    Calculates the attention check accuracy for attention checks

    This function computes the accuracy for a given set of attention checks for a single task df.

    Input:
      df: DataFrame containing task data for a specific task for a single subject.

    Output:
        Returns overall attention check accuracy for a given task df for a single subject.
    """

    test_trials__df = df[(df["trial_id"] == "test_attention_check")]
    attention_check_accuracy = test_trials__df["correct_trial"].mean()
    return attention_check_accuracy


def calculate_average_rt(
    df,
    condition_col="condition",
    test_trial="test_trial",
    correct_trial_col="correct_trial",
    factorial_condition=False,
    factorial_conditions=[],
    split_by_block_num=False,
    **kwargs,
):
    """
    Calculates the average reaction time (RT) for given test trials based on specific conditions.

    This function can handle both standard conditions and factorial conditions. Additionally,
    results can optionally be split by block number.

    Input:
      df: DataFrame containing the task data.
      condition_col: Name of the column representing the condition. Default is 'condition'.
      test_trial: Name of the column indicating the type of trial. Default is 'test_trial'.
      correct_trial_col: Column indicating if the trial was correctly executed. Default is 'correct_trial'.
      factorial_condition: Boolean to specify if the data has factorial conditions. Default is False.
      factorial_conditions: List of columns indicating factorial conditions. Default is [].
      split_by_block_num: Boolean to specify if results should be split by block number. Default is False.

    Output:
      Returns the average RT for the specified conditions.
    """
    test_trials__df = df[(df["trial_id"] == test_trial) & (df[correct_trial_col] == 1)]

    if factorial_condition:
        grouping_columns = factorial_conditions
    else:
        grouping_columns = [condition_col]

    if split_by_block_num:
        grouping_columns.append("block_num")

    rt_by_condition = test_trials__df.groupby(grouping_columns).apply(
        lambda group: group["rt"].mean()
    )

    return rt_by_condition.to_json()


def calculate_omission_rate(
    df,
    test_trial="test_trial",
    condition_col="condition",
    factorial_condition=False,
    factorial_conditions=[],
    split_by_block_num=False,
    **kwargs,
):
    """
    Calculates the omission rate for given test trials based on specific conditions.

    Omission rate refers to the proportion of missing reaction times (RTs) in the data. This function
    supports calculations for both standard and factorial conditions. Results can optionally be split
    by block number.

    Input:
       df: DataFrame containing task data for a specific task for a single subject.
      test_trial: Name of the column indicating the type of trial. Default is 'test_trial'.
      condition_col: Name of the column representing the condition. Default is 'condition'.
      factorial_condition: Boolean to specify if the data has factorial conditions. Default is False.
      factorial_conditions: List of columns indicating factorial conditions. Default is [].
      split_by_block_num: Boolean to specify if results should be split by block number. Default is False.

    Output:
      Returns the omission rate for the specified conditions.
    """

    test_trials__df = df[df["trial_id"] == test_trial]

    if factorial_condition:
        grouping_columns = factorial_conditions
    else:
        grouping_columns = [condition_col]

    if split_by_block_num:
        grouping_columns.append("block_num")

    omission_rate = test_trials__df.groupby(grouping_columns).apply(
        lambda group: group["rt"].isna().mean()
    )

    return omission_rate.to_json()



def calculate_omission_rate__span(df):
    """
    Calculates the omission rate for the 'span' task based on specific trial types and response lengths.

    This function targets the 'span' task data to calculate two types of omissions:
    1) Completely empty responses, and
    2) Incomplete responses (i.e., responses with a length between 1 and 3).

    Additionally, this function calculates the omission rate for 'test_inter-stimulus' trials,
    which is the proportion of missing reaction times (RTs) in these trials.

    Input:
       df: DataFrame containing task data for a specific task for a single subject.

    Output:
      Returns the mean number of empty responses, the mean number of incomplete responses,
      and the omission rate for 'test_inter-stimulus' trials.
    """

    test_response_trials__df = df[df["trial_id"] == "test_response"].copy()
    test_processing_trials__df = df[df["trial_id"] == "test_inter-stimulus"].copy()

    # Convert the strings in the 'response' column to actual lists
    test_response_trials__df["response"] = test_response_trials__df["response"]

    omission_rate_processing_trials = test_processing_trials__df["rt"].isna().mean()

    # Calculate the number of empty and incomplete responses
    test_response_trials__df["empty"] = test_response_trials__df["response"].apply(
        lambda x: len(x) == 0
    )
    test_response_trials__df["incomplete"] = test_response_trials__df["response"].apply(
        lambda x: 0 < len(x) < 4
    )

    # Get the mean of each type
    mean_empty = test_response_trials__df["empty"].mean()
    mean_incomplete = test_response_trials__df["incomplete"].mean()

    # Return the results as a dictionary
    return {
        "omission_rate_empty_response_trials": mean_empty,
        "omission_rate_incomplete_response_trials": mean_incomplete,
        "omission_rate_processing_trials": omission_rate_processing_trials,
    }


def calculate_average_accuracy(
    df,
    correct_trial_col="correct_trial",
    condition_col="condition",
    test_trial="test_trial",
    factorial_condition=False,
    factorial_conditions=[],
    split_by_block_num=False,
    **kwargs,
):
    """
    Calculates the average accuracy for given test trials based on specified conditions.

    This function computes the mean accuracy for a given set of test trials. It allows for grouping
    by a single condition or multiple factorial conditions. The option to further split by block number
    is also available. The accuracy is determined by averaging the values in the `correct_trial_col`.

    Input:
      df: DataFrame containing task data for a specific task for a single subject.
      correct_trial_col (optional): Name of the column indicating correct trials (default is 'correct_trial').
      condition_col (optional): Name of the main condition column for grouping (default is 'condition').
      test_trial (optional): Specifies the trial type to be considered for accuracy calculation (default is 'test_trial').
      factorial_condition (optional): Boolean flag indicating if factorial conditions should be used for grouping (default is False).
      factorial_conditions (optional): List of columns to be used for factorial grouping (default is an empty list).
      split_by_block_num (optional): Boolean flag to determine if results should be split by block number (default is False).

    Output:
      Returns the average accuracy grouped by the specified conditions.
    """

    test_trials__df = df[df["trial_id"] == test_trial]

    if factorial_condition:
        grouping_columns = factorial_conditions
    else:
        grouping_columns = [condition_col]

    if split_by_block_num:
        grouping_columns.append("block_num")

    accuracy_by_condition = test_trials__df.groupby(grouping_columns)[
        correct_trial_col
    ].mean()

    return accuracy_by_condition.to_json()


kwargs_lookup = {
    "ax_cpt": {"test_trial": "test_probe"},
    "cued_ts": {
        "factorial_condition": True,
        "factorial_conditions": ["cue_condition", "task_condition"],
    },
    "flanker": {},
    "go_nogo": {},
    "n_back": {"condition_col": "delay"},
    "span": {
        "test_trial": "test_inter-stimulus",
        "correct_trial_col": "correct_response",
    },
    "spatial_ts": {},
    "spatial_cueing": {},
    "stroop": {},
    "stop_signal": {},
    "visual_search": {
        "factorial_condition": True,
        "factorial_conditions": ["condition", "num_stimuli"],
    },
}


def apply_qa_funcs(task__name, task__df):
    kwargs = kwargs_lookup.get(task__name, None)
    if kwargs is None:
        return None, None
    ret_metrics = {}
    ret_error = None
    try:
        ret_metrics["attention_check_accuracy"] = calculate_attention_check_accuracy(
            task__df
        )
        if (task__name == 'stop_signal'):
            ret_metrics["stopping_data"] = get_stopping_data(task__df)
        else:
            ret_metrics["omissions"] = calculate_omission_rate(task__df, **kwargs)
            ret_metrics["accuracies"] = calculate_average_accuracy(task__df, **kwargs)
            ret_metrics["rts"] = calculate_average_rt(task__df, **kwargs)
    except Exception as e:
        ret_error = e
    return ret_metrics, ret_error


def check_same_response(
    df, test_trial="test_trial", task=None, correct_trial="correct_trial"
):
    """
    Checks to see if the subject is only responding with a single key. This could be an issue for certain tasks
    in which accuracies is not enough to catch such behavior (e.g. subject could only respond mismatch in nback and still
    achieve an 80% accuracy.)

    Tasks that could have this issue are: n-back, go-nogo, stop-signal

    Input:
       df: DataFrame containing task data for a specific task for a single subject.

    Output:
      Returns proportion of same, single responses for single condition (helps us determine if subject is doing task, e.g., if only go-ing in
      go_nogo this may not be captured by accuracy, but if only responding go (,) then this will be captured using this function)
    """
    test_response_trials__df = df[df["trial_id"] == test_trial].copy()

    if task == "go_nogo":
        correct_response = df[(df["correct_trial"] == 1) & (df["condition"] == "go")][
            "response"
        ].unique()[0]

        length_go = len(df[df["response"] == correct_response])
        proportion_go = length_go / len(test_response_trials__df)
        proportions = {}
        proportions["go"] = proportion_go
        return proportions

    if task == "n_back":
        value_counts = test_response_trials__df["response"].value_counts()

        proportions = value_counts / test_response_trials__df["response"].count()
        mismatch_correct_response = df[
            (df["correct_trial"] == 1) & (df["condition"] == "mismatch")
        ]["response"].unique()[0]

        match_correct_response = df[
            (df["correct_trial"] == 1) & (df["condition"] == "match")
        ]["response"].unique()[0]

        if mismatch_correct_response in proportions:
            proportions["mismatch"] = proportions[mismatch_correct_response]
            del proportions[mismatch_correct_response]

        if match_correct_response in proportions:
            proportions["match"] = proportions[match_correct_response]
            del proportions[match_correct_response]

        return proportions.to_json()


def calculate_partial_accuracy__span(df):
    """
    Calculates partial accuracy for span. For example, if response is [1,2,3,5] and correct response is [1,2,3,4], the
    accuracy would be calculated as .75 for this row, since they selected 3 spatial stimuli correctly. The order does not
    matter, and it can handle responses with fewer than 4 selected.

    Input:
       df: DataFrame containing span task data for a specific task for a single subject.

    Output:
      Returns proportion of partial correct responses, average partial accuracy for all rows in df.
    """

    test_response_trials__df = df[df["trial_id"] == "test_response"].copy()
    responses = test_response_trials__df["response"]
    correct_spatial_sequences = test_response_trials__df["spatial_sequence"]

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
