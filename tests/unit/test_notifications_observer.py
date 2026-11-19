"""Unit tests for AcademicEventPublisher and Observers (Observer Pattern).

Tests behavioral Observer pattern with:
- AcademicEventPublisher (Subject)
- InAppObserver, EmailObserver, AnalyticsObserver (Concrete Observers)
- Mocking external email/SMS dispatchers with unittest.mock.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest

from suams.notifications.publisher import (
    AcademicEvent,
    AcademicEventType,
    AcademicEventPublisher,
    InAppObserver,
    EmailObserver,
    AnalyticsObserver,
)
from suams.models.notification import NotificationLog


def test_publisher_attach_detach_observer() -> None:
    """Test attaching and detaching observers to/from AcademicEventPublisher."""
    publisher = AcademicEventPublisher()
    mock_observer = MagicMock()

    publisher.attach(mock_observer)
    assert mock_observer in publisher.observers

    publisher.detach(mock_observer)
    assert mock_observer not in publisher.observers


def test_publisher_notifies_all_registered_observers() -> None:
    """Test publisher dispatches event to all attached observers."""
    publisher = AcademicEventPublisher()
    obs1 = MagicMock()
    obs2 = MagicMock()

    publisher.attach(obs1)
    publisher.attach(obs2)

    event = AcademicEvent(
        event_type=AcademicEventType.RESULT_PUBLISHED,
        payload={"course_id": 1, "published_count": 10},
        timestamp=datetime.now(timezone.utc),
    )

    publisher.notify(event)

    obs1.update.assert_called_once_with(event, None)
    obs2.update.assert_called_once_with(event, None)


def test_detached_observer_does_not_receive_notifications() -> None:
    """Test detached observer stops receiving notifications."""
    publisher = AcademicEventPublisher()
    obs1 = MagicMock()
    obs2 = MagicMock()

    publisher.attach(obs1)
    publisher.attach(obs2)
    publisher.detach(obs1)

    event = AcademicEvent(
        event_type=AcademicEventType.REGISTRATION_APPROVED,
        payload={"enrollment_id": 5, "student_id": 1},
        timestamp=datetime.now(timezone.utc),
    )

    publisher.notify(event)

    obs1.update.assert_not_called()
    obs2.update.assert_called_once_with(event, None)


def test_in_app_observer_persists_notification_log() -> None:
    """Test InAppObserver logs an in-app notification to the database."""
    mock_db = MagicMock()
    observer = InAppObserver()

    event = AcademicEvent(
        event_type=AcademicEventType.RESULT_PUBLISHED,
        payload={
            "user_id": 1,
            "recipient": "student1@ruet.ac.bd",
            "message": "Results for CSE 3206 published.",
        },
        timestamp=datetime.now(timezone.utc),
    )

    observer.update(event, db=mock_db)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    added_log = mock_db.add.call_args[0][0]
    assert isinstance(added_log, NotificationLog)
    assert added_log.channel == "IN_APP"
    assert added_log.event_type == AcademicEventType.RESULT_PUBLISHED.value


def test_email_observer_dispatches_via_mocked_gateway() -> None:
    """Test EmailObserver invokes the email dispatcher gateway and creates log."""
    mock_db = MagicMock()
    observer = EmailObserver()

    event = AcademicEvent(
        event_type=AcademicEventType.RESULT_PUBLISHED,
        payload={
            "user_id": 2,
            "recipient": "student2@ruet.ac.bd",
            "message": "Grade A+ in CSE 3206.",
        },
        timestamp=datetime.now(timezone.utc),
    )

    with patch("suams.notifications.publisher.EmailDispatcher.send_email") as mock_send:
        mock_send.return_value = True
        observer.update(event, db=mock_db)

        mock_send.assert_called_once_with(
            to_email="student2@ruet.ac.bd",
            subject=f"Academic Notice: {AcademicEventType.RESULT_PUBLISHED.value}",
            body="Grade A+ in CSE 3206.",
        )
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        added_log = mock_db.add.call_args[0][0]
        assert added_log.channel == "EMAIL"
        assert added_log.status == "SENT"


def test_analytics_observer_records_metric() -> None:
    """Test AnalyticsObserver processes telemetry for academic events."""
    mock_db = MagicMock()
    observer = AnalyticsObserver()

    event = AcademicEvent(
        event_type=AcademicEventType.REGISTRATION_APPROVED,
        payload={
            "user_id": 3,
            "recipient": "analytics@ruet.ac.bd",
            "message": "Enrollment approved.",
        },
        timestamp=datetime.now(timezone.utc),
    )

    observer.update(event, db=mock_db)

    assert observer.processed_count == 1
    mock_db.add.assert_called_once()
    added_log = mock_db.add.call_args[0][0]
    assert added_log.channel == "ANALYTICS"
