"""Behavioral Design Pattern: Observer Pattern for Academic Notifications.

This module implements the Observer Pattern (Behavioral) to publish academic events
(e.g., RESULT_PUBLISHED, REGISTRATION_APPROVED) to decoupled subscribers
without tightly coupling service logic to external notification mechanisms.

Subject:
    - AcademicEventPublisher

Observers:
    - InAppObserver: Persists in-app notifications into the database.
    - EmailObserver: Dispatches email notices through external gateway (mocked).
    - AnalyticsObserver: Telemetry aggregator recording academic lifecycle metrics.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from sqlalchemy.orm import Session

from suams.models.notification import NotificationLog


class AcademicEventType(str, Enum):
    """Enumeration of academic event types dispatched by the publisher."""

    RESULT_PUBLISHED = "RESULT_PUBLISHED"
    REGISTRATION_APPROVED = "REGISTRATION_APPROVED"


@dataclass
class AcademicEvent:
    """Event data container passed to all subscribed observers."""

    event_type: AcademicEventType
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EmailDispatcher:
    """Gateway service for sending external emails. Mocked in tests."""

    @classmethod
    def send_email(cls, to_email: str, subject: str, body: str) -> bool:
        """Simulate sending an email through an external SMTP/API provider."""
        # Simulated dispatch log; in test runs this is mocked with unittest.mock.patch
        return True


class AcademicObserver(ABC):
    """Abstract Observer contract for subscribers of AcademicEvents."""

    @abstractmethod
    def update(self, event: AcademicEvent, db: Session | None = None) -> None:
        """Receive notification from Subject when an academic event occurs.

        Args:
            event: The dispatched AcademicEvent.
            db: Optional SQLAlchemy session to persist notification records.
        """
        pass


class InAppObserver(AcademicObserver):
    """Concrete Observer: Persists notifications to user in-app notification logs."""

    def update(self, event: AcademicEvent, db: Session | None = None) -> None:
        """Create and persist an In-App NotificationLog entry."""
        if db is not None:
            user_id = event.payload.get("user_id")
            recipient = event.payload.get("recipient", "student@ruet.ac.bd")
            message = event.payload.get("message", "Academic update notification.")
            event_type_str = (
                event.event_type.value
                if hasattr(event.event_type, "value")
                else str(event.event_type)
            )

            log_entry = NotificationLog(
                user_id=user_id,
                event_type=event_type_str,
                channel="IN_APP",
                recipient=recipient,
                message=message,
                status="SENT",
            )
            db.add(log_entry)
            db.commit()


class EmailObserver(AcademicObserver):
    """Concrete Observer: Dispatches email alerts and records delivery status."""

    def update(self, event: AcademicEvent, db: Session | None = None) -> None:
        """Dispatch email and persist an Email NotificationLog entry."""
        recipient = event.payload.get("recipient", "student@ruet.ac.bd")
        message = event.payload.get("message", "Academic update notification.")
        event_type_str = (
            event.event_type.value
            if hasattr(event.event_type, "value")
            else str(event.event_type)
        )
        subject = f"Academic Notice: {event_type_str}"

        # External dispatch (mockable)
        EmailDispatcher.send_email(
            to_email=recipient,
            subject=subject,
            body=message,
        )

        if db is not None:
            user_id = event.payload.get("user_id")
            log_entry = NotificationLog(
                user_id=user_id,
                event_type=event_type_str,
                channel="EMAIL",
                recipient=recipient,
                message=message,
                status="SENT",
            )
            db.add(log_entry)
            db.commit()


class AnalyticsObserver(AcademicObserver):
    """Concrete Observer: Telemetry subscriber tracking academic operations."""

    def __init__(self) -> None:
        self.processed_count: int = 0

    def update(self, event: AcademicEvent, db: Session | None = None) -> None:
        """Process event telemetry and optionally log analytics trace."""
        self.processed_count += 1
        if db is not None:
            user_id = event.payload.get("user_id")
            recipient = event.payload.get("recipient", "analytics@ruet.ac.bd")
            message = f"Telemetry captured: {event.event_type.value}"
            event_type_str = (
                event.event_type.value
                if hasattr(event.event_type, "value")
                else str(event.event_type)
            )

            log_entry = NotificationLog(
                user_id=user_id,
                event_type=event_type_str,
                channel="ANALYTICS",
                recipient=recipient,
                message=message,
                status="RECORDED",
            )
            db.add(log_entry)
            db.commit()


class AcademicEventPublisher:
    """Subject in the Observer Pattern.

    Maintains a registry of observers and distributes academic events
    whenever events such as RESULT_PUBLISHED or REGISTRATION_APPROVED occur.
    """

    def __init__(self) -> None:
        self._observers: list[AcademicObserver] = []

    @property
    def observers(self) -> list[AcademicObserver]:
        """Return shallow copy of attached observers."""
        return list(self._observers)

    def attach(self, observer: AcademicObserver) -> None:
        """Register a new observer subscriber."""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: AcademicObserver) -> None:
        """Unregister an observer subscriber."""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event: AcademicEvent, db: Session | None = None) -> None:
        """Broadcast the event to all registered observers."""
        for observer in self._observers:
            observer.update(event, db)


# Default singleton publisher instance pre-configured with core observers
academic_publisher: AcademicEventPublisher = AcademicEventPublisher()
academic_publisher.attach(InAppObserver())
academic_publisher.attach(EmailObserver())
academic_publisher.attach(AnalyticsObserver())
