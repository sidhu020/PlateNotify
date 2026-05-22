# helpers.py
"""Utility helper functions for PlateNotify.

Includes URL validation for safe redirects and message flashing utilities.
"""

from flask import flash, request, url_for, redirect
from urllib.parse import urlparse, urljoin


def safe_redirect(endpoint, **values):
    """Redirect to a given endpoint only if the target URL is safe.

    This prevents an attacker from supplying a malicious `next` parameter 
    that points to an external site.
    
    Args:
        endpoint (str): The Flask endpoint to redirect to
        **values: Additional URL parameters
        
    Returns:
        Response: Redirect response to the safe endpoint
    """
    target = url_for(endpoint, **values)
    if not is_safe_url(target):
        return redirect(url_for('index'))
    return redirect(target)


def is_safe_url(target):
    """Return True if the URL is safe for redirects.
    
    Prevents open redirect vulnerabilities by ensuring the target URL
    is on the same host as the current request.
    
    Args:
        target (str): The URL to validate
        
    Returns:
        bool: True if URL is safe, False otherwise
    """
    host_url = request.host_url
    ref_url = urlparse(host_url)
    test_url = urlparse(urljoin(host_url, target))
    return (test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc)


def flash_message(message, category='info'):
    """Convenient wrapper around Flask's flash with a default category.
    
    Args:
        message (str): The message to flash to the user
        category (str): The message category (info, success, warning, danger). 
                       Defaults to 'info'
    """
    flash(message, category)


def format_datetime(dt):
    """Format a datetime object as a readable string.
    
    Args:
        dt (datetime): The datetime to format
        
    Returns:
        str: Formatted datetime string (e.g., '2024-01-15 14:30')
    """
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M')
    return 'Unknown'


def send_telegram_message(token, chat_id, text):
    """Send a message to a Telegram chat using the Bot API.
    
    Gemini told me using Python's built-in urllib is much better because it doesn't
    require adding 'requests' to requirements.txt!
    """
    import json
    import urllib.request
    import urllib.error

    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    # Prepare data and request
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    try:
        # Gemini said to put a timeout=5 here, otherwise if Telegram is down,
        # our anonymous reporter will be stuck waiting forever for the page to load!
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except urllib.error.URLError as e:
        # We just print it to logs and return False – we don't want to crash the page!
        print(f"Error sending Telegram notification: {e}")
        return False

