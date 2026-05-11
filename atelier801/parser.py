import re
from datetime import datetime


def extract_csrf_token(html, token_name):
    """Extract CSRF token from HTML"""
    match = re.search(rf'name="{token_name}" value="([^"]+)"', html)
    return match.group(1) if match else None


def extract_any_token(html):
    """Extract any CSRF token from HTML - finds hidden inputs with random-looking values"""
    hidden = re.findall(r'<input[^>]*type="hidden"[^>]*>', html)
    for h in hidden:
        name_match = re.search(r'name="([^"]+)"', h)
        value_match = re.search(r'value="([^"]*)"', h)
        if name_match and value_match:
            name = name_match.group(1)
            value = value_match.group(1)
            if len(value) > 20 and len(name) > 5:
                return name, value
    return None, None


def extract_token_for_action(html, action_url):
    """Extract the token used for a specific action based on nearby form"""
    form_match = re.search(rf'<form[^>]*action="{action_url}"[^>]*>(.*?)</form>', html, re.DOTALL)
    if form_match:
        form_content = form_match.group(1)
        hidden = re.findall(r'<input[^>]*type="hidden"[^>]*>', form_content)
        for h in hidden:
            name_match = re.search(r'name="([^"]+)"', h)
            value_match = re.search(r'value="([^"]+)"', h)
            if name_match and value_match and len(value_match.group(1)) > 20:
                return name_match.group(1), value_match.group(1)
    return None, None


def extract_email(html):
    """Extract email from HTML"""
    match = re.search(r'[\w.-]+@[\w.-]+\.\w+', html)
    return match.group(0) if match else None


def extract_registration_date(html):
    """Extract registration date from HTML"""
    match = re.search(r'(\d{2}/\d{2}/\d{4})', html)
    return match.group(1) if match else None


def extract_username_from_account(html, base_username):
    """Extract full username from account page"""
    match = re.search(rf'{re.escape(base_username.split("#")[0])}#\d+', html)
    return match.group(0) if match else None


def extract_ban_info(html):
    """Extract ban information from profile page"""
    ban_type = re.search(r'<span class="texte-type-sanction">([^<]+)</span>', html)
    ban_reason = re.search(r'<td class="message-plus-moins"[^>]*>([^<]+)</td>', html)
    ban_duration = re.search(r'<span class="texte-duree-sanction"[^>]*>.*?(\d+)\s*heure', html)
    ban_state = re.search(r'<span class="texte-etat-sanction">([^<]+)</span>', html)
    
    ban_start = None
    ban_end = None
    
    sanctions_row = re.search(r'<tr[^>]*>.*?<span class="texte-type-sanction">.*?</tr>', html, re.DOTALL)
    if sanctions_row:
        timestamps = re.findall(r'data-order="(\d+)"', sanctions_row.group(0))
        if len(timestamps) >= 3:
            ban_start_ts = int(timestamps[2]) / 1000
            ban_start = datetime.fromtimestamp(ban_start_ts).strftime('%d/%m/%Y %H:%M:%S')
        if len(timestamps) >= 4:
            ban_end_ts = int(timestamps[3]) / 1000
            ban_end = datetime.fromtimestamp(ban_end_ts).strftime('%d/%m/%Y %H:%M:%S')
    
    if not ban_type:
        return None
    
    info = {
        'type': ban_type.group(1),
        'reason': ban_reason.group(1).strip() if ban_reason else None,
        'duration_hours': int(ban_duration.group(1)) if ban_duration else None,
        'state': ban_state.group(1) if ban_state else None,
        'start': ban_start,
        'end': ban_end,
    }
    
    if ban_end:
        end_date = datetime.strptime(ban_end, '%d/%m/%Y %H:%M:%S')
        remaining = end_date - datetime.now()
        info['remaining'] = remaining if remaining.total_seconds() > 0 else None
    
    return info
