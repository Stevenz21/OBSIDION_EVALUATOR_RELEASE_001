#!/usr/bin/env bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BUILD_LOG="$PROJECT_ROOT/Engine/IntelligenceFramework/History/LATEST_BUILD.log"

cd "$PROJECT_ROOT" || exit 1

mkdir -p "$(dirname "$BUILD_LOG")"

echo "======================================================================"
echo "OBSIDION ENGINE BUILD"
echo "======================================================================"

# Run the real build, display it live, and capture the exact output.
dotnet build "$PROJECT_ROOT/Runtime.csproj" "$@" 2>&1 | tee "$BUILD_LOG"

# Preserve dotnet's exit code, not tee's.
BUILD_EXIT=${PIPESTATUS[0]}

echo
echo "======================================================================"
echo "OBSIDION INTELLIGENCE"
echo "======================================================================"

python3 "$PROJECT_ROOT/Engine/IntelligenceFramework/Core/Startup.py"

INTEL_EXIT=$?

echo
echo "======================================================================"

if [ "$BUILD_EXIT" -eq 0 ]; then
    echo "[BUILD] SUCCESS"
else
    echo "[BUILD] FAILED — exit code $BUILD_EXIT"
fi

if [ "$INTEL_EXIT" -eq 0 ]; then
    echo "[INTELLIGENCE] ANALYSIS COMPLETE"
else
    echo "[INTELLIGENCE] FAILED — exit code $INTEL_EXIT"
fi

echo "======================================================================"

# Return the REAL build result.
exit "$BUILD_EXIT"
