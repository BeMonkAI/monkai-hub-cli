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

# Edge Function for test execution (proxies to Railway server internally)
# The Edge Function already has the tester API key — CLI only needs the user JWT.
EDGE_FUNCTION_URL = f"{SUPABASE_URL}/functions/v1/python-test-executor"
