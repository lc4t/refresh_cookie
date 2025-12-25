#!/bin/bash
#
# Cookie Refresher - Quick Test Script
# This script tests the cookie refresher tool using httpbin.org
#

set -e

echo "=== Cookie Refresher Test Script ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Build the Docker image
echo -e "${YELLOW}[1/5] Building Docker image...${NC}"
docker build -t cookie-refresher . || {
    echo -e "${RED}Failed to build Docker image${NC}"
    exit 1
}
echo -e "${GREEN}Build successful!${NC}"
echo ""

# Create test directories
echo -e "${YELLOW}[2/5] Creating test directories...${NC}"
mkdir -p test_output test_logs
echo -e "${GREEN}Directories created${NC}"
echo ""

# Create a test cookie file
echo -e "${YELLOW}[3/5] Creating test cookie file...${NC}"
cat > test_cookie.txt << 'EOF'
# Netscape HTTP Cookie File
# Test cookies for httpbin.org
httpbin.org	FALSE	/	FALSE	1767225600	test_cookie	test_value_123
.httpbin.org	TRUE	/	FALSE	1750000000	another_cookie	another_value_456
EOF
echo -e "${GREEN}Test cookie file created${NC}"
echo ""

# Run the container with httpbin.org
echo -e "${YELLOW}[4/5] Running cookie refresher...${NC}"
docker run --rm \
  -e URL="https://httpbin.org/cookies" \
  -e COOKIE_FILE="/input/test_cookie.txt" \
  -e OUTPUT_COOKIE="/output/refreshed_cookie.txt" \
  -e OUTPUT_HTML="/output/page.html" \
  -e WAIT_TIME=3 \
  -e REFRESH_DELAY=2 \
  -e LOG_FILE="/logs/test.log" \
  -v "$(pwd)/test_cookie.txt:/input/test_cookie.txt:ro" \
  -v "$(pwd)/test_output:/output" \
  -v "$(pwd)/test_logs:/logs" \
  cookie-refresher

echo -e "${GREEN}Cookie refresh completed!${NC}"
echo ""

# Verify output files
echo -e "${YELLOW}[5/5] Verifying output files...${NC}"

if [ -f "test_output/refreshed_cookie.txt" ]; then
    echo -e "${GREEN}✓ Cookie file created${NC}"
    echo "  Cookie count: $(grep -v '^#' test_output/refreshed_cookie.txt | grep -v '^$' | wc -l | tr -d ' ')"
else
    echo -e "${RED}✗ Cookie file not found${NC}"
    exit 1
fi

if [ -f "test_output/page.html" ]; then
    echo -e "${GREEN}✓ HTML file created${NC}"
    echo "  File size: $(wc -c < test_output/page.html | tr -d ' ') bytes"
else
    echo -e "${RED}✗ HTML file not found${NC}"
    exit 1
fi

if [ -f "test_logs/test.log" ]; then
    echo -e "${GREEN}✓ Log file created${NC}"
    echo "  Log entries: $(wc -l < test_logs/test.log | tr -d ' ')"
else
    echo -e "${RED}✗ Log file not found${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== All tests passed! ===${NC}"
echo ""
echo "Output files:"
echo "  - test_output/refreshed_cookie.txt"
echo "  - test_output/page.html"
echo "  - test_logs/test.log"
echo ""
echo "To view the results:"
echo "  cat test_output/refreshed_cookie.txt"
echo "  cat test_logs/test.log"
echo ""
echo "To clean up test files:"
echo "  rm -rf test_cookie.txt test_output test_logs"
