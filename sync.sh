#!/bin/bash
# Sync daily-news from eze-skills-private repository

PRIVATE_REPO="$HOME/.claude/skills"
PUBLIC_REPO="$(cd "$(dirname "$0")" && pwd)"
SKILL="daily-news"

echo "Syncing $SKILL from private repo..."

# Check if private repo exists
if [ ! -d "$PRIVATE_REPO/$SKILL" ]; then
    echo "Error: $SKILL not found in $PRIVATE_REPO"
    exit 1
fi

# Remove old version
rm -rf "$PUBLIC_REPO/$SKILL"

# Copy from private repo
cp -R "$PRIVATE_REPO/$SKILL" "$PUBLIC_REPO/"

echo "✓ $SKILL synced successfully"
echo ""
echo "Next steps:"
echo "  cd $PUBLIC_REPO"
echo "  git add ."
echo "  git commit -m 'Update $SKILL from private repo'"
echo "  git push"
