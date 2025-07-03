# Slack MCP Server

A Model Context Protocol (MCP) server that provides comprehensive Slack API integration, enabling AI assistants to interact with Slack workspaces through a standardized interface.

## Overview

This MCP server allows AI models to perform various Slack operations including messaging, channel management, user interactions, file operations, and workspace administration through the Slack Web API.

## Features

- **Messaging**: Send messages to channels, users, and threads
- **Channel Management**: List, create, and manage Slack channels
- **User Management**: Retrieve user information and workspace members
- **File Operations**: Upload and manage files in Slack
- **Workspace Info**: Access workspace details and team information
- **Search Capabilities**: Search messages, files, and users
- **Reactions**: Add and remove reactions to messages
- **Thread Management**: Handle message threads and replies

## Architecture

- **Docker-based deployment** for easy setup and isolation
- **Secure token management** using environment variables
- **Rate limiting** to respect Slack API limits
- **Error handling** with detailed logging
- **MCP protocol compliance** for seamless AI integration

## Prerequisites

- Docker and Docker Compose
- Slack workspace with appropriate permissions
- Slack API token (Bot or User token)

## Quick Start

1. Clone the repository
2. Configure your Slack API token
3. Run with Docker Compose
4. Connect to your AI assistant

## Configuration

The server supports both Bot tokens (`xoxb-`) and User tokens (`xoxp-`) depending on your use case and required permissions.

## Development Status

🚧 **In Development** - See [ROADMAP.md](ROADMAP.md) for current progress and planned features.

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests for any improvements.

## Support

For issues and questions, please use the GitHub Issues tracker.
