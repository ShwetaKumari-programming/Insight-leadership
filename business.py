from transaction import (
    compare_device_success_rate,
    failure_analysis_last_weekend,
    highest_spending_age_group_night_food,
    state_failure_rate,
)


def business_logic_router(intent, entities, df):
    if intent == "failure_analysis_weekend":
        return failure_analysis_last_weekend(
            df, entities.get("state", "Maharashtra")
        )

    elif intent == "top_spending_age_group":
        return highest_spending_age_group_night_food(df)

    elif intent == "device_comparison":
        return compare_device_success_rate(df)

    elif intent == "state_failure_rate":
        return state_failure_rate(df)

    else:
        return {"error": "Intent not supported yet"}


def generate_failure_insight(result, state):
    return (
        f"Transaction failures in {state} increased to {result['failure_rate']}% "
        f"last weekend. The majority of failures occurred on "
        f"{result['top_device']} devices, primarily over "
        f"{result['top_network']} networks. "
        f"This suggests a need to optimize system performance "
        f"for high-traffic periods on these platforms."
    )


def generate_spending_insight(result):
    return (
        f"The {result['top_age_group']} age group has the highest average "
        f"night-time food spending at INR {result['average_spend']}. "
        f"This indicates a strong opportunity for targeted promotions "
        f"during evening hours for this segment."
    )


def generate_device_comparison_insight(result):
    android_success = result["Android"].get("Success", 0)
    ios_success = result["iOS"].get("Success", 0)

    better_device = "Android" if android_success > ios_success else "iOS"

    return (
        f"{better_device} devices show a higher transaction success rate. "
        f"Android success rate is {android_success}% while iOS success rate "
        f"is {ios_success}%. Monitoring platform-specific performance "
        f"can help improve overall reliability."
    )


def generate_state_risk_insight(result):
    top_state = max(result, key=result.get)

    return (
        f"{top_state} has the highest transaction failure rate at "
        f"{result[top_state]}%. This region should be prioritized "
        f"for network and infrastructure improvements."
    )


def insight_text_router(intent, analysis_result, entities=None):
    entities = entities or {}

    if intent == "failure_analysis_weekend":
        return generate_failure_insight(
            analysis_result,
            entities.get("state", "the selected state")
        )

    elif intent == "top_spending_age_group":
        return generate_spending_insight(analysis_result)

    elif intent == "device_comparison":
        return generate_device_comparison_insight(analysis_result)

    elif intent == "state_failure_rate":
        return generate_state_risk_insight(analysis_result)

    else:
        return "Insight generation for this query is not supported yet."
