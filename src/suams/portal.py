"""Academic Portal Web Interface for E2E browser interactions and manual testing."""
from fastapi.responses import HTMLResponse

PORTAL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SUAMS - Smart University Academic Management System</title>
    <style>
        :root {
            --primary: #1e3a8a;
            --accent: #2563eb;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #0f172a;
            --success: #16a34a;
            --danger: #dc2626;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        header {
            background: var(--primary);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 24px;
        }
        h1, h2, h3 { margin-top: 0; }
        .card {
            background: var(--card-bg);
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 16px;
        }
        label {
            display: block;
            margin-bottom: 6px;
            font-weight: 600;
        }
        input {
            width: 100%;
            padding: 10px;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            box-sizing: border-box;
        }
        button {
            background: var(--accent);
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
        }
        button:hover { opacity: 0.9; }
        .btn-register { background: var(--primary); }
        .badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 9999px;
            font-size: 13px;
            font-weight: 600;
            background: #e2e8f0;
        }
        .badge-pending { background: #fef3c7; color: #92400e; }
        .badge-success { background: #dcfce7; color: #166534; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }
        th, td {
            text-align: left;
            padding: 10px;
            border-bottom: 1px solid #e2e8f0;
        }
        th { background: #f1f5f9; }
        .error-msg { color: var(--danger); margin-top: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>SUAMS Academic Management Portal</h1>
            <p>Department of Computer Science & Engineering | RUET</p>
        </header>

        <!-- Authentication Panel -->
        <div id="login-section" class="card">
            <h2>User Authentication</h2>
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" placeholder="e.g. student_e2e" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" placeholder="••••••••" required>
            </div>
            <button id="login-btn" onclick="handleLogin()">Sign In</button>
            <div id="login-error" class="error-msg"></div>
        </div>

        <!-- Student Dashboard Panel -->
        <div id="dashboard-section" class="card" style="display: none;">
            <h2 id="welcome-msg"></h2>
            <p id="user-role-badge" class="badge badge-success"></p>

            <!-- Course Registration Panel -->
            <div id="registration-panel" style="margin-top: 24px;">
                <h3>Available Course Catalog & Registration</h3>
                <div id="reg-status-badge" class="badge" style="display: none; margin-bottom: 12px;"></div>
                <table id="courses-table">
                    <thead>
                        <tr>
                            <th>Code</th>
                            <th>Title</th>
                            <th>Credits</th>
                            <th>Capacity</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody id="courses-tbody">
                        <tr><td colspan="5">Loading courses...</td></tr>
                    </tbody>
                </table>
            </div>

            <!-- Results & Academic Records Tab -->
            <div id="results-tab" style="margin-top: 32px;">
                <h3>Academic Records & Results</h3>
                <div id="results-container">
                    <table id="results-table">
                        <thead>
                            <tr>
                                <th>Course ID</th>
                                <th>Total Marks</th>
                                <th>Grade</th>
                                <th>GPA</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="results-tbody">
                            <tr><td colspan="5">No published results yet.</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        let authToken = "";

        async function handleLogin() {
            const username = document.getElementById("username").value.trim();
            const password = document.getElementById("password").value.trim();
            const errorDiv = document.getElementById("login-error");
            errorDiv.innerText = "";

            try {
                const response = await fetch("/api/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });

                if (!response.ok) {
                    const err = await response.json();
                    errorDiv.innerText = err.detail || "Authentication failed";
                    return;
                }

                const data = await response.json();
                authToken = data.access_token;

                // Load User Dashboard
                document.getElementById("login-section").style.display = "none";
                document.getElementById("dashboard-section").style.display = "block";
                document.getElementById("welcome-msg").innerText = "Welcome, " + username;
                document.getElementById("user-role-badge").innerText = "Role: " + data.role;

                await loadCourses();
                await loadResults();
            } catch (e) {
                errorDiv.innerText = "Error contacting server: " + e.message;
            }
        }

        async function loadCourses() {
            const tbody = document.getElementById("courses-tbody");
            try {
                const response = await fetch("/api/registration/courses", {
                    headers: { "Authorization": "Bearer " + authToken }
                });
                const courses = await response.json();
                tbody.innerHTML = "";

                if (courses.length === 0) {
                    tbody.innerHTML = "<tr><td colspan='5'>No courses cataloged.</td></tr>";
                    return;
                }

                courses.forEach(c => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td><strong>${c.code}</strong></td>
                        <td>${c.title}</td>
                        <td>${c.credits}</td>
                        <td>${c.seat_capacity}</td>
                        <td>
                            <button class="btn-register" onclick="registerCourse(${c.id})">Register</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (e) {
                tbody.innerHTML = "<tr><td colspan='5'>Failed to load courses</td></tr>";
            }
        }

        async function registerCourse(courseId) {
            const badge = document.getElementById("reg-status-badge");
            badge.style.display = "inline-block";
            badge.className = "badge";
            badge.innerText = "Submitting registration...";

            try {
                const response = await fetch("/api/registration/register", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": "Bearer " + authToken
                    },
                    body: JSON.stringify({ course_id: courseId })
                });

                const data = await response.json();
                if (response.ok) {
                    badge.className = "badge badge-pending";
                    badge.innerText = "Registration Submitted (Status: " + data.status + ")";
                } else {
                    badge.className = "badge";
                    badge.style.background = "#fee2e2";
                    badge.style.color = "#991b1b";
                    badge.innerText = "Error: " + (data.detail || "Registration failed");
                }
            } catch (e) {
                badge.innerText = "Network error: " + e.message;
            }
        }

        async function loadResults() {
            const tbody = document.getElementById("results-tbody");
            try {
                const response = await fetch("/api/results/my-results", {
                    headers: { "Authorization": "Bearer " + authToken }
                });
                if (!response.ok) return;
                const results = await response.json();
                if (results.length > 0) {
                    tbody.innerHTML = "";
                    results.forEach(r => {
                        const tr = document.createElement("tr");
                        tr.innerHTML = `
                            <td>Course ${r.course_id}</td>
                            <td>${r.total_marks}</td>
                            <td>${r.grade || "N/A"}</td>
                            <td>${r.gpa !== null ? r.gpa.toFixed(2) : "N/A"}</td>
                            <td>${r.evaluation_status || "PUBLISHED"}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
            } catch (e) {
                console.error("Could not fetch results", e);
            }
        }
    </script>
</body>
</html>
"""


def get_portal_html() -> HTMLResponse:
    """Return the interactive HTML portal for SUAMS."""
    return HTMLResponse(content=PORTAL_HTML, status_code=200)
