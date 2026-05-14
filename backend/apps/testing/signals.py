from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="testing.TestSession")
def on_session_finished(sender, instance, created: bool, **kwargs) -> None:
    if created:
        return

    from apps.testing.models import SessionStatus

    if instance.status != SessionStatus.FINISHED:
        return

    if getattr(instance, "_report_task_dispatched", False):
        logger.debug(
            "[signal] Skipping duplicate report dispatch for session %s.",
            instance.id,
        )
        return

    instance._report_task_dispatched = True

    session_id = str(instance.id)

    try:
        from apps.testing.tasks import send_session_report_task

        send_session_report_task.apply_async(
            args=[session_id],
            countdown=5,
        )
        logger.info(
            "[signal:on_session_finished] Telegram report task dispatched. "
            "session_id=%s session_title=%s",
            session_id,
            instance.title or instance.key,
        )
    except Exception as exc:
        logger.error(
            "[signal:on_session_finished] Failed to dispatch Telegram report. "
            "session_id=%s error=%s",
            session_id,
            exc,
        )