# Integrations

## Overview

TaskFlow integrations connect your workspace to tools your team already uses. Integrations can send project updates to Slack, attach files from Google Drive, and connect GitHub activity to tasks.

Admins manage workspace integrations by default. Some integrations may also require approval from the third-party service owner, such as a Slack workspace admin or GitHub organization owner.

## Steps

1. Open TaskFlow.
2. Select **Workspace settings**.
3. Select **Integrations**.
4. Choose the integration you want to connect.
5. Select **Connect**.
6. Sign in to the third-party service when prompted.
7. Review the requested permissions.
8. Select **Allow** or **Authorize**.
9. Return to TaskFlow and configure integration settings.
10. Select **Save**.

To connect Slack, choose the Slack workspace and channel where TaskFlow should post updates. You can send task assignments, mentions, due date reminders, and project status changes.

To connect Google Drive, choose the Drive account and folders users can attach from. Team members can then link Drive files to tasks and projects.

To connect GitHub, choose the organization and repositories to sync. TaskFlow can link pull requests, commits, and issues to tasks.

To disconnect an integration, open **Workspace settings > Integrations**, select the connected service, and choose **Disconnect**.

## Important Notes

- Only Admins can connect or disconnect workspace-wide integrations unless permissions are customized.
- Third-party services may ask you to approve access outside TaskFlow.
- Disconnecting an integration stops new sync activity but does not remove existing task comments or history.
- Some integrations are available only on selected subscription plans.
- Integration permissions should be reviewed regularly when team membership changes.

## Troubleshooting

If an integration will not connect, confirm that you are signed in to the correct third-party account and have permission to approve apps.

If Slack messages are not appearing, check the selected channel and confirm that TaskFlow has not been removed from the Slack workspace.

If Google Drive files cannot be opened, review the file’s Drive sharing settings and the user’s TaskFlow project access.

If GitHub activity is missing, confirm that the correct repositories are selected and that repository access has not changed.

## FAQ

**Can I connect more than one Slack channel?**  
Yes, supported plans allow different projects to send updates to different Slack channels.

**Does disconnecting GitHub delete linked tasks?**  
No. Existing tasks remain, but new GitHub activity stops syncing.

**Can Members connect integrations?**  
Usually no. Admins manage workspace integrations unless custom permissions allow it.

**Why does Google Drive ask for permission again?**  
The connection may have expired, or your organization may require periodic reauthorization.
