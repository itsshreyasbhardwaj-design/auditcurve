from auditcurve.tasks.registry import all_tasks, get_task


def test_all_tasks_registers_exactly_eight_tasks():
    tasks = all_tasks()
    assert len(tasks) == 8
    assert len({t.task_id for t in tasks}) == 8  # no duplicate ids


def test_three_domains_represented():
    domains = {t.domain for t in all_tasks()}
    assert domains == {"refunds", "travel", "expenses"}


def test_get_task_by_id():
    task = get_task("refunds_001_large_amount")
    assert task.domain == "refunds"
    assert task.evaluator is not None


def test_every_task_has_at_least_one_tool_and_one_policy():
    for task in all_tasks():
        assert task.tool_schemas
        assert task.policy_constraints
        assert task.user_request
        assert task.system_prompt
