from app.services.cost import calculate_cost


def test_calculate_cost_for_known_model():
    cost = calculate_cost("gpt-4o-mini", prompt_tokens=1000, completion_tokens=1000)
    assert cost == 0.00075
