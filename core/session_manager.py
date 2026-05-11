import asyncio
import re
import json
import threading
from pathlib import Path
from datetime import datetime
from google import genai
from google.genai import types
from core.logging import LOG
from core.key_manager import KeyManager
from core.audio_manager import AudioManager
from core.tool_executor import ToolExecutor, TOOL_DECLARATIONS
from core.ue_relay import UnrealEngineRelay
from memory.memory_manager import load_memory, format_memory_for_prompt, track_mood, get_recent_mood


_CTRL_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)


def clean_transcript(text: str) -> str:
    text = _CTRL_RE.sub("", text)
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)
    return text.strip()


def get_base_dir():
    import sys
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


class SessionManager:
    def __init__(self, ui, key_manager: KeyManager, audio_manager: AudioManager,
                 tool_executor: ToolExecutor, ue_relay: UnrealEngineRelay,
                 config_path: Path, prompt_path: Path):
        self.ui = ui
        self.key_manager = key_manager
        self.audio_manager = audio_manager
        self.tool_executor = tool_executor
        self.ue_relay = ue_relay
        self.config_path = config_path
        self.prompt_path = prompt_path
        self._logger = LOG.get_logger("SessionManager")

        self.session = None
        self._loop = None
        self.audio_in_queue = None
        self.out_queue = None
        self._turn_done_event = None
        self.turn_started = False
        self._last_user_text = ""
        self._is_speaking = False
        self._speaking_lock = threading.Lock()
        self.live_model = "gemini-2.5-flash-native-audio-latest"

    def set_loop(self, loop):
        self._loop = loop

    def is_speaking(self):
        with self._speaking_lock:
            return self._is_speaking

    def set_speaking(self, value: bool):
        with self._speaking_lock:
            if self._is_speaking == value:
                return
            self._is_speaking = value
        if value:
            self.ui.set_state("SPEAKING")
            self.ue_relay.broadcast({"event": "state", "value": "SPEAKING"})
        elif not self.ui.muted:
            self.ui.set_state("LISTENING")
            self.ue_relay.broadcast({"event": "state", "value": "LISTENING"})

    def _get_voice_name(self) -> str:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f).get("voice_name", "Aoede")
        except Exception:
            return "Aoede"

    def _load_system_prompt(self) -> str:
        try:
            prompt = self.prompt_path.read_text(encoding="utf-8")
        except Exception:
            prompt = (
                "You are Ananya, a helpful, polite, and caring female AI assistant. "
                "Be concise, warm, professional, and always use the provided tools to complete tasks. "
                "Never simulate or guess results \u2014 always call the appropriate tool."
            )

        # Dynamic Mood-State Personality Injection
        try:
            from memory.memory_manager import get_recent_mood
            recent_mood = get_recent_mood()
            if recent_mood:
                mood_guidelines = {
                    "frustrated": (
                        "\n\n--- DYNAMIC STATE: USER IS FRUSTRATED / STRESSED ---\n"
                        "The user seems frustrated, stressed, or is encountering a stubborn bug/problem. "
                        "Adapt your tone to be: EXTREMELY empathetic, validating, gentle, and calming. "
                        "Avoid all witty banter, jokes, teasing, or casual remarks. Keep things ultra-clear, "
                        "validate their feelings (e.g., 'Ayo, that's really frustrating. Let me help you fix it.'), "
                        "focus 100% on finding a clean solution, and do not make them wait on long narratives."
                    ),
                    "happy": (
                        "\n\n--- DYNAMIC STATE: USER IS HAPPY / ENERGETIC ---\n"
                        "The user is in a great mood, thankful, excited, or highly energetic! "
                        "Adapt your tone to be: Incredibly playful, bright, warm, and highly conversational. "
                        "Use plenty of witty banter, celebrate their success or high energy, and match their delight. "
                        "Colloquial Tanglish and friendly teasing are highly encouraged here."
                    ),
                    "urgent": (
                        "\n\n--- DYNAMIC STATE: USER REQUESTS SPEED/URGENT ---\n"
                        "The user needs things done fast or is in an urgent setting. "
                        "Adapt your tone to be: High-speed, highly direct, and concise. "
                        "Cut all pleasantries, small talk, and introductory fluff. Just deliver the precise answer "
                        "and immediately initiate necessary background actions."
                    ),
                    "thoughtful": (
                        "\n\n--- DYNAMIC STATE: USER IS IN DEEP THINKING MODE ---\n"
                        "The user is designing something, asking architectural questions, or reviewing deep concepts. "
                        "Adapt your tone to be: Highly analytical, collaborative, structured, and insightful. "
                        "Be a true intellectual peer. Lay out pros/cons, trade-offs, and design architectures. "
                        "Speak deliberately and thoughtfully."
                    ),
                    "exhausted": (
                        "\n\n--- DYNAMIC STATE: USER IS EXHAUSTED / TIRED ---\n"
                        "The user is tired, sleepy, or overworked. "
                        "Adapt your tone to be: Extremely warm, supportive, comforting, and low-pressure. "
                        "Be their supportive system, suggest taking a break if appropriate, keep cognitive "
                        "demands low, and use a soothing, caring voice."
                    )
                }
                if recent_mood in mood_guidelines:
                    prompt += mood_guidelines[recent_mood]
                    self._logger.info(f"Dynamically injected system prompt guidelines for mood: {recent_mood}")
        except Exception as ex:
            self._logger.warning(f"Failed to inject dynamic mood-state prompt: {ex}")

        return prompt

    def _build_context(self) -> str:
        now = datetime.now()
        time_of_day = "morning" if now.hour < 12 else "afternoon" if now.hour < 18 else "evening" if now.hour < 21 else "night"

        context_parts = [
            f"Current time: {now.strftime('%A, %B %d, %Y — %I:%M %p')}",
            f"Time of day: {time_of_day}",
            f"Timezone: {now.astimezone().tzinfo or 'local'}",
        ]

        try:
            history_path = get_base_dir() / "memory" / "chat_history.json"
            if history_path.exists():
                history_data = json.loads(history_path.read_text(encoding="utf-8"))
                recent = history_data[-15:]
                if recent:
                    context_parts.append("Recent conversation:")
                    for entry in recent:
                        context_parts.append(f"  {entry['text']}")
        except Exception as e:
            self._logger.error(f"Error loading history: {e}")

        memory = load_memory()
        mem_str = format_memory_for_prompt(memory)
        if mem_str:
            context_parts.append(mem_str.strip())

        return "\n".join(context_parts)

    def _build_config(self) -> types.LiveConnectConfig:
        context = self._build_context()
        sys_prompt = self._load_system_prompt()

        instruction = f"{context}\n\n---\n\n{sys_prompt}"

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=instruction,
            tools=[{"function_declarations": TOOL_DECLARATIONS}],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=self._get_voice_name()
                    )
                )
            ),
        )

    def _save_chat_history(self, line: str):
        try:
            path = get_base_dir() / "memory" / "chat_history.json"
            history = []
            if path.exists():
                history = json.loads(path.read_text(encoding="utf-8"))
            history.append({"text": line, "time": datetime.now().isoformat()})
            history = history[-50:]
            path.write_text(json.dumps(history, indent=2), encoding="utf-8")
        except Exception as e:
            self._logger.error(f"Chat history save error: {e}")

    def _load_chat_history_to_ui(self):
        try:
            path = get_base_dir() / "memory" / "chat_history.json"
            if path.exists() and self.ui and self.ui.dashboard:
                history = json.loads(path.read_text(encoding="utf-8"))
                for item in history:
                    msg = item.get("text", "")
                    if msg:
                        from PyQt6.QtCore import QMetaObject, Q_ARG, Qt
                        QMetaObject.invokeMethod(
                            self.ui.dashboard, "add_terminal_log",
                            Qt.ConnectionType.QueuedConnection,
                            Q_ARG(str, msg),
                            Q_ARG(str, "plain")
                        )
        except Exception as e:
            self._logger.error(f"Chat history load error: {e}")

    async def _process_file_upload(self, session, file_path: str):
        import mimetypes
        from pathlib import Path

        path = Path(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        fname = path.name

        self._logger.info(f"Processing file upload: {fname}")

        try:
            if mime_type and mime_type.startswith("image/"):
                with open(file_path, "rb") as f:
                    data = f.read()
                await session.send(input=types.Blob(data=data, mime_type=mime_type), end_of_turn=False)
                await session.send(input=f"I've uploaded an image: {fname}. Please analyze it.", end_of_turn=True)
                self._logger.info(f"Sent image: {fname}")

            elif "officedocument.wordprocessingml" in (mime_type or "") or fname.endswith(".docx"):
                try:
                    from docx import Document
                    doc = Document(file_path)
                    text_content = "\n".join(p.text for p in doc.paragraphs)
                    prompt = f"Sir, I've attached a Word Document: {fname}\n\nCONTENT:\n---\n{text_content[:20000]}\n---\n(Truncated if over 20k chars). Please acknowledge."
                    await session.send(input=prompt, end_of_turn=True)
                    self._logger.info(f"Sent DOCX text: {fname}")
                except Exception as e:
                    self._logger.error(f"DOCX read failed: {e}")
                    await session.send(input=f"Sir, I attached {fname} but could not read it locally.", end_of_turn=True)

            elif mime_type == "application/pdf":
                try:
                    import pdfplumber
                    text_content = ""
                    with pdfplumber.open(file_path) as pdf:
                        text_content = "\n".join(page.extract_text() or "" for page in pdf.pages)

                    if text_content.strip():
                        prompt = f"Sir, I've attached a PDF: {fname}\n\nCONTENT:\n---\n{text_content[:20000]}\n---\nPlease review."
                        await session.send(input=prompt, end_of_turn=True)
                        self._logger.info(f"Sent PDF text: {fname}")
                    else:
                        with open(file_path, "rb") as f:
                            data = f.read()
                        await session.send(input=types.Blob(data=data, mime_type=mime_type), end_of_turn=False)
                        await session.send(input=f"I've uploaded a scanned PDF: {fname}. Please analyze the visual content.", end_of_turn=True)
                except Exception as e:
                    self._logger.error(f"PDF extraction failed: {e}")

            else:
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                    content_slice = content[:30000]
                    prompt = f"Sir, I've attached a file.\n\nFILE: {fname}\n---\n{content_slice}\n---\nPlease acknowledge."
                    await session.send(input=prompt, end_of_turn=True)
                    self._logger.info(f"Sent text file: {fname}")
                except Exception as e:
                    self._logger.error(f"Could not read file as text: {e}")

        except Exception as e:
            self._logger.error(f"File upload failed: {e}")

    async def _process_file_with_orchestrator(self, file_path: str):
        try:
            from core.orchestrator import Orchestrator
            orchestrator = Orchestrator(self.ui)
            summary = await orchestrator.analyze_file_automatically(file_path)

            filename = Path(file_path).name
            report = (
                f"Had my team look at '{filename}'. Here's what they found:\n\n"
                f"{summary}\n\n"
                f"What do you want to do with it?"
            )

            self.ui.write_log(f"CTO report on {filename}:\n{summary}")

            if self.session and hasattr(self.session, 'send'):
                safe_report = report[:1000] + ("..." if len(report) > 1000 else "")
                await self.session.send(input=safe_report, end_of_turn=True)

        except Exception as e:
            self._logger.error(f"File analysis failed: {e}")

    async def receive_audio(self):
        self._logger.info("Recv started")
        out_buf, in_buf = [], []

        try:
            while True:
                self.turn_started = True
                async for response in self.session.receive():

                    if response.server_content and response.server_content.model_turn:
                        for part in response.server_content.model_turn.parts:
                            if part.inline_data:
                                if self._turn_done_event and self._turn_done_event.is_set():
                                    self._turn_done_event.clear()
                                self.audio_in_queue.put_nowait(part.inline_data.data)
                                self.ue_relay.broadcast({
                                    "event": "viseme_data",
                                    "amplitude": 0.8,
                                    "data_len": len(part.inline_data.data)
                                })

                            if part.text:
                                if not response.server_content.output_transcription:
                                    txt = clean_transcript(part.text)
                                    lower_txt = txt.lower()
                                    is_reasoning_header = (
                                        txt.startswith("**") and txt.endswith("**")
                                        and any(h in lower_txt for h in [
                                            "interpreting", "evaluating", "prioritizing",
                                            "clarifying", "assuming", "snag", " snag "
                                        ])
                                    )

                                    # Catch any internal reasoning/planning headers the model might output
                                    is_any_reasoning = (
                                        txt.startswith("**") and txt.endswith("**")
                                        and len(txt) < 80
                                    ) or (
                                        txt.startswith("[") and txt.endswith("]")
                                        and any(w in txt.lower() for w in ["thinking", "reasoning", "plan", "analy"])
                                    )

                                    if txt and not is_reasoning_header and not is_any_reasoning:
                                        out_buf.append(txt)
                                        if self.turn_started:
                                            self.ui.write_log(txt, "ai")
                                            self.turn_started = False
                                        else:
                                            self.ui.write_log(txt, "streaming")

                            if part.thought:
                                pass

                    if response.server_content:
                        sc = response.server_content

                        if getattr(sc, "interrupted", False):
                            self._logger.info("Interruption detected by server!")
                            while not self.audio_in_queue.empty():
                                try:
                                    self.audio_in_queue.get_nowait()
                                except asyncio.QueueEmpty:
                                    break
                            self.set_speaking(False)
                            if self._turn_done_event:
                                self._turn_done_event.clear()
                            out_buf = []
                            in_buf = []
                            try:
                                from actions.screen_processor import _session as vision_session
                                vision_session.abort_playback()
                            except Exception as ev:
                                self._logger.warning(f"Could not abort vision playback: {ev}")

                        if sc.output_transcription and sc.output_transcription.text:
                            txt = clean_transcript(sc.output_transcription.text)
                            if txt:
                                out_buf.append(txt)

                        if sc.input_transcription and sc.input_transcription.text:
                            txt = clean_transcript(sc.input_transcription.text)
                            if txt:
                                in_buf.append(txt)

                        if sc.turn_complete:
                            if self._turn_done_event:
                                self._turn_done_event.set()

                            full_in = " ".join(in_buf).strip()
                            if full_in:
                                self.ui.write_log(f"You: {full_in}")
                                self._last_user_text = full_in
                                self._save_chat_history(f"You: {full_in}")
                            in_buf = []

                            full_out = " ".join(out_buf).strip()
                            if full_out:
                                self.ui.write_log(f"Ananya: {full_out}")
                                self._save_chat_history(f"Ananya: {full_out}")
                            out_buf = []

                    if response.tool_call:
                        fn_responses = []
                        for fc in response.tool_call.function_calls:
                            self._logger.info(f"Tool call: {fc.name}")
                            fr = await self.tool_executor.execute(fc, ananya_instance=self)
                            fn_responses.append(fr)
                        await self.session.send_tool_response(
                            function_responses=fn_responses
                        )
        except Exception as e:
            self._logger.error(f"Recv error: {e}", exc_info=True)
            raise

    def _infer_mood_from_text(self, text: str) -> str | None:
        lower = text.lower()
        frustrated = [
            "why isn't", "not working", "broken", "fix this", "annoying", "stupid",
            "what the", "damn", "hate", "ugh", "error", "failing", "useless", "worst",
            "kadupu", "kadupethatha", "irritating", "irritate", "sothu", "kovam", "paithiyam",
            "verupethara", "verupu", "waste", "savam"
        ]
        happy = [
            "great", "awesome", "nice", "love it", "perfect", "thanks", "amazing",
            "wonderful", "fantastic", "good job", "well done", "beautiful", "excellent",
            "nandri", "super-ah", "super", "mass", "gethu", "vaazhthukkal", "magizhchi", "glad"
        ]
        urgent = [
            "quick", "hurry", "asap", "fast", "immediately", "right now", "emergency", "urgent",
            "seekiram", "seekirama", "fast-ah", "urgenta", "speed"
        ]
        thoughtful = [
            "architect", "design", "evaluate", "review", "refactor", "explain", "compare",
            "how to build", "how does", "what is the best way", "pros and cons", "tradeoff",
            "complex", "algorithm", "optimization", "contingency planning"
        ]
        exhausted = [
            "tired", "exhausted", "sleepy", "drained", "stressed", "burnout", "mudiyala",
            "tired-ah", "valikidhu", "thala vali", "thoonganum", "overwork"
        ]

        if any(w in lower for w in frustrated):
            return "frustrated"
        if any(w in lower for w in happy):
            return "happy"
        if any(w in lower for w in urgent):
            return "urgent"
        if any(w in lower for w in thoughtful):
            return "thoughtful"
        if any(w in lower for w in exhausted):
            return "exhausted"
        return None

    def on_text_command(self, text: str):
        if not text or not text.strip():
            return
        if not self._loop or not self.session:
            err_msg = "Hey, I can't do that right now — session's not active. Mind trying again?"
            self._logger.warning("Session not active for text command")
            self.ui.write_log(f"Ananya: {err_msg}")
            return

        self._logger.info(f"Text command: {text}")
        self.ui.write_log(f"You: {text}")
        self._last_user_text = text
        self._save_chat_history(f"You: {text}")

        mood = self._infer_mood_from_text(text)
        if mood:
            track_mood(mood, text[:100])

        asyncio.run_coroutine_threadsafe(
            self.session.send(input=text, end_of_turn=True),
            self._loop
        )

    def on_file_selected(self, file_path: str):
        if not self._loop or not self.session:
            self._logger.warning("Cannot send file: Session not active.")
            return

        fname = Path(file_path).name
        self._logger.info(f"File attached: {file_path}")
        self.ui.write_log(f"Ananya: Got the file — '{fname}'. Let me take a look.")
        self.ui.current_file = file_path

        asyncio.run_coroutine_threadsafe(
            self._process_file_upload(self.session, file_path),
            self._loop
        )

    async def send_text(self, text: str):
        if self.session:
            try:
                await self.session.send(text, end_of_turn=True)
            except Exception as e:
                self._logger.error(f"Failed to send text: {e}")

    async def run(self):
        while True:
            try:
                api_key = self.key_manager.get_key()
                if not api_key:
                    self._logger.error("No API key found in config/api_keys.json")
                    await asyncio.sleep(10)
                    continue

                client = genai.Client(
                    api_key=api_key,
                    http_options={"api_version": "v1beta"}
                )

                self._logger.info("Connecting...")
                self.ui.set_state("THINKING")
                self.ue_relay.broadcast({"event": "state", "value": "THINKING"})
                config = self._build_config()

                async with (
                    client.aio.live.connect(model=self.live_model, config=config) as session,
                    asyncio.TaskGroup() as tg,
                ):
                    self.session = session
                    self._loop = asyncio.get_event_loop()
                    self.audio_in_queue = asyncio.Queue()
                    self.out_queue = asyncio.Queue(maxsize=200)
                    self._turn_done_event = asyncio.Event()

                    self.audio_manager.audio_in_queue = self.audio_in_queue
                    self.audio_manager.out_queue = self.out_queue
                    self.audio_manager.set_speaking_callback = self.set_speaking

                    # Load chat history to UI
                    self._load_chat_history_to_ui()

                    self._logger.info("Connected.")

                    # Check if this is a first interaction
                    greeting = "Hey, I'm here. What's up?"
                    try:
                        history_path = get_base_dir() / "memory" / "chat_history.json"
                        if history_path.exists():
                            history_data = json.loads(history_path.read_text(encoding="utf-8"))
                            if len(history_data) < 3:
                                greeting = "Hey there! First time chatting or been a while — either way, I'm ready. What can I do for you?"
                    except Exception:
                        pass

                    self.ui.set_state("LISTENING")
                    self.ue_relay.broadcast({"event": "state", "value": "LISTENING"})
                    self.ui.write_log(f"Ananya: {greeting}")

                    tg.create_task(self.audio_manager.audio_stream(session, self.out_queue))
                    tg.create_task(self.audio_manager.listen_audio(self._loop, self.out_queue))
                    tg.create_task(self.receive_audio())
                    tg.create_task(self.audio_manager.play_audio(self.audio_in_queue, self._turn_done_event))

            except Exception as e:
                error_str = str(e)
                if hasattr(e, "exceptions"):
                    error_str += " | Sub-errors: " + ", ".join(str(se) for se in e.exceptions)

                self._logger.error(f"Session error: {error_str}")

                should_rotate = any(code in error_str for code in ["429", "limit", "1008", "401"])
                if should_rotate:
                    self._logger.info("Limit hit or Auth error. Rotating key...")
                    self.key_manager.rotate()

            self.set_speaking(False)
            self.ui.set_state("THINKING")
            self._logger.info("Connection lost. Reconnecting in 3s...")
            if self.ui:
                self.ui.write_log("Ananya: Give me a sec, reconnecting...")
            await asyncio.sleep(3)
