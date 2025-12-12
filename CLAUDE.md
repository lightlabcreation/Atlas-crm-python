# Claude Code Instructions for Atlas CRM

## ⚠️ PROTECTION MODE: ENABLED

**DO NOT modify any files in this project unless the user EXPLICITLY requests changes.**

### Rules:
1. **READ-ONLY by default** - Only read files, do not edit or create files
2. **No automatic fixes** - Do not fix bugs, typos, or "improvements" unless asked
3. **No refactoring** - Do not restructure or reorganize code
4. **No new features** - Do not add functionality unless specifically requested
5. **Ask first** - If something seems broken, ASK the user before making changes

### To make changes, the user must say things like:
- "Edit the file..."
- "Change the code to..."
- "Fix this bug..."
- "Add this feature..."
- "Update the..."
- "Modify..."

### Protected Files (Critical - Extra Caution):
- `templates/base.html` - Main dashboard template with mobile navigation
- `landing/templates/landing/home.html` - Landing page
- `landing/templates/landing/base_landing.html` - Landing base template
- `users/views.py` - Authentication logic
- `users/management/commands/create_demo_users.py` - Demo user creation

### Current Stable Version:
- **Commit**: 7a7e7f1
- **Date**: December 12, 2025
- **Features**: Mobile dashboard navigation, modernized landing page, all 8 demo logins working

### Rollback Command:
```bash
git checkout 7a7e7f1
```
