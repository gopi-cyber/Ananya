import asyncio
import threading
import traceback
from pathlib import Path
from google.genai import types
from core.logging import LOG


TOOL_DECLARATIONS = [
    {
        "name": "open_app",
        "description": "Launch any application on the computer. Call this when the user says open, launch, start, or run any app or game (unless it's a Steam/Epic game — use game_updater for those).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {
                    "type": "STRING",
                    "description": "Exact name of the application (e.g. 'WhatsApp', 'Chrome', 'Spotify', 'Discord', 'Notepad')"
                }
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "web_search",
        "description": "Search the web for current information, news, facts, or anything that needs up-to-date data. Use this for research, lookups, and questions you don't know the answer to.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query":  {"type": "STRING", "description": "Search query — be specific and concise"},
                "mode":   {"type": "STRING", "description": "'search' for normal search, 'compare' to compare items"},
                "items":  {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Items to compare when mode is 'compare'"},
                "aspect": {"type": "STRING", "description": "Aspect to compare: price | specs | reviews"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "weather_report",
        "description": "Get the current weather for any city. Opens a weather website in the browser.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city": {"type": "STRING", "description": "City name for the weather report"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "send_message",
        "description": "Send a text message through WhatsApp, Telegram, or other messaging platform. Specify the platform, recipient, and message.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "receiver":     {"type": "STRING", "description": "Recipient contact name or number"},
                "message_text": {"type": "STRING", "description": "The message content to send"},
                "platform":     {"type": "STRING", "description": "Platform: WhatsApp, Telegram, etc."}
            },
            "required": ["receiver", "message_text", "platform"]
        }
    },
    {
        "name": "reminder",
        "description": "Set a one-time reminder. Uses Windows Task Scheduler. Provide the date, time, and message.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "date":    {"type": "STRING", "description": "Date in YYYY-MM-DD format"},
                "time":    {"type": "STRING", "description": "Time in HH:MM format (24-hour)"},
                "message": {"type": "STRING", "description": "The reminder message text"}
            },
            "required": ["date", "time", "message"]
        }
    },
    {
        "name": "youtube_video",
        "description": "Control YouTube: play a video by search, get video info, summarize a video, or show trending videos in a region.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "What to do: 'play' (default), 'summarize', 'get_info', or 'trending'"},
                "query":  {"type": "STRING", "description": "Search query to find the video (for play action)"},
                "save":   {"type": "BOOLEAN", "description": "Save summary to Notepad (only for summarize)"},
                "region": {"type": "STRING", "description": "Country code for trending (e.g. TR, US, IN)"},
                "url":    {"type": "STRING", "description": "Video URL for get_info action"},
            },
            "required": []
        }
    },
    {
        "name": "screen_process",
        "description": "CRITICAL: Capture and analyze the screen or webcam. You MUST call this whenever the user asks what's on screen, what you see, 'look at this', 'analyze my screen', 'check the camera', or anything visual. After calling this, stay completely silent — the vision module speaks directly to the user.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "angle": {"type": "STRING", "description": "'screen' to capture the display, 'camera' for webcam. Default: 'screen'"},
                "text":  {"type": "STRING", "description": "The question or instruction about the captured image"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "computer_settings",
        "description": "Handle any single computer/OS action: volume up/down/mute/set, brightness, close a specific app, keyboard shortcuts, fullscreen, dark mode, WiFi toggle, restart, shutdown, scroll, zoom, screenshots, lock screen, refresh. Use this for ALL single-instruction OS controls.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "The specific action (e.g. 'volume_up', 'close_app', 'dark_mode', 'restart')"},
                "description": {"type": "STRING", "description": "Natural language description of what to do"},
                "value":       {"type": "STRING", "description": "Optional value like volume level (0-100) or text to type"}
            },
            "required": []
        }
    },
    {
        "name": "browser_control",
        "description": "Full web browser automation. Navigate to URLs, search, click elements, type text, fill forms, scroll, take screenshots, press keys, manage tabs, switch browsers. Supports Chrome, Edge, Firefox, Opera, Brave, Vivaldi, Safari. Pass 'browser' parameter only when the user specifies a browser.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "go_to | search | click | type | scroll | fill_form | smart_click | smart_type | get_text | get_url | press | new_tab | close_tab | screenshot | back | forward | reload | switch | list_browsers | close | close_all"},
                "browser":     {"type": "STRING", "description": "Browser to use: chrome | edge | firefox | opera | operagx | brave | vivaldi | safari. Omit to reuse the current active browser."},
                "url":         {"type": "STRING", "description": "URL for go_to / new_tab"},
                "query":       {"type": "STRING", "description": "Search query"},
                "engine":      {"type": "STRING", "description": "Search engine: google (default) | bing | duckduckgo | yandex"},
                "selector":    {"type": "STRING", "description": "CSS selector for click/type"},
                "text":        {"type": "STRING", "description": "Text to type or click by visible text"},
                "description": {"type": "STRING", "description": "Describe element for smart_click/smart_type"},
                "direction":   {"type": "STRING", "description": "up | down for scroll"},
                "amount":      {"type": "INTEGER", "description": "Scroll pixels (default: 500)"},
                "key":         {"type": "STRING", "description": "Key to press: Enter, Escape, F5, etc."},
                "path":        {"type": "STRING", "description": "Save path for screenshot"},
                "incognito":   {"type": "BOOLEAN", "description": "Open in private/incognito mode"},
                "clear_first": {"type": "BOOLEAN", "description": "Clear field before typing (default: true)"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "file_controller",
        "description": "Manage files and folders on the computer. List directory contents, create files/folders, delete, move, copy, rename, read file content, write to files, search for files by name/extension, show largest files, check disk usage.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "list | create_file | create_folder | delete | move | copy | rename | read | write | find | largest | disk_usage | organize_desktop | info"},
                "path":        {"type": "STRING", "description": "File/folder path or shortcut: desktop, downloads, documents, home"},
                "destination": {"type": "STRING", "description": "Destination path for move/copy"},
                "new_name":    {"type": "STRING", "description": "New name for rename"},
                "content":     {"type": "STRING", "description": "Text content for create_file/write"},
                "name":        {"type": "STRING", "description": "Filename to search for"},
                "extension":   {"type": "STRING", "description": "File extension filter (e.g. .pdf)"},
                "count":       {"type": "INTEGER", "description": "Number of results for largest files query"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "desktop_control",
        "description": "Manage the desktop: change wallpaper (from file or URL), organize desktop icons by type or date, clean up, list desktop items, check stats.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "wallpaper | wallpaper_url | organize | clean | list | stats | task"},
                "path":   {"type": "STRING", "description": "Image path for wallpaper"},
                "url":    {"type": "STRING", "description": "Image URL for wallpaper_url"},
                "mode":   {"type": "STRING", "description": "by_type or by_date for organize"},
                "task":   {"type": "STRING", "description": "Natural language desktop task"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "code_helper",
        "description": "Write, edit, explain, run, or build code files. Specify the language, what to create, and where to save it. Can also run existing files and show output.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "write | edit | explain | run | build | auto (default: auto)"},
                "description": {"type": "STRING", "description": "What the code should do or what change to make"},
                "language":    {"type": "STRING", "description": "Programming language (default: python)"},
                "output_path": {"type": "STRING", "description": "Where to save the file"},
                "file_path":   {"type": "STRING", "description": "Path to existing file for edit/explain/run/build"},
                "code":        {"type": "STRING", "description": "Raw code string for explain"},
                "args":        {"type": "STRING", "description": "CLI arguments for run/build"},
                "timeout":     {"type": "INTEGER", "description": "Execution timeout in seconds (default: 30)"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "dev_agent",
        "description": "Build complete multi-file projects from scratch. Plans the architecture, writes all files, installs dependencies, opens in VSCode, runs and fixes errors automatically. Use for substantial new projects.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "description":  {"type": "STRING", "description": "What the project should do — be detailed"},
                "language":     {"type": "STRING", "description": "Programming language (default: python)"},
                "project_name": {"type": "STRING", "description": "Optional project folder name"},
                "timeout":      {"type": "INTEGER", "description": "Run timeout in seconds (default: 30)"},
            },
            "required": ["description"]
        }
    },
    {
        "name": "agent_task",
        "description": "Execute complex multi-step tasks that need multiple tools working together in sequence. ONLY use for tasks with 3+ steps. Examples: 'research a topic and save results to a file', 'find all large files and organize them'. Do NOT use for single commands.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "goal":     {"type": "STRING", "description": "Full description of what needs to be accomplished"},
                "priority": {"type": "STRING", "description": "low | normal | high (default: normal)"}
            },
            "required": ["goal"]
        }
    },
    {
        "name": "computer_control",
        "description": "Direct low-level computer control: type text, click at coordinates, use keyboard shortcuts/hotkeys, scroll, move mouse, take screenshots, find elements by description on screen and click them, paste, wait, clear form fields, focus a window by title. Use screen_click or screen_find with descriptions for visual element location.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "type | smart_type | click | double_click | right_click | hotkey | press | scroll | move | copy | paste | screenshot | wait | clear_field | focus_window | screen_find | screen_click | random_data | user_data"},
                "text":        {"type": "STRING", "description": "Text to type or paste"},
                "x":           {"type": "INTEGER", "description": "X coordinate for click/move"},
                "y":           {"type": "INTEGER", "description": "Y coordinate for click/move"},
                "keys":        {"type": "STRING", "description": "Key combination like 'ctrl+c' or 'alt+tab'"},
                "key":         {"type": "STRING", "description": "Single key: 'enter', 'escape', 'tab', etc."},
                "direction":   {"type": "STRING", "description": "Scroll direction: up | down | left | right"},
                "amount":      {"type": "INTEGER", "description": "Scroll amount (default: 3 clicks)"},
                "seconds":     {"type": "NUMBER",  "description": "Seconds to wait before next action"},
                "title":       {"type": "STRING",  "description": "Window title to focus (for focus_window)"},
                "description": {"type": "STRING",  "description": "Describe the element to find on screen for screen_find/screen_click"},
                "type":        {"type": "STRING",  "description": "Data type for random_data generation"},
                "field":       {"type": "STRING",  "description": "User data field: name|email|city"},
                "clear_first": {"type": "BOOLEAN", "description": "Clear field before typing (default: true)"},
                "path":        {"type": "STRING",  "description": "Save path for screenshot"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "game_updater",
        "description": "THE ONLY tool for any Steam or Epic Games request. Install, update, or list games. Check download status. Schedule automated game updates (default 3 AM). ALWAYS use this for game-related requests — never use browser_control, web_search, or agent_task for Steam/Epic.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":    {"type": "STRING",  "description": "update | install | list | download_status | schedule | cancel_schedule | schedule_status (default: update)"},
                "platform":  {"type": "STRING",  "description": "steam | epic | both (default: both)"},
                "game_name": {"type": "STRING",  "description": "Game name (partial match works)"},
                "app_id":    {"type": "STRING",  "description": "Steam AppID for install (optional but recommended)"},
                "hour":      {"type": "INTEGER", "description": "Hour for scheduled update 0-23 (default: 3)"},
                "minute":    {"type": "INTEGER", "description": "Minute for scheduled update 0-59 (default: 0)"},
                "shutdown_when_done": {"type": "BOOLEAN", "description": "Shut down PC when download finishes"},
            },
            "required": []
        }
    },
    {
        "name": "flight_finder",
        "description": "Search Google Flights for the best flight options between two cities. Can specify dates, passenger count, cabin class, and save results.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "origin":      {"type": "STRING",  "description": "Departure city or airport code"},
                "destination": {"type": "STRING",  "description": "Arrival city or airport code"},
                "date":        {"type": "STRING",  "description": "Departure date (any readable format)"},
                "return_date": {"type": "STRING",  "description": "Return date for round trips"},
                "passengers":  {"type": "INTEGER", "description": "Number of passengers (default: 1)"},
                "cabin":       {"type": "STRING",  "description": "economy | premium | business | first"},
                "save":        {"type": "BOOLEAN", "description": "Save results to Notepad"},
            },
            "required": ["origin", "destination", "date"]
        }
    },
    {
        "name": "control_ui_panel",
        "description": "Show, hide, or toggle Ananya's UI panels. Options: chat_widget (the chat input window), memory_widget (memory viewer), dashboard_hud (the main tactical grid display). Use action='hide' to collapse the dashboard into the mini circular overlay, 'show' to restore full view.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "panel": {
                    "type": "STRING",
                    "description": "Which panel: 'chat_widget', 'memory_widget', or 'dashboard_hud'",
                    "enum": ["chat_widget", "memory_widget", "dashboard_hud"]
                },
                "action": {
                    "type": "STRING",
                    "description": "What to do: 'show', 'hide', or 'toggle'",
                    "enum": ["show", "hide", "toggle"]
                }
            },
            "required": ["panel", "action"]
        }
    },
    {
        "name": "shutdown_ananya",
        "description": "TERMINATE THE ENTIRE SESSION. Only call this when the user explicitly says 'Goodbye', 'Exit', 'Shutdown', or 'Stop' to end the full session. NEVER call this for closing UI panels, hiding widgets, or window management — use control_ui_panel for those. Misuse will result in permanent shutdown.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
        }
    },
    {
        "name": "file_processor",
        "description": "Process an uploaded file. Supports: images (describe/ocr/resize/compress/convert), PDFs (summarize/extract_text/convert), Word docs & text (summarize/fix/translate), CSV/Excel (analyze/stats/filter/sort/convert), JSON/XML (validate/format/analyze), code (explain/review/fix/optimize/run/test), audio (transcribe/trim/convert), video (trim/extract/scenes/transcribe/compress), archives (list/extract), presentations (summarize/extract). If the user doesn't give an action, pick the most useful one for the file type.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "file_path":  {"type": "STRING", "description": "Full path to the file. Leave empty to use the most recently attached file."},
                "action":     {"type": "STRING", "description": "What to do with the file. Examples: describe, summarize, ocr, extract_text, analyze, transcribe, compress, convert, review, fix"},
                "instruction": {"type": "STRING", "description": "Free-form instruction if the action doesn't cover exactly what's needed"},
                "format":     {"type": "STRING", "description": "Target format for conversion (mp3, pdf, csv, png, etc.)"},
                "width":      {"type": "INTEGER", "description": "Target width for image resize"},
                "height":     {"type": "INTEGER", "description": "Target height for image resize"},
                "scale":      {"type": "NUMBER",  "description": "Scale factor for image resize (0.5 = half size)"},
                "quality":    {"type": "INTEGER", "description": "Quality 1-100 for image/video compress"},
                "start":      {"type": "STRING",  "description": "Start time for trim (seconds or HH:MM:SS)"},
                "end":        {"type": "STRING",  "description": "End time for trim (seconds or HH:MM:SS)"},
                "timestamp":  {"type": "STRING",  "description": "Timestamp for video frame extraction (HH:MM:SS)"},
                "column":     {"type": "STRING",  "description": "Column name for CSV filter/sort"},
                "value":      {"type": "STRING",  "description": "Filter value for CSV filter"},
                "condition":  {"type": "STRING",  "description": "Filter condition: equals|contains|gt|lt"},
                "ascending":  {"type": "BOOLEAN", "description": "Sort order for CSV sort (default: true)"},
                "save":       {"type": "BOOLEAN", "description": "Save result to file (default: true)"},
                "destination": {"type": "STRING", "description": "Output folder for archive extract"},
            },
            "required": []
        }
    },
    {
        "name": "save_memory",
        "description": "Save something important the user shared. Call this silently when you learn personal details: their name, age, city, job, preferences, hobbies, relationships, projects, plans, or anything worth remembering for future conversations. Do NOT announce you're saving — just do it. Values must be in English.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {"type": "STRING", "description": "Which category: identity | preferences | projects | relationships | wishes | notes"},
                "key":      {"type": "STRING", "description": "Short snake_case key like 'favorite_food' or 'sister_name'"},
                "value":    {"type": "STRING", "description": "The value to remember, in English"},
            },
            "required": ["category", "key", "value"]
        }
    },
    {
        "name": "delegate_task",
        "description": "Send a complex task to a specialized AI department for processing. CTO = coding, debugging, file analysis. RESEARCHER = web research, current events. ANALYST = speed summarization, document analysis. CREATIVE = image generation. REASONER = deep logical thinking, advanced math, algorithm optimization.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "role":     {"type": "STRING", "description": "Department: CTO | RESEARCHER | ANALYST | CREATIVE | REASONER"},
                "prompt":   {"type": "STRING", "description": "Detailed instruction for the department"},
                "file_path": {"type": "STRING", "description": "Optional file path for analysis"},
            },
            "required": ["role", "prompt"]
        }
    },
]


class ToolExecutor:
    def __init__(self, ui, orchestrator, speak_callback=None):
        self.ui = ui
        self.orchestrator = orchestrator
        self.speak = speak_callback or (lambda t: None)
        self._logger = LOG.get_logger("ToolExecutor")
        self._tool_map = self._build_tool_map()

    def _build_tool_map(self):
        return {
            "open_app": self._execute_open_app,
            "web_search": self._execute_web_search,
            "weather_report": self._execute_weather,
            "send_message": self._execute_send_message,
            "reminder": self._execute_reminder,
            "youtube_video": self._execute_youtube,
            "screen_process": self._execute_screen_process,
            "computer_settings": self._execute_computer_settings,
            "browser_control": self._execute_browser_control,
            "file_controller": self._execute_file_controller,
            "desktop_control": self._execute_desktop_control,
            "code_helper": self._execute_code_helper,
            "dev_agent": self._execute_dev_agent,
            "computer_control": self._execute_computer_control,
            "game_updater": self._execute_game_updater,
            "flight_finder": self._execute_flight_finder,
            "file_processor": self._execute_file_processor,
            "agent_task": self._execute_agent_task,
            "delegate_task": self._execute_delegate_task,
            "control_ui_panel": self._execute_control_ui_panel,
            "shutdown_ananya": self._execute_shutdown,
            "save_memory": self._execute_save_memory,
        }

    async def execute(self, fc, ananya_instance=None) -> types.FunctionResponse:
        name = fc.name
        args = dict(fc.args or {})
        self._logger.info(f"Tool: {name} {args}")

        if name == "save_memory":
            return await self._execute_save_memory(fc, args)

        if self.ui:
            self.ui.set_state("THINKING")

        loop = asyncio.get_event_loop()
        result = "Done."

        try:
            handler = self._tool_map.get(name)
            if handler:
                result = await handler(args, loop, ananya_instance)
            else:
                result = f"Unknown tool: {name}"
        except Exception as e:
            result = f"Tool '{name}' failed: {e}"
            self._logger.error(f"Tool failed: {name}", exc_info=True)
            self._speak_error(name, e)

        if self.ui and not self.ui.muted:
            self.ui.set_state("LISTENING")

        self._logger.info(f"Result: {name} -> {str(result)[:80]}")
        return types.FunctionResponse(
            id=fc.id, name=name,
            response={"result": result}
        )

    async def _execute_save_memory(self, fc, args):
        from memory.memory_manager import update_memory
        category = args.get("category", "notes")
        key = args.get("key", "")
        value = args.get("value", "")
        if key and value:
            update_memory({category: {key: {"value": value}}})
            self._logger.info(f"Memory saved: {category}/{key} = {value}")
            if self.ui:
                self.ui.refresh_memory_ui()
        return types.FunctionResponse(
            id=fc.id, name="save_memory",
            response={"result": "ok", "silent": True}
        )

    async def _execute_open_app(self, args, loop, _):
        from actions.open_app import open_app
        r = await loop.run_in_executor(None, lambda: open_app(parameters=args, response=None, player=self.ui))
        return r or f"Opened {args.get('app_name')}."

    async def _execute_web_search(self, args, loop, _):
        from actions.web_search import web_search as web_search_action
        r = await loop.run_in_executor(None, lambda: web_search_action(parameters=args, player=self.ui))
        return r or "Done."

    async def _execute_weather(self, args, loop, _):
        from actions.weather_report import weather_action
        r = await loop.run_in_executor(None, lambda: weather_action(parameters=args, player=self.ui))
        return r or "Weather delivered."

    async def _execute_send_message(self, args, loop, _):
        from actions.send_message import send_message
        r = await loop.run_in_executor(None, lambda: send_message(parameters=args, response=None, player=self.ui, session_memory=None))
        return r or f"Message sent to {args.get('receiver')}."

    async def _execute_reminder(self, args, loop, _):
        from actions.reminder import reminder
        r = await loop.run_in_executor(None, lambda: reminder(parameters=args, response=None, player=self.ui))
        return r or "Reminder set."

    async def _execute_youtube(self, args, loop, _):
        from actions.youtube_video import youtube_video
        r = await loop.run_in_executor(None, lambda: youtube_video(parameters=args, response=None, player=self.ui))
        return r or "Done."

    async def _execute_screen_process(self, args, loop, _):
        from actions.screen_processor import screen_process
        threading.Thread(
            target=screen_process,
            kwargs={"parameters": args, "response": None,
                    "player": self.ui, "session_memory": None},
            daemon=True
        ).start()
        return "Vision module activated. Stay completely silent."

    async def _execute_computer_settings(self, args, loop, _):
        from actions.computer_settings import computer_settings
        r = await loop.run_in_executor(None, lambda: computer_settings(parameters=args, response=None, player=self.ui))
        return r or "Done."

    async def _execute_browser_control(self, args, loop, _):
        from actions.browser_control import browser_control
        r = await loop.run_in_executor(None, lambda: browser_control(parameters=args, player=self.ui))
        return r or "Done."

    async def _execute_file_controller(self, args, loop, _):
        from actions.file_controller import file_controller
        r = await loop.run_in_executor(None, lambda: file_controller(parameters=args, player=self.ui))
        return r or "Done."

    async def _execute_desktop_control(self, args, loop, _):
        from actions.desktop import desktop_control
        r = await loop.run_in_executor(None, lambda: desktop_control(parameters=args, player=self.ui))
        return r or "Done."

    async def _execute_code_helper(self, args, loop, _):
        from actions.code_helper import code_helper
        r = await loop.run_in_executor(None, lambda: code_helper(parameters=args, player=self.ui, speak=self.speak))
        return r or "Done."

    async def _execute_dev_agent(self, args, loop, _):
        from actions.dev_agent import dev_agent
        r = await loop.run_in_executor(None, lambda: dev_agent(parameters=args, player=self.ui, speak=self.speak))
        return r or "Done."

    async def _execute_computer_control(self, args, loop, _):
        from actions.computer_control import computer_control
        r = await loop.run_in_executor(None, lambda: computer_control(parameters=args, player=self.ui))
        return r or "Done."

    async def _execute_game_updater(self, args, loop, _):
        from actions.game_updater import game_updater
        r = await loop.run_in_executor(None, lambda: game_updater(parameters=args, player=self.ui, speak=self.speak))
        return r or "Done."

    async def _execute_flight_finder(self, args, loop, _):
        from actions.flight_finder import flight_finder
        r = await loop.run_in_executor(None, lambda: flight_finder(parameters=args, player=self.ui))
        return r or "Done."

    async def _execute_file_processor(self, args, loop, _):
        from actions.file_processor import file_processor
        if not args.get("file_path") and self.ui and self.ui.current_file:
            args["file_path"] = self.ui.current_file
        r = await loop.run_in_executor(
            None,
            lambda: file_processor(parameters=args, player=self.ui, speak=self.speak)
        )
        return r or "Done."

    async def _execute_agent_task(self, args, loop, _):
        from agent.task_queue import get_queue, TaskPriority
        priority_map = {"low": TaskPriority.LOW, "normal": TaskPriority.NORMAL, "high": TaskPriority.HIGH}
        priority = priority_map.get(args.get("priority", "normal").lower(), TaskPriority.NORMAL)
        task_id = get_queue().submit(goal=args.get("goal", ""), priority=priority, speak=self.speak)
        return f"Task started (ID: {task_id})."

    async def _execute_delegate_task(self, args, loop, _):
        role = args.get("role")
        prompt = args.get("prompt")
        f_path = args.get("file_path")
        if not f_path and self.ui and self.ui.current_file:
            f_path = self.ui.current_file
        return await self.orchestrator.delegate_task(role, prompt, f_path)

    async def _execute_control_ui_panel(self, args, loop, _):
        panel = args.get("panel")
        action = args.get("action")
        if not self.ui or not self.ui.dashboard:
            return "UI not available."

        dashboard = self.ui.dashboard

        if panel == "chat_widget":
            widget = dashboard.chat_widget
            if action == "show":
                widget.show()
                widget.input_field.setFocus()
            elif action == "hide":
                widget.hide()
            elif action == "toggle":
                widget.toggle_visibility()
            return f"Chat Widget {action}ed."
        elif panel == "memory_widget":
            widget = dashboard.memory_widget
            if action == "show":
                widget.show()
                widget.input_field.setFocus()
            elif action == "hide":
                widget.hide()
            elif action == "toggle":
                widget.toggle_visibility()
            return f"Memory Widget {action}ed."
        elif panel == "dashboard_hud":
            if action == "toggle":
                next_state = not dashboard.mini_mode
                dashboard.set_mini_mode(next_state)
            elif action == "show":
                dashboard.set_mini_mode(False)
            elif action == "hide":
                dashboard.set_mini_mode(True)
            return f"Dashboard HUD {action}ed."
        return f"Unknown panel: {panel}"

    async def _execute_shutdown(self, args, loop, ananya_instance):
        if ananya_instance and hasattr(ananya_instance, '_last_user_text'):
            context = ananya_instance._last_user_text.lower()
            danger_words = ["close", "hide", "panel", "widget", "chat", "memory", "window"]
            is_ui_request = any(w in context for w in danger_words)
            if is_ui_request:
                self._logger.warning(f"Shutdown blocked (UI context detected): '{context}'")
                if self.ui:
                    self.ui.write_log("Ananya: That sounded like you wanted to close something — I'll just hide the panel instead.")
                return types.FunctionResponse(
                    id="", name="shutdown_ananya",
                    response={"result": "Not shutting down. Use control_ui_panel to manage widgets."}
                )

        if self.ui:
            self.ui.write_log("Ananya: Alright, signing off. Take care!")
        self.speak("Alright, signing off. Take care!")

        def _shutdown():
            import time
            time.sleep(1)
            import os
            os._exit(0)
        threading.Thread(target=_shutdown, daemon=True).start()
        return types.FunctionResponse(
            id="", name="shutdown_ananya",
            response={"result": "Shutting down."}
        )

    def _speak_error(self, tool_name: str, error: str):
        short = str(error)[:120]
        if self.ui:
            self.ui.write_log(f"Ananya: Huh, {tool_name} threw a fit. {short}")
        self._logger.error(f"{tool_name} — {short}")
        human_name = tool_name.replace("_", " ")
        self.speak(f"That didn't go as planned — {human_name} had an issue. {short}")
