#!/bin/bash

################################################################################
# Telegram Downloader Files Extractor
# 
# This script parses the markdown artifact and extracts all code blocks
# into their respective files, maintaining the correct directory structure.
#
# Usage: ./extract_files.sh <markdown_file>
# Example: ./extract_files.sh telegram-downloader-files.md
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if markdown file is provided
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: No markdown file specified${NC}"
    echo "Usage: $0 <markdown_file>"
    echo "Example: $0 telegram-downloader-files.md"
    exit 1
fi

MARKDOWN_FILE="$1"

# Check if file exists
if [ ! -f "$MARKDOWN_FILE" ]; then
    echo -e "${RED}Error: File '$MARKDOWN_FILE' not found${NC}"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Telegram Downloader Files Extractor${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Processing: ${YELLOW}$MARKDOWN_FILE${NC}"
echo ""

# Create project directory if it doesn't exist
PROJECT_DIR="telegram-downloader"
if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
    echo -e "${GREEN}✓${NC} Created project directory: $PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Counter for extracted files
EXTRACTED_COUNT=0

# Temporary variables
CURRENT_FILE=""
IN_CODE_BLOCK=false
CODE_CONTENT=""

# Process the markdown file line by line
while IFS= read -r line; do
    # Check for file header (## File: `filename`)
    if [[ "$line" =~ ^##[[:space:]]+File:[[:space:]]+\`([^\`]+)\` ]]; then
        CURRENT_FILE="${BASH_REMATCH[1]}"
        IN_CODE_BLOCK=false
        CODE_CONTENT=""
        continue
    fi
    
    # Check for code block start (```language or just ```)
    if [[ "$line" =~ ^\`\`\`[a-z]* ]] && [ -n "$CURRENT_FILE" ]; then
        if [ "$IN_CODE_BLOCK" = false ]; then
            # Starting a code block
            IN_CODE_BLOCK=true
            CODE_CONTENT=""
        else
            # Ending a code block - write the file
            if [ -n "$CODE_CONTENT" ]; then
                # Create directory if filename contains path
                DIR_NAME=$(dirname "$CURRENT_FILE")
                if [ "$DIR_NAME" != "." ] && [ ! -d "$DIR_NAME" ]; then
                    mkdir -p "$DIR_NAME"
                fi
                
                # Write the file
                echo -n "$CODE_CONTENT" > "$CURRENT_FILE"
                echo -e "${GREEN}✓${NC} Extracted: ${YELLOW}$CURRENT_FILE${NC}"
                
                # Make scripts executable
                if [[ "$CURRENT_FILE" == *.sh ]]; then
                    chmod +x "$CURRENT_FILE"
                    echo -e "  ${BLUE}→${NC} Made executable"
                fi
                
                EXTRACTED_COUNT=$((EXTRACTED_COUNT + 1))
            fi
            
            IN_CODE_BLOCK=false
            CODE_CONTENT=""
            CURRENT_FILE=""
        fi
        continue
    fi
    
    # If we're in a code block, accumulate the content
    if [ "$IN_CODE_BLOCK" = true ]; then
        if [ -z "$CODE_CONTENT" ]; then
            CODE_CONTENT="$line"
        else
            CODE_CONTENT="$CODE_CONTENT"$'\n'"$line"
        fi
    fi
    
done < "../$MARKDOWN_FILE"

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Extraction Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Total files extracted: ${GREEN}$EXTRACTED_COUNT${NC}"
echo -e "Project location: ${YELLOW}$(pwd)${NC}"
echo ""

# Check if .env.example exists and .env doesn't
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠${NC}  Next steps:"
    echo -e "   1. Copy .env.example to .env:"
    echo -e "      ${BLUE}cp .env.example .env${NC}"
    echo -e "   2. Edit .env and add your Telegram API credentials:"
    echo -e "      ${BLUE}nano .env${NC}"
    echo -e "   3. Get API credentials from: ${BLUE}https://my.telegram.org${NC}"
    echo ""
fi

echo -e "${GREEN}✓${NC} Ready to build and run!"
echo -e "   Next: ${BLUE}docker compose build${NC}"
echo ""