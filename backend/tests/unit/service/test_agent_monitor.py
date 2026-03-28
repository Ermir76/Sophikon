import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.service.agent.loop import ProactiveFindings
from app.tasks.agent_monitor import _run_all_health_checks, _run_proactive_check


def _make_project(project_id=None, owner_id=None):
    project = MagicMock()
    project.id = project_id or uuid.uuid4()
    project.owner_id = owner_id or uuid.uuid4()
    project.organization_id = uuid.uuid4()
    project.name = "Test Project"
    project.is_deleted = False
    project.settings = {}
    return project


def _make_owner(owner_id=None):
    owner = MagicMock()
    owner.id = owner_id or uuid.uuid4()
    owner.preferences = {}
    return owner


def _make_db(project, owner):
    db = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()

    project_result = MagicMock()
    project_result.scalar_one_or_none.return_value = project

    owner_result = MagicMock()
    owner_result.scalar_one_or_none.return_value = owner

    db.execute = AsyncMock(side_effect=[project_result, owner_result])
    return db


@pytest.mark.asyncio
async def test_run_proactive_check_posts_comment_and_notification_when_issues_found(
    monkeypatch: pytest.MonkeyPatch,
):
    import app.tasks.agent_monitor as monitor

    project = _make_project()
    owner = _make_owner(project.owner_id)
    db = _make_db(project, owner)

    findings = ProactiveFindings(has_issues=True, summary="Task X is overdue.")
    mock_comment_ctx = MagicMock()
    mock_conversation = MagicMock()
    mock_conversation.id = uuid.uuid4()

    monkeypatch.setattr(monitor, "get_model_catalog", AsyncMock(return_value={}))
    monkeypatch.setattr(
        monitor,
        "resolve_effective_provider_model",
        MagicMock(return_value=("mock", "mock")),
    )
    monkeypatch.setattr(monitor, "read_user_ai_preferences", MagicMock(return_value={}))
    monkeypatch.setattr(
        monitor, "run_proactive_analysis", AsyncMock(return_value=findings)
    )
    monkeypatch.setattr(
        monitor.organization_service,
        "get_organization_by_id",
        AsyncMock(return_value=None),
    )

    mock_create_comment = AsyncMock()
    mock_create_notification = AsyncMock()

    monkeypatch.setattr(
        monitor.comment_service,
        "resolve_entity_context",
        AsyncMock(return_value=mock_comment_ctx),
    )
    monkeypatch.setattr(monitor.comment_service, "create_comment", mock_create_comment)
    monkeypatch.setattr(
        monitor.notification_service, "create_notification", mock_create_notification
    )

    with patch(
        "app.tasks.agent_monitor.AIConversation", return_value=mock_conversation
    ):
        await _run_proactive_check(db, project.id)

    mock_create_notification.assert_called_once()
    mock_create_comment.assert_called_once()


@pytest.mark.asyncio
async def test_run_proactive_check_does_nothing_when_no_issues(
    monkeypatch: pytest.MonkeyPatch,
):
    import app.tasks.agent_monitor as monitor

    project = _make_project()
    owner = _make_owner(project.owner_id)
    db = _make_db(project, owner)

    findings = ProactiveFindings(has_issues=False, summary="")
    mock_conversation = MagicMock()
    mock_conversation.id = uuid.uuid4()

    monkeypatch.setattr(monitor, "get_model_catalog", AsyncMock(return_value={}))
    monkeypatch.setattr(
        monitor,
        "resolve_effective_provider_model",
        MagicMock(return_value=("mock", "mock")),
    )
    monkeypatch.setattr(monitor, "read_user_ai_preferences", MagicMock(return_value={}))
    monkeypatch.setattr(
        monitor, "run_proactive_analysis", AsyncMock(return_value=findings)
    )
    monkeypatch.setattr(
        monitor.organization_service,
        "get_organization_by_id",
        AsyncMock(return_value=None),
    )

    mock_create_comment = AsyncMock()
    mock_create_notification = AsyncMock()

    monkeypatch.setattr(monitor.comment_service, "resolve_entity_context", AsyncMock())
    monkeypatch.setattr(monitor.comment_service, "create_comment", mock_create_comment)
    monkeypatch.setattr(
        monitor.notification_service, "create_notification", mock_create_notification
    )

    with patch(
        "app.tasks.agent_monitor.AIConversation", return_value=mock_conversation
    ):
        await _run_proactive_check(db, project.id)

    mock_create_comment.assert_not_called()
    mock_create_notification.assert_not_called()


@pytest.mark.asyncio
async def test_run_all_health_checks_skips_failed_project_and_continues(
    monkeypatch: pytest.MonkeyPatch,
):
    import app.tasks.agent_monitor as monitor

    id1 = uuid.uuid4()
    id2 = uuid.uuid4()

    monkeypatch.setattr(
        monitor, "_get_active_project_ids", AsyncMock(return_value=[id1, id2])
    )

    call_count = 0

    async def _mock_check(db, project_id):
        nonlocal call_count
        if project_id == id1:
            raise RuntimeError("ai-service is down")
        call_count += 1

    monkeypatch.setattr(monitor, "_run_proactive_check", _mock_check)

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("app.tasks.agent_monitor.AsyncSessionLocal", return_value=mock_session):
        count = await _run_all_health_checks()

    assert count == 1
    assert call_count == 1


@pytest.mark.asyncio
async def test_notification_targets_correct_project(
    monkeypatch: pytest.MonkeyPatch,
):
    import app.tasks.agent_monitor as monitor

    project = _make_project()
    owner = _make_owner(project.owner_id)
    db = _make_db(project, owner)

    findings = ProactiveFindings(has_issues=True, summary="Critical path delayed.")
    mock_conversation = MagicMock()
    mock_conversation.id = uuid.uuid4()

    monkeypatch.setattr(monitor, "get_model_catalog", AsyncMock(return_value={}))
    monkeypatch.setattr(
        monitor,
        "resolve_effective_provider_model",
        MagicMock(return_value=("mock", "mock")),
    )
    monkeypatch.setattr(monitor, "read_user_ai_preferences", MagicMock(return_value={}))
    monkeypatch.setattr(
        monitor, "run_proactive_analysis", AsyncMock(return_value=findings)
    )
    monkeypatch.setattr(
        monitor.organization_service,
        "get_organization_by_id",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        monitor.comment_service,
        "resolve_entity_context",
        AsyncMock(return_value=MagicMock()),
    )
    monkeypatch.setattr(monitor.comment_service, "create_comment", AsyncMock())

    mock_create_notification = AsyncMock()
    monkeypatch.setattr(
        monitor.notification_service, "create_notification", mock_create_notification
    )

    with patch(
        "app.tasks.agent_monitor.AIConversation", return_value=mock_conversation
    ):
        await _run_proactive_check(db, project.id)

    call_kwargs = mock_create_notification.call_args.kwargs
    assert call_kwargs["entity_type"] == "project"
    assert call_kwargs["entity_id"] == project.id
    assert call_kwargs["user_id"] == project.owner_id


@pytest.mark.asyncio
async def test_run_proactive_check_skips_when_project_agent_disabled(
    monkeypatch: pytest.MonkeyPatch,
):
    import app.tasks.agent_monitor as monitor

    project = _make_project()
    project.settings = {"agent_enabled": False}
    owner = _make_owner(project.owner_id)
    db = _make_db(project, owner)

    mock_get_model_catalog = AsyncMock(return_value={})
    monkeypatch.setattr(monitor, "get_model_catalog", mock_get_model_catalog)
    monkeypatch.setattr(
        monitor.organization_service,
        "get_organization_by_id",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(monitor, "run_proactive_analysis", AsyncMock())

    await _run_proactive_check(db, project.id)

    mock_get_model_catalog.assert_not_called()
    monitor.run_proactive_analysis.assert_not_called()


@pytest.mark.asyncio
async def test_run_proactive_check_skips_when_organization_agent_disabled(
    monkeypatch: pytest.MonkeyPatch,
):
    import app.tasks.agent_monitor as monitor

    project = _make_project()
    owner = _make_owner(project.owner_id)
    db = _make_db(project, owner)

    disabled_org = MagicMock()
    disabled_org.settings = {"agent_enabled": False}

    mock_get_model_catalog = AsyncMock(return_value={})
    monkeypatch.setattr(monitor, "get_model_catalog", mock_get_model_catalog)
    monkeypatch.setattr(
        monitor.organization_service,
        "get_organization_by_id",
        AsyncMock(return_value=disabled_org),
    )
    monkeypatch.setattr(monitor, "run_proactive_analysis", AsyncMock())

    await _run_proactive_check(db, project.id)

    mock_get_model_catalog.assert_not_called()
    monitor.run_proactive_analysis.assert_not_called()
