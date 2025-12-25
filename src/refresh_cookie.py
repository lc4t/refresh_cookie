"""
Cookie Refresher - Main Entry Point
Automatically refresh cookies by visiting a webpage using Playwright + Chromium
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from cookie_utils import parse_netscape_cookies, save_netscape_cookies


def setup_logger(log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure logger with file and/or stdout output.

    Args:
        log_file: Path to log file. If None, logs to stdout only.

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    logger.handlers = []

    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        try:
            # Create parent directory if needed
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.info(f"Logging to file: {log_file}")
        except Exception as e:
            logger.warning(f"Failed to setup file logging: {e}")

    return logger


def parse_custom_headers(headers_json: str) -> Dict[str, str]:
    """
    Parse JSON format custom headers.

    Args:
        headers_json: JSON string of headers

    Returns:
        Dictionary of headers

    Raises:
        json.JSONDecodeError: If JSON is invalid
    """
    if not headers_json or headers_json.strip() == '':
        return {}

    try:
        headers = json.loads(headers_json)
        if not isinstance(headers, dict):
            raise ValueError("Headers must be a JSON object")
        return {str(k): str(v) for k, v in headers.items()}
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format for CUSTOM_HEADERS: {e}")


def validate_env_vars() -> Dict[str, str]:
    """
    Validate and retrieve environment variables.

    Returns:
        Dictionary of environment variables

    Raises:
        ValueError: If required environment variables are missing
    """
    required_vars = ['URL', 'COOKIE_FILE', 'OUTPUT_COOKIE', 'OUTPUT_HTML']
    env_vars = {}

    # Check required variables
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            env_vars[var] = value

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Optional variables with defaults
    env_vars['WAIT_TIME'] = int(os.getenv('WAIT_TIME', '5'))
    env_vars['REFRESH_DELAY'] = int(os.getenv('REFRESH_DELAY', '5'))
    env_vars['CUSTOM_HEADERS'] = os.getenv('CUSTOM_HEADERS', '{}')
    env_vars['LOG_FILE'] = os.getenv('LOG_FILE')

    return env_vars


async def main():
    """Main execution flow"""
    logger = None

    try:
        # 1. Parse and validate environment variables
        env = validate_env_vars()

        # Setup logger
        logger = setup_logger(env['LOG_FILE'])
        logger.info("=== Cookie Refresher Started ===")
        logger.info(f"Target URL: {env['URL']}")
        logger.info(f"Input Cookie: {env['COOKIE_FILE']}")
        logger.info(f"Output Cookie: {env['OUTPUT_COOKIE']}")
        logger.info(f"Output HTML: {env['OUTPUT_HTML']}")

        # 2. Parse custom headers
        custom_headers = parse_custom_headers(env['CUSTOM_HEADERS'])
        if custom_headers:
            logger.info(f"Custom headers: {list(custom_headers.keys())}")

        # 3. Load cookies from Netscape format
        logger.info("Loading cookies from file...")
        cookies = parse_netscape_cookies(env['COOKIE_FILE'])
        logger.info(f"Loaded {len(cookies)} cookies")

        # 4. Launch Playwright
        logger.info("Launching Chromium browser...")
        async with async_playwright() as p:
            # Launch browser with anti-detection settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )

            # Default User-Agent (can be overridden by custom headers)
            default_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

            # Create context with cookies
            context_options = {
                "user_agent": custom_headers.get('User-Agent', default_ua),
            }

            context = await browser.new_context(**context_options)

            # Add cookies to context
            await context.add_cookies(cookies)
            logger.info("Cookies added to browser context")

            # Create page
            page = await context.new_page()

            # Set custom headers
            if custom_headers:
                await page.set_extra_http_headers(custom_headers)
                logger.info("Custom headers applied")

            # Hide webdriver property
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            # 5. Navigate to URL
            logger.info(f"Navigating to {env['URL']}...")
            try:
                response = await page.goto(env['URL'], wait_until='networkidle', timeout=30000)
                logger.info(f"Page loaded with status: {response.status}")
            except Exception as e:
                logger.error(f"Navigation failed: {e}")
                raise

            # 6. Wait for initial load
            logger.info(f"Waiting {env['WAIT_TIME']} seconds for page to fully load...")
            await asyncio.sleep(env['WAIT_TIME'])

            # 7. Refresh page
            logger.info("Refreshing page...")
            await page.reload(wait_until='networkidle', timeout=30000)

            # 8. Wait after refresh
            logger.info(f"Waiting {env['REFRESH_DELAY']} seconds after refresh...")
            await asyncio.sleep(env['REFRESH_DELAY'])

            # 9. Get updated cookies
            logger.info("Retrieving updated cookies...")
            updated_cookies = await context.cookies()
            logger.info(f"Retrieved {len(updated_cookies)} cookies")

            # Compare cookie count
            if len(updated_cookies) != len(cookies):
                logger.warning(f"Cookie count changed: {len(cookies)} -> {len(updated_cookies)}")

            # 10. Get rendered HTML
            logger.info("Retrieving rendered HTML...")
            html_content = await page.evaluate("document.documentElement.outerHTML")
            logger.info(f"HTML content length: {len(html_content)} characters")

            # 11. Save cookies to Netscape format
            logger.info(f"Saving cookies to {env['OUTPUT_COOKIE']}...")
            # Create output directory if needed
            Path(env['OUTPUT_COOKIE']).parent.mkdir(parents=True, exist_ok=True)
            save_netscape_cookies(updated_cookies, env['OUTPUT_COOKIE'])

            # 12. Save HTML
            logger.info(f"Saving HTML to {env['OUTPUT_HTML']}...")
            Path(env['OUTPUT_HTML']).parent.mkdir(parents=True, exist_ok=True)
            with open(env['OUTPUT_HTML'], 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Cleanup
            await context.close()
            await browser.close()

        logger.info("=== Cookie Refresher Completed Successfully ===")
        return 0

    except ValueError as e:
        if logger:
            logger.error(f"Validation error: {e}")
        else:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    except FileNotFoundError as e:
        if logger:
            logger.error(f"File not found: {e}")
        else:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        if logger:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        else:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
