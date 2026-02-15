"""HTTP load-test scenarios for Valentine Hotline staging/prod APIs."""

from __future__ import annotations

import os
from uuid import uuid4

from locust import HttpUser, between, task


class SuitorUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_landing(self):
        self.client.get("/api/v1/public/melika", name="public_profile")

    @task(2)
    def register_suitor(self):
        self.client.post(
            "/api/v1/suitors/register",
            json={
                "name": f"Load-{uuid4().hex[:6]}",
                "age": 27,
                "gender": "female",
                "orientation": "straight",
            },
            name="register_suitor",
        )

    @task(1)
    def create_session(self):
        self.client.post(
            "/api/v1/sessions/start",
            json={"heart_slug": "melika"},
            name="start_session",
        )


class DashboardUser(HttpUser):
    wait_time = between(2, 5)

    def on_start(self):
        key = os.getenv("DASHBOARD_API_KEY", "")
        self.headers = {"X-Dashboard-Key": key} if key else {}

    @task(3)
    def view_stats(self):
        self.client.get(
            "/api/v1/dashboard/stats", headers=self.headers, name="dash_stats"
        )

    @task(2)
    def view_sessions(self):
        self.client.get(
            "/api/v1/dashboard/sessions?page=1&per_page=20",
            headers=self.headers,
            name="dash_sessions",
        )

    @task(1)
    def view_trends(self):
        self.client.get(
            "/api/v1/dashboard/stats/trends",
            headers=self.headers,
            name="dash_trends",
        )
