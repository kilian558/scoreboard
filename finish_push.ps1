# Close any open git editor
$env:GIT_EDITOR = "true"

# Abort current rebase if any
git rebase --abort 2>&1 | Out-Null

# Reset to clean state
git reset --hard HEAD

# Pull latest changes
git pull origin main --no-rebase

# Merge our optimizations
git add -A
git commit -m "Optimize for PM2: Add logging, graceful shutdown, error handling, freeze tracker with data directory"

# Push
git push origin main

Write-Host "`n=== Push Complete ===" -ForegroundColor Green
Write-Host "Repository: https://github.com/kilian558/scoreboard" -ForegroundColor Cyan
