import re

path = '/home/z/my-project/WebScraperPro/ui/main_window.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add LogPanel import
content = content.replace(
    'from ui.panels.settings_panel import SettingsPanel',
    'from ui.panels.settings_panel import SettingsPanel\nfrom ui.panels.log_panel import LogPanel'
)

# 2. Add logs to NAV
content = content.replace(
    '"proxies": "\u2295",\n        "scheduler":',
    '"proxies": "\u2295",\n        "logs": "\u2630",\n        "scheduler":'
)

content = content.replace(
    'NAV_LABELS = ["Scraper", "Proxies", "Scheduler", "Settings"]',
    'NAV_LABELS = ["Scraper", "Proxies", "Logs", "Scheduler", "Settings"]'
)

content = content.replace(
    'NAV_KEYS = ["dashboard", "scraper", "proxies", "scheduler", "settings"]',
    'NAV_KEYS = ["dashboard", "scraper", "proxies", "logs", "scheduler", "settings"]'
)

# 3. Version
content = content.replace('"v1.0.0"', '"v1.1.0"')

# 4. Add log panel creation
content = content.replace(
    'self._panels["settings"] = SettingsPanel(self._content_frame)',
    'self._panels["settings"] = SettingsPanel(self._content_frame)\n        self._panels["logs"] = LogPanel(self._content_frame)\n        self._log_panel = self._panels["logs"]'
)

# 5. Add logs to title_map
content = content.replace(
    '"proxies": "Proxy Manager",\n            "scheduler":',
    '"proxies": "Proxy Manager",\n            "logs": "Logs",\n            "scheduler":'
)

# 6. Wire log callback
content = content.replace(
    'def _on_log(self, message: str, level: str = "info"):\n        pass',
    'def _on_log(self, message: str, level: str = "info"):\n        self.after(0, lambda: self._log_panel.add_log(message, level))'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Done - main_window.py updated')
