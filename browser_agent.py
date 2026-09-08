import os
import json
import time
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

class KiraBrowserAgent:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self, headless=False):
        if not PLAYWRIGHT_AVAILABLE:
            print("[WARN] Playwright not installed. Browser agent disabled.")
            return
            
        if not self.playwright:
            self.playwright = sync_playwright().start()
        if not self.browser:
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.context = self.browser.new_context(viewport={"width": 1280, "height": 720})
            self.page = self.context.new_page()

    def stop(self):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

    def navigate(self, url: str):
        if not self.page:
            self.start()
        if not self.page:
            return
        if not url.startswith("http"):
            url = f"https://{url}"
        self.page.goto(url, wait_until="domcontentloaded")
        time.sleep(1) # wait for animations

    def get_dom_structure(self):
        """Returns simplified DOM structure for LLM grounding."""
        if not self.page:
            return []
            
        script = """
        () => {
            const elements = Array.from(document.querySelectorAll('a, button, input, textarea, select'));
            return elements.map((e, i) => {
                const rect = e.getBoundingClientRect();
                return {
                    id: i,
                    tag: e.tagName.toLowerCase(),
                    text: (e.innerText || e.value || e.placeholder || '').substring(0, 50).trim(),
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    visible: rect.width > 0 && rect.height > 0
                };
            }).filter(e => e.visible && e.text.length > 0);
        }
        """
        return self.page.evaluate(script)

    def execute_action(self, action_type: str, target: str = None, value: str = None):
        """
        Execute a universal browser action.
        Supports standard locators as well as mapping OmniParser relative coordinates.
        """
        if not self.page:
            self.start()
        if not self.page:
            return False, "Browser agent not available (Playwright missing)."
            
        try:
            if action_type == "goto":
                self.navigate(target)
                return True, f"Navigated to {target}"
                
            elif action_type == "click_coords":
                # Converts OmniParser normalised coords (0-1) to Playwright viewport pixels
                # e.g., target="0.5,0.2"
                cx, cy = map(float, target.split(","))
                vp = self.page.viewport_size
                px = int(cx * vp["width"])
                py = int(cy * vp["height"])
                self.page.mouse.click(px, py)
                return True, f"Clicked coordinate ({px}, {py})"
                
            elif action_type == "click_text":
                locator = self.page.get_by_text(target).first
                if locator.count() > 0:
                    locator.click()
                    return True, f"Clicked '{target}'"
                
                locator = self.page.locator(f"text='{target}'").first
                if locator.count() > 0:
                    locator.click()
                    return True, f"Clicked '{target}' (exact match)"
                    
                return False, f"Could not find element with text '{target}'"
                
            elif action_type == "type_text":
                # target could be text or a placeholder
                locator = self.page.get_by_text(target).first
                if locator.count() == 0:
                    locator = self.page.get_by_placeholder(target).first
                
                if locator.count() > 0:
                    locator.fill(value)
                    self.page.keyboard.press("Enter")
                    return True, f"Typed '{value}' into '{target}'"
                return False, f"Could not find input field '{target}'"
                
            elif action_type == "scroll":
                amount = int(value) if value else 500
                self.page.mouse.wheel(0, amount)
                return True, f"Scrolled by {amount}px"
                
            elif action_type == "wait":
                secs = float(value) if value else 1.0
                time.sleep(secs)
                return True, f"Waited {secs}s"
                
        except Exception as e:
            return False, f"Error executing {action_type}: {e}"
            
        return False, f"Unknown action: {action_type}"

# Singleton for reuse
browser_agent = KiraBrowserAgent()
