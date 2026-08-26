from dataclasses import dataclass
from typing import List
import re


@dataclass
class CaptchaDetection:
    """Result of a captcha detection check."""
    detected: bool
    captcha_type: str  # recaptcha, hcaptcha, cloudflare, custom, none
    confidence: str  # high, medium, low
    description: str  # Human-readable description


# Patterns that indicate captcha challenges
CAPTCHA_SIGNATURES = {
    "recaptcha": {
        "high": [
            r'g-recaptcha',
            r'google\.com/recaptcha',
            r'recaptcha/api',
            r'recaptcha\\.google',
            r'data-sitekey="[^"]*"',
        ],
        "medium": [
            r'recaptcha',
            r'rc-anchor',
            r'No CAPTCHA',
            r"I'm not a robot",
        ],
    },
    "hcaptcha": {
        "high": [
            r'hcaptcha\.com',
            r'h-captcha',
            r'data-hcaptcha-sitekey',
            r'js\.hcaptcha\.com',
        ],
        "medium": [
            r'hcaptcha',
            r'accessibility_stmt',
        ],
    },
    "cloudflare": {
        "high": [
            r'cloudflare',
            r'cf-browser-verification',
            r'challenge-platform',
            r'cf-turnstile',
            r'challenges\.cloudflare\.com',
        ],
        "medium": [
            r'Just a moment',
            r'Checking your browser',
            r'cf-chl',
            r'cloudflare\-challenge',
        ],
    },
    "custom": {
        "high": [
            r'captcha',
            r'verify you are human',
            r'are you a robot',
            r'bot detection',
            r'solve.*captcha',
        ],
        "low": [
            r'verification',
            r'challenge',
            r'security check',
        ],
    },
}


def detect_captcha(html_content: str) -> CaptchaDetection:
    """
    Analyze HTML content for captcha/challenge signatures.
    Returns a CaptchaDetection with details about what was found.
    """
    if not html_content:
        return CaptchaDetection(detected=False, captcha_type="none",
                               confidence="none", description="No content")

    html_lower = html_content.lower()
    detections = []

    for captcha_type, confidence_levels in CAPTCHA_SIGNATURES.items():
        for confidence, patterns in confidence_levels.items():
            for pattern in patterns:
                if re.search(pattern, html_lower, re.IGNORECASE):
                    detections.append((captcha_type, confidence, pattern))

    if not detections:
        return CaptchaDetection(detected=False, captcha_type="none",
                               confidence="none", description="No captcha detected")

    # Pick the highest-confidence detection
    confidence_order = {"high": 0, "medium": 1, "low": 2}
    detections.sort(key=lambda d: confidence_order.get(d[1], 3))

    best_type, best_conf, best_pattern = detections[0]
    all_types = list(set(d[0] for d in detections))

    type_names = {
        "recaptcha": "Google reCAPTCHA",
        "hcaptcha": "hCaptcha",
        "cloudflare": "Cloudflare Challenge",
        "custom": "Generic Captcha",
    }

    description = f"{type_names.get(best_type, best_type)} detected (confidence: {best_conf})"
    if len(all_types) > 1:
        description += f" [+{len(all_types) - 1} more signals]"

    return CaptchaDetection(
        detected=True,
        captcha_type=best_type,
        confidence=best_conf,
        description=description,
    )


def get_captcha_info_for_log(detection: CaptchaDetection) -> str:
    """Return a formatted log string for a captcha detection."""
    if not detection.detected:
        return ""
    return f"CAPTCHA DETECTED: {detection.description}"
