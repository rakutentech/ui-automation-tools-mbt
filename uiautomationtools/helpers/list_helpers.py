def unique_subsets(super_set, constraint):
    """
    This finds the minimum subset of a list of lists.

    Args:
        super_set (list<list>): The list to whittle down.
        constraint (list): The constraint set.

    Returns:
        all_encompassing (list): The minified list of lists.
        constraint (list): The remaining constraints.

    """
    all_encompassing = []
    constraint = set(constraint)
    for sub_set in super_set:
        if set(sub_set) <= constraint:
            all_encompassing.append(sub_set)
            constraint -= set(sub_set)
    return all_encompassing, list(constraint)
