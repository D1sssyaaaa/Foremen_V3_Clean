#!/bin/bash
# Chaos Runner - "Anti-Gravity" Suite

echo "🚀 Starting Anti-Gravity Test Suite..."
echo "📂 Project Root: $(pwd)"

# 1. Install Dependencies
echo "📦 Installing testing dependencies..."
pip install pytest pytest-asyncio httpx factory_boy pytest-html

# 2. Run Tests
echo "🔥 Executing Chaos Tests..."
# Running only our new tests
pytest tests/security tests/integration --verbose --html=chaos_report.html --self-contained-html

TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed (Suspicious... is the system too secure?)"
else
    echo "⚠️ Vulnerabilities or Logic gaps found! Check chaos_report.html"
fi

echo "📊 Report generated: chaos_report.html"
exit $TEST_EXIT_CODE
