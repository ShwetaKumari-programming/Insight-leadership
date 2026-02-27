def transaction_summary(df):
    total = len(df)
    success = len(df[df["transaction_status"] == "Success"])
    failure = len(df[df["transaction_status"] == "Failure"])

    return {
        "total_transactions": total,
        "success_rate": round((success / total) * 100, 2),
        "failure_rate": round((failure / total) * 100, 2)
    }


def failure_by_state(df):
    result = (
        df[df["transaction_status"] == "Failure"]
        .groupby("state")
        .size()
        .sort_values(ascending=False)
    )
    return result


def peak_failure_hours(df):
    failures = df[df["transaction_status"] == "Failure"].copy()
    failures["hour"] = failures["transaction_time"].dt.hour

    return failures.groupby("hour").size().sort_values(ascending=False)


def avg_spend_by_category(df):
    return (
        df.groupby("category")["amount"]
        .mean()
        .round(2)
        .sort_values(ascending=False)
    )


def device_success_rate(df):
    device_stats = (
        df.groupby("device_type")["transaction_status"]
        .value_counts(normalize=True)
        .unstack()
    )
    return (device_stats * 100).round(2)


def fraud_overview(df):
    fraud_count = df["fraud_flag"].sum()
    total = len(df)

    return {
        "fraud_transactions": fraud_count,
        "fraud_percentage": round((fraud_count / total) * 100, 2)
    }


def filter_by_state(df, state):
    return df[df["state"].str.lower() == state.lower()]


def filter_by_category(df, category):
    return df[df["category"].str.lower() == category.lower()]


def filter_night_transactions(df):
    df = df.copy()
    df["hour"] = df["transaction_time"].dt.hour
    return df[(df["hour"] >= 20) & (df["hour"] <= 23)]


def filter_weekend(df):
    df = df.copy()
    df["day"] = df["transaction_time"].dt.dayofweek
    return df[df["day"] >= 5]


def failure_analysis_last_weekend(df, state):
    filtered = filter_by_state(df, state)
    weekend_data = filter_weekend(filtered)

    total = len(weekend_data)
    failures = weekend_data[weekend_data["transaction_status"] == "Failure"]

    failure_rate = round((len(failures) / total) * 100, 2)

    device_breakdown = (
        failures.groupby("device_type")
        .size()
        .sort_values(ascending=False)
        .to_dict()
    )

    network_breakdown = (
        failures.groupby("network_type")
        .size()
        .sort_values(ascending=False)
        .to_dict()
    )

    return {
        "failure_rate": failure_rate,
        "top_device": max(device_breakdown, key=device_breakdown.get),
        "top_network": max(network_breakdown, key=network_breakdown.get),
        "device_distribution": device_breakdown,
        "network_distribution": network_breakdown
    }


def highest_spending_age_group_night_food(df):
    night_data = filter_night_transactions(df)
    food_data = filter_by_category(night_data, "Food")

    age_spend = (
        food_data.groupby("age_group")["amount"]
        .mean()
        .round(2)
    )

    top_age_group = age_spend.idxmax()

    return {
        "top_age_group": top_age_group,
        "average_spend": age_spend[top_age_group],
        "all_age_groups": age_spend.to_dict()
    }


def compare_device_success_rate(df):
    stats = (
        df.groupby("device_type")["transaction_status"]
        .value_counts(normalize=True)
        .unstack()
        .fillna(0)
        * 100
    )

    return stats.round(2).to_dict()


def state_failure_rate(df):
    state_stats = (
        df.groupby("state")["transaction_status"]
        .apply(lambda x: (x == "Failure").mean() * 100)
        .round(2)
    )

    return state_stats.sort_values(ascending=False).to_dict()
