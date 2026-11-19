"""End-to-End (E2E) Browser Test using Selenium.

Covers the core student journey:
1. Student login through the academic portal.
2. Viewing available courses and submitting course registration.
3. Checking registration status and viewing results/notifications panel.
"""
import socket
import threading
import time
from typing import Generator
import pytest
import uvicorn
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy.orm import Session

from suams.main import app
from suams.database import Base, SessionLocal, engine
from suams.models.user import User, UserRole
from suams.models.course import Course
from suams.auth.security import get_password_hash


def get_free_port() -> int:
    """Find a random free localhost port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def live_server() -> Generator[str, None, None]:
    """Launch a live uvicorn server in a background daemon thread for Selenium."""
    port = get_free_port()
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="error",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server to become responsive
    url = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except (OSError, ConnectionRefusedError):
            time.sleep(0.1)

    yield url
    server.should_exit = True


@pytest.fixture(scope="module")
def browser() -> Generator[webdriver.Chrome, None, None]:
    """Initialize headless Chrome webdriver."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


@pytest.fixture(scope="module", autouse=True)
def setup_e2e_database() -> Generator[None, None, None]:
    """Create database tables and seed test data for the E2E scenario."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    # Seed E2E Student
    student = db.query(User).filter(User.username == "student_e2e").first()
    if not student:
        student = User(
            email="student_e2e@ruet.ac.bd",
            username="student_e2e",
            full_name="E2E Test Student",
            hashed_password=get_password_hash("password123"),
            role=UserRole.STUDENT,
            department="CSE",
            semester=5,
            is_active=True,
        )
        db.add(student)

    # Seed E2E Course
    course = db.query(Course).filter(Course.code == "CSE 3206").first()
    if not course:
        course = Course(
            code="CSE 3206",
            title="Software Engineering & System Design",
            credits=3.0,
            seat_capacity=50,
            department="CSE",
            semester=5,
        )
        db.add(course)

    db.commit()
    db.close()
    yield


def test_student_core_journey_e2e(browser: webdriver.Chrome, live_server: str) -> None:
    """Execute complete E2E browser journey: Login -> Course Registration -> Status check."""
    portal_url = f"{live_server}/portal"
    browser.get(portal_url)

    wait = WebDriverWait(browser, 10)

    # 1. Verify Portal Title
    assert "SUAMS" in browser.title

    # 2. Complete Login Form
    username_input = wait.until(EC.visibility_of_element_located((By.ID, "username")))
    password_input = browser.find_element(By.ID, "password")
    login_btn = browser.find_element(By.ID, "login-btn")

    username_input.clear()
    username_input.send_keys("student_e2e")
    password_input.clear()
    password_input.send_keys("password123")
    login_btn.click()

    # 3. Verify Dashboard Loads
    dashboard_section = wait.until(EC.visibility_of_element_located((By.ID, "dashboard-section")))
    assert dashboard_section.is_displayed()

    welcome_text = browser.find_element(By.ID, "welcome-msg").text
    assert "E2E Test Student" in welcome_text or "student_e2e" in welcome_text

    # 4. View Courses and Register for CSE 3206
    reg_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-register")))
    reg_btn.click()

    # 5. Verify Registration Status Message
    status_badge = wait.until(EC.visibility_of_element_located((By.ID, "reg-status-badge")))
    assert "PENDING" in status_badge.text or "Success" in status_badge.text

    # 6. Verify Results / Academic Notice Panel is accessible
    results_tab = browser.find_element(By.ID, "results-tab")
    assert results_tab.is_displayed()
