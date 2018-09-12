def is_ok(_, state):
    return state.end_index < 3


def not_ok(_, state):
    return False
