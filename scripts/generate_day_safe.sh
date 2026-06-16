#!/bin/bash
# generate_day_safe.sh — Wrapper that generates one day's lessons with
# extended timeouts and per-lesson error recovery.
# Usage: bash generate_day_safe.sh <day_number>
#
# This script calls generate_day.py and wraps it with:
# - 15-minute timeout per lesson (via the Python script's own curl timeouts)
# - Retry logic: if a lesson fails, retry up to 2 times before moving on
# - Continues on partial failure (doesn't abort the whole day)
# - Always updates state.json and generated.json at the end

set -o pipefail

DAY="${1:?Usage: generate_day_safe.sh <day_number>}"
BASE="/home/mrotatori/ai-training"
cd "$BASE" || exit 1

echo "=== Safe Generator: Day $DAY ==="
echo "Start: $(date -Iseconds)"

# Run the Python generator. It handles its own retries per lesson.
# We give it a very generous wall-clock timeout: 20 minutes for 5 lessons.
timeout 1200 python3 -u scripts/generate_day.py "$DAY" 2>&1
EXIT_CODE=$?

echo ""
echo "Python script exit code: $EXIT_CODE"

# Check which lessons exist now
TUTORIAL_DIR="$BASE/tutorials"
GENERATED=0
MISSING=0
for L in 1 2 3 4 5; do
    FNAME=$(printf "%02d%02d.html" "$DAY" "$L")
    FPATH="$TUTORIAL_DIR/$FNAME"
    if [ -f "$FPATH" ] && [ "$(stat -c%s "$FPATH" 2>/dev/null || echo 0)" -gt 100 ]; then
        GENERATED=$((GENERATED + 1))
    else
        MISSING=$((MISSING + 1))
        echo "  MISSING: $FNAME"
    fi
done

echo "Day $DAY: $GENERATED/5 lessons present ($MISSING missing)"

# Update state.json to advance to next day (only if we have at least 1 new lesson)
if [ "$GENERATED" -gt 0 ]; then
    NEXT_DAY=$((DAY + 1))
    cat > scripts/state.json <<EOF
{
  "next_day": $NEXT_DAY,
  "next_lesson": 1
}
EOF
    echo "Updated state.json: next_day=$NEXT_DAY"

    # Update generated.json
    python3 -c "
import json, time
f = '$BASE/generated.json'
if __import__('os').path.exists(f):
    data = json.load(open(f))
else:
    data = {'lessons': [], 'last_updated': ''}
for l in range(1, 6):
    s = str($DAY).zfill(2) + str(l).zfill(2)
    if s not in data['lessons']:
        p = '$TUTORIAL_DIR/' + s + '.html'
        if __import__('os').path.exists(p) and __import__('os').path.getsize(p) > 100:
            data['lessons'].append(s)
data['last_updated'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
with open(f, 'w') as fh:
    json.dump(data, fh, indent=2)
print(f'Updated generated.json: {len(data[\"lessons\"])} total lessons')
"

    # Git commit and push
    git add -A
    git commit -m "Generate Day $DAY lessons ($(date +%Y-%m-%d))" 2>/dev/null
    git push origin main 2>&1 | tail -3
    echo "Git push done"
else
    echo "ERROR: No lessons generated for Day $DAY, not updating state"
    exit 1
fi

echo "=== Done: $(date -Iseconds) ==="
