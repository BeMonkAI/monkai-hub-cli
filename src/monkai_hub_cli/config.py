# -*- coding: utf-8 -*-
"""Configuration constants for MonkAI Hub CLI."""

from __future__ import annotations

import os

# Supabase (public values — same as the Hub frontend uses)
SUPABASE_URL = os.environ.get(
    "MONKAI_SUPABASE_URL",
    "https://lpvbvnqrozlwalnkvrgk.supabase.co",
)
SUPABASE_ANON_KEY = os.environ.get(
    "MONKAI_SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxwdmJ2bnFyb3psd2Fsbmt2cmdrIiwi"
    "cm9sZSI6ImFub24iLCJpYXQiOjE3NTI3NzU4NDYsImV4cCI6MjA2ODM1MTg0Nn0."
    "s9pXyntkt0fNQW21LRiu3ZNf2COImQuQ9xQ9pcI5zfc",
)

# MonkAI Tester Railway server
TESTER_API_URL = os.environ.get(
    "MONKAI_TESTER_API_URL",
    "https://monkai-tester-production.up.railway.app",
)
# REQUIRED — must be set via environment variable, never hardcoded
TESTER_API_KEY = os.environ.get("MONKAI_TESTER_API_KEY", "")
