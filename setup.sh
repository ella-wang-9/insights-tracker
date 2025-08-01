#!/bin/bash

set -e

# Check for --auto-close flag and temp file
AUTO_CLOSE=false
TEMP_FILE=""
if [ "$1" = "--auto-close" ]; then
    AUTO_CLOSE=true
    TEMP_FILE="$2"
fi

# Function to signal completion on exit
cleanup() {
    if [ "$AUTO_CLOSE" = true ] && [ -n "$TEMP_FILE" ]; then
        echo "setup_complete" > "$TEMP_FILE"
    fi
}

# Set trap to call cleanup on exit
if [ "$AUTO_CLOSE" = true ]; then
    trap cleanup EXIT
fi

echo "🚀 Databricks App Template Setup"
echo "================================="

# Function to prompt for input with default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    read -p "$prompt [$default]: " input
    if [ -z "$input" ]; then
        input="$default"
    fi
    
    # Set the variable dynamically
    eval "$var_name='$input'"
}

# Function to update or add a value in .env.local
update_env_value() {
    local key="$1"
    local value="$2"
    local comment="$3"
    
    if grep -q "^${key}=" .env.local 2>/dev/null; then
        # Update existing value
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS sed
            sed -i '' "s|^${key}=.*|${key}=${value}|" .env.local
        else
            # Linux sed
            sed -i "s|^${key}=.*|${key}=${value}|" .env.local
        fi
    else
        # Add new value with comment if provided
        if [ -n "$comment" ]; then
            echo "" >> .env.local
            echo "# $comment" >> .env.local
        fi
        echo "${key}=${value}" >> .env.local
    fi
}

# Function to test databricks connection
test_databricks_connection() {
    local profile="$1"
    echo "🔍 Testing Databricks connection..."
    
    # Ensure environment variables are exported for databricks CLI
    if [ -n "$DATABRICKS_HOST" ] && [ -n "$DATABRICKS_TOKEN" ]; then
        export DATABRICKS_HOST
        export DATABRICKS_TOKEN
    fi
    
    if [ -n "$profile" ]; then
        if databricks current-user me --profile "$profile" >/dev/null 2>&1; then
            echo "✅ Successfully connected to Databricks with profile '$profile'"
            return 0
        else
            echo "❌ Failed to connect to Databricks with profile '$profile'"
            return 1
        fi
    else
        if databricks current-user me >/dev/null 2>&1; then
            echo "✅ Successfully connected to Databricks"
            return 0
        else
            echo "❌ Failed to connect to Databricks"
            return 1
        fi
    fi
}

# Check if .env.local already exists
if [ -f ".env.local" ]; then
    echo "📋 Found existing .env.local file."
    read -p "Do you want to update it? (y/N): " update_env
    if [[ ! "$update_env" =~ ^[Yy]$ ]]; then
        echo "Skipping environment configuration."
        skip_env=true
    fi
fi

if [ "$skip_env" != "true" ]; then
    echo "⚙️  Setting up environment variables..."
    
    # Load existing values if they exist
    if [ -f ".env.local" ]; then
        source .env.local 2>/dev/null || true
    fi
    
    # Initialize .env.local file if it doesn't exist
    if [ ! -f ".env.local" ]; then
        echo "# Databricks App Configuration" > .env.local
        echo "# Generated by setup script on $(date)" >> .env.local
        echo "" >> .env.local
    fi
    
    # Databricks Authentication Configuration
    echo ""
    echo "🔐 Databricks Authentication"
    echo "-----------------------------"
    echo "Choose authentication method:"
    echo "1. Personal Access Token (PAT)"
    echo "2. Configuration Profile"
    echo ""
    
    # Pre-select based on existing configuration
    if [ "$DATABRICKS_AUTH_TYPE" = "pat" ]; then
        default_choice="1"
    elif [ "$DATABRICKS_AUTH_TYPE" = "profile" ]; then
        default_choice="2"
    else
        default_choice=""
    fi
    
    if [ -n "$default_choice" ]; then
        prompt_with_default "Select option" "$default_choice" "auth_choice"
    else
        read -p "Select option (1 or 2): " auth_choice
    fi
    
    if [ "$auth_choice" = "1" ]; then
        # PAT Authentication
        echo ""
        echo "📝 Personal Access Token Setup"
        echo "-------------------------------"
        
        # Update auth type in .env.local
        update_env_value "DATABRICKS_AUTH_TYPE" "pat" "Databricks Authentication Type"
        
        if [ -z "$DATABRICKS_HOST" ]; then
            prompt_with_default "Databricks Host" "https://your-workspace.cloud.databricks.com" "DATABRICKS_HOST"
        else
            prompt_with_default "Databricks Host" "$DATABRICKS_HOST" "DATABRICKS_HOST"
        fi
        
        # Update host in .env.local
        update_env_value "DATABRICKS_HOST" "$DATABRICKS_HOST" "Databricks Configuration (PAT mode)"
        
        if [ -n "$DATABRICKS_TOKEN" ]; then
            echo "Found existing token: ${DATABRICKS_TOKEN:0:10}... (truncated)"
            read -p "Use existing token? (y/N): " use_existing
            if [[ ! "$use_existing" =~ ^[Yy]$ ]]; then
                DATABRICKS_TOKEN=""
            fi
        fi
        
        if [ -z "$DATABRICKS_TOKEN" ]; then
            echo ""
            echo "You can create a Personal Access Token here:"
            echo "📖 $DATABRICKS_HOST/settings/user/developer/access-tokens"
            echo ""
            read -s -p "Databricks Personal Access Token: " DATABRICKS_TOKEN
            echo ""
        fi
        
        # Update token in .env.local
        update_env_value "DATABRICKS_TOKEN" "$DATABRICKS_TOKEN"
        
        # Set empty profile to indicate PAT mode
        DATABRICKS_CONFIG_PROFILE=""
        DATABRICKS_AUTH_TYPE="pat"
        
        # Test PAT authentication
        echo "🔍 Testing PAT authentication..."
        export DATABRICKS_HOST="$DATABRICKS_HOST"
        export DATABRICKS_TOKEN="$DATABRICKS_TOKEN"
        
        echo "Attempting to connect with:"
        echo "Host: $DATABRICKS_HOST"
        echo "Token: ${DATABRICKS_TOKEN:0:10}... (truncated)"
        echo ""
        
        # Test connection and show output for debugging
        echo "Running: databricks current-user me"
        # Export for databricks CLI
        export DATABRICKS_HOST="$DATABRICKS_HOST"
        export DATABRICKS_TOKEN="$DATABRICKS_TOKEN"
        if databricks current-user me >/dev/null 2>&1; then
            echo "✅ Successfully connected to Databricks with PAT"
        else
            echo ""
            echo "❌ PAT authentication failed."
            echo "Please check your host URL and token are correct."
            echo "You can test manually with:"
            echo "DATABRICKS_HOST='$DATABRICKS_HOST' DATABRICKS_TOKEN='$DATABRICKS_TOKEN' databricks current-user me"
            exit 1
        fi
        
    elif [ "$auth_choice" = "2" ]; then
        # Profile Authentication
        echo ""
        echo "📋 Configuration Profile Setup"
        echo "-------------------------------"
        
        # Update auth type in .env.local
        update_env_value "DATABRICKS_AUTH_TYPE" "profile" "Databricks Authentication Type"
        
        # List existing profiles
        echo "Available profiles:"
        if [ -f "$HOME/.databrickscfg" ]; then
            grep '^\[' "$HOME/.databrickscfg" | sed 's/\[//g' | sed 's/\]//g' | sed 's/^/  - /'
        else
            echo "  No existing profiles found"
        fi
        echo ""
        
        prompt_with_default "Databricks Config Profile" "${DATABRICKS_CONFIG_PROFILE:-DEFAULT}" "DATABRICKS_CONFIG_PROFILE"
        
        # Update profile in .env.local
        update_env_value "DATABRICKS_CONFIG_PROFILE" "$DATABRICKS_CONFIG_PROFILE" "Databricks Configuration (Profile mode)"
        
        # Clear PAT credentials when using profile
        update_env_value "DATABRICKS_HOST" ""
        update_env_value "DATABRICKS_TOKEN" ""
        DATABRICKS_HOST=""
        DATABRICKS_TOKEN=""
        DATABRICKS_AUTH_TYPE="profile"
        
        # Test profile authentication
        if ! test_databricks_connection "$DATABRICKS_CONFIG_PROFILE"; then
            echo ""
            echo "Profile '$DATABRICKS_CONFIG_PROFILE' not found or invalid."
            echo "Would you like to configure it now? (y/N)"
            read -p "> " configure_profile
            
            if [[ "$configure_profile" =~ ^[Yy]$ ]]; then
                echo "Running 'databricks configure --profile $DATABRICKS_CONFIG_PROFILE'..."
                databricks configure --profile "$DATABRICKS_CONFIG_PROFILE"
                
                # Test again after configuration
                if ! test_databricks_connection "$DATABRICKS_CONFIG_PROFILE"; then
                    echo "❌ Profile configuration failed. Please check your settings."
                    exit 1
                fi
            else
                echo "❌ Valid Databricks authentication is required for deployment."
                exit 1
            fi
        fi
        
    else
        echo "❌ Invalid option. Please run setup again."
        exit 1
    fi
    
    # Get current user information (only if we don't have existing DBA_SOURCE_CODE_PATH)
    if [ -z "$DBA_SOURCE_CODE_PATH" ]; then
        echo ""
        echo "🔍 Getting user information..."
        
        if [ "$DATABRICKS_AUTH_TYPE" = "profile" ]; then
            DATABRICKS_USER=$(databricks current-user me --profile "$DATABRICKS_CONFIG_PROFILE" --output json 2>/dev/null | grep -o '"userName":"[^"]*"' | cut -d'"' -f4)
        else
            DATABRICKS_USER=$(databricks current-user me --output json 2>/dev/null | grep -o '"userName":"[^"]*"' | cut -d'"' -f4)
        fi
        
        if [ -n "$DATABRICKS_USER" ]; then
            echo "✅ Detected user: $DATABRICKS_USER"
        else
            echo "⚠️  Could not detect user, will use default email"
        fi
    else
        echo ""
        echo "✅ Using existing configuration from .env.local"
    fi
    
    # App Configuration
    echo ""
    echo "🚀 App Configuration"
    echo "--------------------"
    echo "If you haven't created a Databricks App yet, you can create a custom app from the UI:"
    if [ "$DATABRICKS_AUTH_TYPE" = "profile" ]; then
        WORKSPACE_HOST=$(databricks current-user me --profile "$DATABRICKS_CONFIG_PROFILE" --output json 2>/dev/null | grep -o '"workspaceUrl":"[^"]*"' | cut -d'"' -f4)
    else
        WORKSPACE_HOST="$DATABRICKS_HOST"
    fi
    
    if [ -n "$WORKSPACE_HOST" ]; then
        echo "📖 $WORKSPACE_HOST/apps/create"
    else
        echo "📖 https://your-workspace.cloud.databricks.com/apps/create"
    fi
    echo ""
    prompt_with_default "App Name for Deployment" "${DATABRICKS_APP_NAME:-my-databricks-app}" "DATABRICKS_APP_NAME"
    
    # Update the default source path to use the chosen app name
    if [ -z "$DBA_SOURCE_CODE_PATH" ]; then
        if [ -n "$DATABRICKS_USER" ]; then
            DEFAULT_SOURCE_PATH="/Workspace/Users/$DATABRICKS_USER/$DATABRICKS_APP_NAME"
        else
            DEFAULT_SOURCE_PATH="/Workspace/Users/<your-email@company.com>/$DATABRICKS_APP_NAME"
        fi
    else
        DEFAULT_SOURCE_PATH="$DBA_SOURCE_CODE_PATH"
    fi
    
    prompt_with_default "Source Code Path for Deployment" "$DEFAULT_SOURCE_PATH" "DBA_SOURCE_CODE_PATH"
    
    # Update app configuration in .env.local
    update_env_value "DATABRICKS_APP_NAME" "$DATABRICKS_APP_NAME" "Databricks App Configuration"
    update_env_value "DBA_SOURCE_CODE_PATH" "$DBA_SOURCE_CODE_PATH"
    
    echo ""
    echo "✅ Environment configuration saved to .env.local"
fi

# Check for required tools
echo ""
echo "🔧 Checking dependencies..."

# Check for databricks CLI
if ! command -v databricks &> /dev/null; then
    echo "❌ Databricks CLI not found. Please install it first:"
    echo "   Visit: https://docs.databricks.com/dev-tools/cli/install.html"
    echo "   Or run: pip install databricks-cli"
    exit 1
fi

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
fi

# Check for bun
if ! command -v bun &> /dev/null; then
    echo "❌ bun not found. Installing bun..."
    curl -fsSL https://bun.sh/install | bash
    source ~/.bashrc
fi

echo "✅ All required tools are available"

# Install Claude MCP Playwright (if Claude Code is available)
echo ""
echo "🎭 Installing Claude MCP Playwright..."
if command -v claude &> /dev/null; then
    claude mcp add playwright npx '@playwright/mcp@latest'
    echo "✅ Claude MCP Playwright installed"
else
    echo "⚠️  Claude Code CLI not found, skipping MCP Playwright installation"
    echo "💡 You can install it later with: claude mcp add playwright npx '@playwright/mcp@latest'"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
uv sync --dev

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd client
bun install
cd ..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "⚠️  IMPORTANT: Please restart Claude Code to enable MCP Playwright integration"
echo ""
echo "Next steps:"
echo "1. Restart Claude Code (close and reopen the application)"
echo "2. Run './watch.sh' to start the development servers"
echo "3. Open http://localhost:3000 to view the app"
echo "4. Open http://localhost:8000/docs to view the API documentation"
echo ""
echo "Optional:"
echo "- Run './fix.sh' to format your code"
echo "- Edit .env.local to update configuration"

# Auto-close terminal if flag is set
if [ "$AUTO_CLOSE" = true ]; then
    echo ""
    echo "Press Enter to close this terminal..."
    read
    # Close appropriate terminal app
    if [ -d "/Applications/iTerm.app" ]; then
        # For iTerm, close the current window
        osascript -e 'tell application "iTerm" to close current window'
    else
        # For Terminal, close windows containing setup.sh
        osascript -e 'tell application "Terminal" to close (every window whose name contains "setup.sh")'
    fi
fi