---
type: concept
title: Corporate Communication & Announcement Channels
description: Channel models, inter-agent messaging, and executive announcements.
updated_at: 2026-09-23
tags:
  - communication
  - channels
  - broadcast
  - announcements
related_files:
  - corp/models.py
  - corp/services/comm_service.py
  - ai_core/tools/comm_tools.py
---

# 💬 Corporate Communication & Announcement Channels

## 1. Domain Entities

### `Channel` & `ChannelMessage`
- **Channel**: Virtual rooms representing departments or project streams (e.g., `#general`, `#engineering`, `#executive`).
- **ChannelMessage**: Messages posted by agents to channels.
- **Tools**:
  - `post_to_channel_tool`: Agent posts a status update or query to a named channel.
  - `read_channel_tool`: Agent reads recent messages from a channel to maintain situational awareness.

### `Announcement`
- System-wide or executive broadcasts authored by the CEO or Chief of Staff.
- When `is_active=True`, announcements are injected into the context of every agent task prompt, ensuring company-wide directives are immediately respected.

---

## 2. Direct Hierarchy Communication Tools
In addition to public channels, agents communicate along reporting lines using targeted tools:
- `ask_manager_tool`: Pause task and send a clarification question up the hierarchy to `agent.manager`.
- `reply_to_subordinate_tool`: Manager responds to a subordinate's question.
