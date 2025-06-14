# Replit.md - Growex Telegram Bot

## Overview

This is a Telegram bot designed to calculate shipping costs for consolidated cargo delivery from Turkey to Russia. The bot provides an interactive interface for users to input cargo specifications and receive instant cost estimates, while also collecting leads for the business through optional contact information gathering.

## System Architecture

The application follows a modular Python architecture built on the aiogram framework (v2.25.1). The bot uses a finite state machine pattern to manage user conversations and different calculation flows.

### Core Architecture Components:
- **Bot Engine**: aiogram-based Telegram bot with polling
- **State Management**: FSM (Finite State Machine) for conversation flows
- **Data Storage**: File-based JSON storage for counters and statistics
- **Configuration Management**: Environment variables for sensitive data
- **Modular Handler System**: Separated handlers for different conversation flows

## Key Components

### 1. Handler System (`handlers/`)
- **start.py**: Initial bot interaction and main menu
- **calc_flow.py**: Calculation workflows (volume/weight/description based)
- **contact_collection.py**: Lead generation through contact gathering
- **fallback.py**: Error handling and unrecognized input management

### 2. Utilities (`utils/`)
- **tariffs.py**: Shipping cost calculation engine with city-based coefficients
- **validations.py**: Input validation for emails, phones, and cargo specifications
- **counter.py**: Statistics tracking for calculations and leads

### 3. Templates (`templates/`)
- **messages.py**: Centralized message templates and text constants

### 4. Configuration
- **config.py**: Environment variable management and validation
- **.env**: Bot token and manager chat ID storage

## Data Flow

1. **User Initiation**: User starts with `/start` command
2. **Flow Selection**: User chooses calculation method (volume+weight, volume only, weight only, or description)
3. **Data Collection**: Bot guides user through relevant input collection
4. **Calculation**: System calculates shipping cost using tariff engine
5. **Result Display**: User receives cost estimate with breakdown
6. **Optional Contact Collection**: Bot offers to collect contact information for follow-up
7. **Manager Notification**: If contacts provided, lead is sent to manager chat
8. **Statistics Update**: Counters are updated for analytics

## External Dependencies

### Primary Dependencies:
- **aiogram 2.25.1**: Telegram Bot API framework
- **python-dotenv 1.0.1**: Environment variable management

### System Requirements:
- Python 3.11+
- File system access for JSON storage
- Internet connection for Telegram API

## Deployment Strategy

The application is configured for deployment on Replit with the following setup:

### Replit Configuration:
- **Runtime**: Python 3.11 on Nix stable-24_05
- **Startup**: Automatic dependency installation and bot execution
- **File Structure**: Organized modular architecture
- **Environment**: Secure token and chat ID management

### Deployment Process:
1. Dependencies installed via pip from requirements file
2. Bot starts with polling mode
3. Automatic directory creation for data storage
4. Logging configured for monitoring

### Key Architectural Decisions:

**State Management**: Chose aiogram's FSM for conversation flow management
- **Problem**: Need to handle multi-step user interactions
- **Solution**: Finite State Machine with clear state transitions
- **Rationale**: Provides clean separation of conversation stages and prevents user confusion

**File-Based Storage**: JSON files for statistics instead of database
- **Problem**: Need simple persistence for counters
- **Solution**: JSON file storage in data/ directory
- **Rationale**: Lightweight solution for simple data, easy backup and inspection

**Modular Handler System**: Separated handlers by functionality
- **Problem**: Complex bot logic needs organization
- **Solution**: Separate modules for different conversation flows
- **Rationale**: Improves maintainability and allows independent development of features

**Tariff Calculation Engine**: City-based coefficient system
- **Problem**: Different delivery costs to different Russian cities
- **Solution**: Base rates with city-specific multipliers
- **Rationale**: Flexible pricing that can be easily updated and maintained

## Recent Changes

```
Recent Changes:
✓ June 14, 2025: Fixed FSM storage configuration - bot now properly handles conversation states
✓ June 14, 2025: Verified all core functionality working (calculations, validations, counters)
✓ June 14, 2025: Bot successfully deployed and polling Telegram API
✓ June 14, 2025: All handler flows tested and operational
```

## User Preferences

```
Preferred communication style: Russian language, simple and clear explanations.
```