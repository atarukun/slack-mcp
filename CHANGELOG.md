# Changelog

All notable changes to the Slack MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.1] - 2025-07-09

### Changed
- Cleaned up core tools

## [1.3.0] - 2024-01-04

### Added
- **Phase 6: User Management Tools** (6 new tools)
  - `get_user_info` - Get detailed information about a Slack user
  - `list_workspace_members` - List all members in the workspace with categorization
  - `search_slack_users` - Search for users by name, email, or title
  - `get_user_presence` - Get a user's current presence status
  - `get_user_timezone` - Get a user's timezone information
  - `get_user_conversations` - List all conversations a user is member of
  - Note: Tools requiring user tokens have been moved to Phase 10.6

### Changed
- Updated ROADMAP to move deferred channel settings from Phase 5.3 to Phase 10.5
- Tool count increased from 24 to 30 production-ready tools
- Moved user token required operations to Phase 10.6 in ROADMAP

### Fixed
- Fixed `get_user_info` returning JSON instead of formatted text (issue #8)
- Renamed `search_users` to `search_slack_users` to avoid naming conflicts (issue #8)

### Technical Improvements
- Added user categorization (admins, regular users, bots) in listing tools
- Enhanced search functionality with multiple field matching
- Added proper timezone calculations and display
- Improved error messages for token type requirements

## [1.2.0] - 2025-01-04

### Added
- **Phase 5: Channel Management Tools**
  - `create_channel` - Create new public or private channels with descriptions
  - `archive_channel` - Archive channels to preserve history
  - `set_channel_topic` - Set or update channel topics
  - `set_channel_purpose` - Set channel purposes/descriptions
  - `join_channel` - Join public channels
  - `leave_channel` - Leave channels
  - `invite_to_channel` - Invite multiple users to channels
  - `remove_from_channel` - Remove users from channels (kick)
  - `list_channel_members` - List all members of a channel with pagination

### Changed
- Updated tool count from 15 to 24 production-ready tools
- Enhanced documentation with Phase 5 tools
- Improved error handling consistency across all channel operations

### Removed
- `unarchive_channel` - Not supported with bot tokens due to Slack API limitations

### Technical
- All new tools follow async patterns with proper rate limiting
- Comprehensive error handling for permission-based operations
- Support for enterprise grid workspaces (team_id parameter)
- Rich formatted responses for all channel operations

## [1.1.0] - 2025-07-03

### 🚀 Phase 4: Extended Messaging Tools

This release adds comprehensive messaging management capabilities, expanding from 7 to 15 production-ready MCP tools.

### ✨ Features Added

#### 📝 **Message Management**
- **`update_message`**: Edit and update existing messages with new text, blocks, and attachments
- **`delete_message`**: Remove messages from channels with proper error handling
- **`pin_message`**: Pin important messages to channels for visibility
- **`unpin_message`**: Remove pinned messages from channels
- **`get_message_permalink`**: Generate shareable links to specific messages

#### ⏰ **Message Scheduling**
- **`schedule_message`**: Schedule messages for future delivery with Unix timestamp support
- Full support for rich formatting (blocks and attachments) in scheduled messages
- Comprehensive scheduling feedback with formatted timestamps

#### 🧵 **Thread Operations**
- **`get_thread_replies`**: Retrieve and display thread conversations with full formatting
- Enhanced thread navigation with parent message context
- Comprehensive reply listing with timestamps and user information
- Configurable reply limits (up to 1000 messages)

#### 💬 **Direct Messaging**
- **`send_direct_message`**: Send private messages directly to users
- Automatic DM conversation opening and management
- Full support for rich formatting in direct messages
- User-friendly recipient identification

### 🔧 Technical Improvements

#### **Enhanced Error Handling**
- Consistent error formatting across all new tools
- Comprehensive Slack API error translation
- Improved user feedback with specific error messages
- Graceful handling of edge cases and API limitations

#### **Async Operations**
- All new tools implement full async/await patterns
- Consistent rate limiting across extended messaging operations
- Optimized API call patterns for better performance
- Proper resource management for concurrent operations

#### **Response Formatting**
- Rich, user-friendly output formatting for all tools
- Consistent emoji usage for visual clarity
- Comprehensive status reporting with detailed information
- Proper truncation for long content with visual indicators

### 🛠️ **Implementation Details**

#### **Code Organization**
- Clean separation of Phase 4 tools with clear commenting
- Consistent parameter validation using existing patterns
- Reuse of established helper functions (`make_slack_request`, `init_async_client`)
- Maintained code style and documentation standards

#### **Version Management**
- Version bumped to 1.1.0 for feature release
- Updated test scripts to verify all 15 tools
- Enhanced tool discovery and validation
- Maintained backward compatibility with existing tools

### 📊 **Current Capabilities**

**15 Production-Ready MCP Tools:**
- **Authentication**: `set_slack_token`, `test_slack_connection`
- **Basic Messaging**: `send_message`, `send_direct_message`
- **Message Management**: `update_message`, `delete_message`, `pin_message`, `unpin_message`
- **Advanced Features**: `schedule_message`, `get_message_permalink`, `get_thread_replies`
- **Workspace Discovery**: `list_channels`, `get_channel_info`, `get_user_info`

### 🧪 **Testing & Validation**

- All 15 tools successfully registered and validated
- Container builds tested and verified
- Tool discovery functioning properly
- Async operations tested for consistency
- Error handling validated across all new tools

### 🔮 **Future Development**

Phase 4 completion sets the foundation for:
- **Phase 5**: Channel Management Tools
- **Phase 6**: User Management Tools  
- **Phases 8-13**: Search, interactions, analytics, and production features

### 🏆 **Achievement Summary**

✅ **8 new messaging tools** implemented and tested  
✅ **Doubled tool count** from 7 to 15 production-ready tools  
✅ **Extended messaging capabilities** covering all major message operations  
✅ **Maintained code quality** and consistency standards  
✅ **Full async implementation** with proper error handling  
✅ **Comprehensive testing** and validation completed  

---

*Phase 4 represents a significant expansion of messaging capabilities, providing users with comprehensive control over Slack message operations while maintaining the high quality and reliability standards established in previous phases.*

## [1.0.0] - 2025-07-03

### 🎉 Initial Release

This is the first stable release of the Slack MCP Server, providing comprehensive Slack API integration through the Model Context Protocol (MCP).

### ✨ Features Added

#### 🔐 Authentication & Security
- **Token Management**: Secure Slack bot token handling via environment variables
- **Token Validation**: Automatic validation of token format and API connectivity
- **Multi-token Support**: Support for Bot tokens (`xoxb-`) and User tokens (`xoxp-`)
- **Rate Limiting**: Built-in rate limiting compliance (1-second minimum intervals)

#### 💬 Messaging Tools
- **send_message**: Send messages to channels, users, or threads
- **Rich Text Support**: Full support for Slack blocks and attachments
- **Thread Support**: Reply to existing threads with `thread_ts` parameter
- **Multi-channel Support**: Send messages to multiple channels simultaneously

#### 🏢 Workspace Discovery
- **list_channels**: List and categorize workspace channels with beautiful formatting
- **get_channel_info**: Detailed channel information including members, topic, purpose
- **Channel Types**: Support for public, private, and archived channels
- **Member Counts**: Display channel membership statistics

#### 👥 User Management
- **get_user_info**: Comprehensive user profile information
- **User Status**: Display names, titles, status messages, and timezone info
- **Admin Detection**: Identify admin users and bot accounts
- **Email Lookup**: Support for user lookup by email address


#### 🔌 Connection & Testing
- **test_slack_connection**: Comprehensive connection testing and workspace info
- **Workspace Details**: Display workspace name, domain, and branding
- **API Configuration**: Show rate limiting and User-Agent configuration
- **Connection Diagnostics**: Detailed error reporting for troubleshooting

### 🏗️ Architecture

#### 🐳 Docker-First Design
- **Multi-stage Dockerfile**: Optimized for development and production
- **Python 3.12**: Latest Python version with full async support
- **uv Package Manager**: Fast, reliable dependency management
- **Container Security**: Non-root user execution in production
- **Health Checks**: Built-in container health monitoring

#### ⚡ MCP Protocol Implementation
- **FastMCP Framework**: Leverages Python type hints for automatic tool registration
- **STDIO Transport**: Primary transport method for MCP clients
- **Async Operations**: All tools use async/await for optimal performance
- **Type Safety**: Full type hints and Pydantic validation
- **Error Handling**: Comprehensive error handling with user-friendly messages

#### 🔄 Async Operations
- **AsyncWebClient**: Full async Slack API integration
- **Rate Limiting**: Async delays for API compliance
- **Concurrent Operations**: Support for multiple simultaneous API calls
- **Resource Management**: Proper async context management

### 🛠️ Technical Implementation

#### Dependencies
- **mcp[cli] 1.10.1+**: Official MCP protocol implementation
- **slack-sdk 3.35.0+**: Official Slack SDK for Python
- **aiohttp 3.12.13+**: Async HTTP client for Slack WebClient
- **httpx 0.28.1+**: Modern async HTTP client
- **pydantic 2.11.7+**: Data validation and settings management
- **python-dotenv 1.1.1+**: Environment variable management

#### Configuration
- **Environment Variables**: `SLACK_BOT_TOKEN` for authentication
- **MCP Integration**: Compatible with Claude Desktop, Warp, and other MCP clients
- **Docker Configuration**: Support for both direct Docker and wrapper script approaches
- **Cross-platform**: Works on Linux, macOS, and Windows (in containers)

### 📖 Documentation

#### Configuration Guides
- **CONFIGURATION_GUIDE.md**: Comprehensive setup instructions for different MCP clients
- **Warp Configuration**: Correct format for Warp.dev MCP integration
- **Claude Desktop**: Proper configuration for Claude Desktop
- **Docker Examples**: Multiple deployment patterns and wrapper scripts

#### Development Documentation
- **ROADMAP.md**: Detailed development phases and completion status
- **README.md**: Quick start guide and feature overview
- **Container Documentation**: Docker build and deployment instructions

### 🧪 Testing & Quality

#### Test Coverage
- **Tool Registration**: Automated testing of all 7 MCP tools
- **Container Testing**: Verification of Docker container functionality
- **API Validation**: Mock testing of Slack API integration
- **Error Handling**: Comprehensive error condition testing

#### Quality Assurance
- **Type Checking**: Full type hint coverage
- **Linting**: Code quality enforcement
- **Container Verification**: Multi-stage build testing
- **Integration Testing**: End-to-end MCP protocol testing

### 🚀 Deployment

#### Container Support
- **Production Ready**: Optimized Docker image for production deployment
- **Development Mode**: Live-reload container for development
- **Multi-architecture**: Support for AMD64 and ARM64 platforms
- **Registry Ready**: Prepared for Docker Hub or private registry deployment

#### MCP Client Integration
- **Claude Desktop**: Full compatibility with official configuration format
- **Warp.dev**: Optimized for Warp's MCP integration
- **Custom Clients**: Standard MCP protocol compliance for any client
- **Wrapper Scripts**: Shell scripts for complex deployment scenarios

### 📊 Current Capabilities

**6 Production-Ready MCP Tools:**
1. `set_slack_token` - Configure authentication
2. `test_slack_connection` - Verify connectivity and show workspace info
3. `send_message` - Send messages with full formatting support
4. `get_channel_info` - Retrieve detailed channel information
5. `list_channels` - Explore workspace channels with categorization
6. `get_user_info` - Get comprehensive user profiles

**Workspace Tested:**
- Successfully tested with ILDM workspace
- 4 public channels discovered and interacted with
- Message sending and channel listing verified
- Full authentication and rate limiting confirmed working

### 🔜 Future Development

The roadmap includes 10 additional phases for advanced features:
- **Phases 4-6**: Extended messaging, channel management, and user operations
- **Phases 7-9**: Search capabilities and interactive elements
- **Phases 10-13**: Advanced features, analytics, and production deployment

### 👨‍💻 Attribution

**Author**: Brennon Church (atarukun@gmail.com)  
**License**: MIT License  
**Repository**: https://github.com/atarukun/slack-mcp  

### 🙏 Acknowledgments

- Model Context Protocol (MCP) team for the excellent protocol specification
- Slack for their comprehensive API and SDK
- FastMCP framework for simplifying MCP server development
- Docker and uv teams for excellent development tools

---

## Version History

### [1.0.0] - 2025-07-03
- Initial stable release with 6 core tools
- Full Docker containerization
- MCP protocol compliance
- Comprehensive documentation

---

*Note: This changelog follows the [Keep a Changelog](https://keepachangelog.com/) format and will be updated with each release.*
