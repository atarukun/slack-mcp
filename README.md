# Slack MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)

A **production-ready** Model Context Protocol (MCP) server for comprehensive Slack integration. Enable AI assistants to interact seamlessly with Slack workspaces through standardized, secure tools.

## 🚀 Quick Start

### For Warp.dev Users

1. **Build the Docker image:**
   ```bash
   git clone https://github.com/atarukun/slack-mcp.git
   cd slack-mcp
   docker build -t slack-mcp:latest .
   ```

2. **Configure in Warp:**
   ```json
   {
     "slack-mcp": {
       "command": "docker",
       "args": [
         "run", "--rm", "-i",
         "-e", "SLACK_BOT_TOKEN=xoxb-your-actual-slack-bot-token",
         "slack-mcp:latest"
       ],
       "env": {},
       "working_directory": null,
       "start_on_launch": true
     }
   }
   ```

3. **Get your Slack bot token** from https://api.slack.com/apps

4. **Start using Slack tools** in Warp!

### For Claude Desktop Users

See [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) for detailed setup instructions.

## ✨ Features

### 🔐 **Authentication & Security**
- Secure bot token handling via environment variables
- Automatic token validation and format checking
- Rate limiting compliance (1-second minimum intervals)
- Support for Bot (`xoxb-`) and User (`xoxp-`) tokens

### 💬 **Messaging Tools**
- **send_message**: Send messages to channels, users, or threads
- Rich text formatting with Slack blocks and attachments
- Thread reply support with `thread_ts` parameter
- Multi-channel message broadcasting

### 🏢 **Workspace Discovery**
- **list_channels**: Categorized channel listing with beautiful formatting
- **get_channel_info**: Detailed channel information and statistics
- Support for public, private, and archived channels
- Member counts and channel metadata

### 👥 **User Management**
- **get_user_info**: Comprehensive user profile information
- Display names, titles, status messages, and timezone data
- Admin and bot account detection
- Email-based user lookup


### 🔌 **Connection & Testing**
- **test_slack_connection**: Comprehensive connectivity testing
- Workspace information display (name, domain, branding)
- API configuration details and diagnostics
- **set_slack_token**: Runtime token configuration

## 🏗️ Architecture

### **Docker-First Design**
- Multi-stage Dockerfile optimized for development and production
- Python 3.12 with full async support
- `uv` package manager for fast, reliable dependency management
- Non-root user execution for security
- Built-in health checks and monitoring

### **MCP Protocol Implementation**
- **FastMCP Framework** for automatic tool registration
- **STDIO Transport** for maximum client compatibility
- **Async Operations** with proper error handling
- **Type Safety** with full Pydantic validation
- **Rate Limiting** built into all API operations

## 📊 Current Status

**Version**: 1.4.1 (File operations removed)  
**Phases Completed**: 6 of 13  
**Tools Available**: 29 production-ready MCP tools
**Testing**: Verified with ILDM workspace

### **Available Tools**

#### **Core Tools (Phases 1-3)**
1. **`set_slack_token`** - Configure authentication
2. **`test_slack_connection`** - Verify connectivity and workspace info
3. **`send_message`** - Send formatted messages to channels/users
4. **`get_channel_info`** - Get detailed channel information  
5. **`list_channels`** - Explore workspace channels with categorization
6. **`get_user_info`** - Retrieve comprehensive user profiles

#### **Extended Messaging Tools (Phase 4)**
7. **`update_message`** - Edit/update existing messages
8. **`delete_message`** - Delete messages from channels
9. **`pin_message`** - Pin important messages to channels
10. **`unpin_message`** - Unpin messages from channels
11. **`get_message_permalink`** - Generate shareable message links
12. **`schedule_message`** - Schedule messages for future delivery
13. **`get_thread_replies`** - Retrieve and display thread conversations
14. **`send_direct_message`** - Send private messages to users

#### **Channel Management Tools (Phase 5)**
15. **`create_channel`** - Create new public or private channels
16. **`archive_channel`** - Archive channels to preserve history
17. **`set_channel_topic`** - Set or update channel topics
18. **`set_channel_purpose`** - Set channel purposes/descriptions
19. **`join_channel`** - Join public channels
20. **`leave_channel`** - Leave channels
21. **`invite_to_channel`** - Invite users to channels
22. **`remove_from_channel`** - Remove users from channels
23. **`list_channel_members`** - List all members of a channel

#### **User Management Tools (Phase 6)**
24. **`get_user_info`** - Get detailed information about a Slack user
25. **`list_workspace_members`** - List all members in the workspace (with categorization)
26. **`search_slack_users`** - Search for users by name, email, or title
27. **`get_user_presence`** - Get a user's current presence status (active/away)
28. **`get_user_timezone`** - Get a user's timezone information
29. **`get_user_conversations`** - List all conversations a user is member of


## 📖 Documentation

- **[CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)** - Setup for different MCP clients
- **[ROADMAP.md](ROADMAP.md)** - Development phases and future features
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes
- **Docker configurations** - Multiple deployment examples

## 🛠️ Development

### **Prerequisites**
- Docker and Docker Compose
- Python 3.12+ (for local development)
- Slack Bot Token from https://api.slack.com/apps

### **Local Development**

```bash
# Clone and setup
git clone https://github.com/atarukun/slack-mcp.git
cd slack-mcp

# Build development container
docker build --target development -t slack-mcp-dev .

# Run with development setup
docker-compose up --build

# Run tests
source .venv/bin/activate
python test_tools.py
```

### **Production Deployment**

```bash
# Build production image
docker build --target production -t slack-mcp:latest .

# Run production container
docker run --rm -i \
  -e SLACK_BOT_TOKEN=xoxb-your-token \
  slack-mcp:latest
```

## 🤝 Contributing

Contributions are welcome! This project follows a structured development roadmap:

- **Phases 1-3**: ✅ Core implementation (COMPLETED)
- **Phases 4-5**: ✅ Extended messaging, channel management (COMPLETED)
- **Phase 6**: User Management with basic tools (Completely moved more advanced user management to Phase 10)
- **Phases 7-9**: Search, interactive elements, and other advanced features
- **Phases 10-13**: Analytics, workflows, production features

See [ROADMAP.md](ROADMAP.md) for detailed development phases.

## 📄 License

**MIT License** - see [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Brennon Church** (atarukun@gmail.com)

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) team for the excellent protocol
- [Slack](https://slack.com/) for their comprehensive API and SDK
- [FastMCP](https://github.com/modelcontextprotocol/servers) framework for rapid development
- [uv](https://github.com/astral-sh/uv) and [Docker](https://docker.com/) for excellent development tools

---

⭐ **Star this repository** if you find it useful!  
🐛 **Report issues** on GitHub  
💡 **Suggest features** via GitHub Discussions
