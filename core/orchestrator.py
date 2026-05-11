import asyncio
import mimetypes
from typing import Dict, Any, Optional
from pathlib import Path
from google.genai import types
from core.model_registry import get_registry
from core.logging import LOG


class Orchestrator:
    def __init__(self, ui=None):
        self.ui = ui
        self.registry = get_registry()
        self._logger = LOG.get_logger("Orchestrator")

    async def delegate_task(self, role: str, prompt: str, file_path: Optional[str] = None) -> str:
        model_name = self.registry.get_model_name(role)
        log_msg = f"Delegating to {role} ({model_name})..."
        self._logger.info(log_msg)
        if self.ui:
            self.ui.write_log(f"SYS: {log_msg}")

        contents = self._build_contents(role, prompt, file_path)
        if not contents:
            return "Error: Internal logic failure - no content generated for delegation."

        return await self._execute_with_retry(role, prompt, file_path, contents, model_name)

    def _build_contents(self, role: str, prompt: str, file_path: Optional[str] = None):
        if not file_path:
            return [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]

        p = Path(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        fname_lower = p.name.lower()

        doc_type = None
        if mime_type == "application/pdf" or fname_lower.endswith(".pdf"):
            doc_type = "pdf"
        elif (mime_type and "officedocument.wordprocessingml" in mime_type) or fname_lower.endswith(".docx"):
            doc_type = "docx"

        if doc_type:
            return self._build_doc_contents(p, doc_type, prompt)

        if mime_type and mime_type.startswith("image/"):
            with open(file_path, "rb") as f:
                data = f.read()
            return [types.Content(role="user", parts=[
                types.Part.from_bytes(data=data, mime_type=mime_type),
                types.Part.from_text(text=prompt)
            ])]

        try:
            text_content = p.read_text(encoding="utf-8", errors="ignore")
            full_prompt = f"FILE: {p.name}\n---\n{text_content}\n---\n{prompt}"
            return [types.Content(role="user", parts=[types.Part.from_text(text=full_prompt)])]
        except Exception as e:
            self._logger.error(f"Could not read {p.name} as text: {e}")
            return [types.Content(role="user", parts=[types.Part.from_text(text=f"File: {p.name} attached.\n\nTask: {prompt}")])]

    def _build_doc_contents(self, path: Path, doc_type: str, prompt: str):
        text_content = ""
        try:
            if doc_type == "docx":
                from actions.file_processor import extract_docx_content
                text_content = extract_docx_content(str(path))
            elif doc_type == "pdf":
                import pdfplumber
                with pdfplumber.open(str(path)) as pdf:
                    text_content = "\n".join(page.extract_text() or "" for page in pdf.pages)

            if text_content.strip():
                SAFE_LIMIT = 100000
                truncated = len(text_content) > SAFE_LIMIT
                if truncated:
                    text_content = text_content[:SAFE_LIMIT]

                full_prompt = (
                    f"I have provided the content of '{path.name}' below.\n\n"
                    f"--- START OF FILE CONTENT ---\n{text_content}\n--- END OF FILE CONTENT ---\n"
                    f"{'(Note: Document was truncated for size)' if truncated else ''}\n\n"
                    f"INSTRUCTION: {prompt}\n\n"
                    f"PLEASE PROVIDE ONLY YOUR FINAL OUTPUT. DO NOT INCLUDE REASONING HEADERS OR METADATA."
                )
                return [types.Content(role="user", parts=[types.Part.from_text(text=full_prompt)])]
            else:
                self._logger.warning(f"No text extracted from {path.name}")
        except Exception as e:
            self._logger.error(f"Local extraction failed for {path.name}: {e}")

        return [types.Content(role="user", parts=[types.Part.from_text(
            text=f"The user attached a document named '{path.name}', but it appears empty or unreadable.\n\nTask: {prompt}"
        )])]

    async def _execute_with_retry(self, role: str, prompt: str, file_path: Optional[str],
                                   contents: list, model_name: str) -> str:
        retries = 3
        for attempt in range(retries):
            try:
                result = await self._execute_single(contents, model_name, role)
                self._logger.info(f"OK: {role} completed task.")
                if self.ui:
                    self.ui.write_log(f"SYS: {role} completed task.")
                return result
            except Exception as e:
                error_str = str(e)
                is_retryable = any(code in error_str for code in
                                   ["500", "429", "INTERNAL", "RESOURCE_EXHAUSTED", "connection"])

                if is_retryable:
                    self.registry.mark_key_failed(self.registry.last_used_key)

                if is_retryable and attempt < retries - 1:
                    wait_time = 3 * (attempt + 1)
                    self._logger.warning(f"{role} failed ({error_str[:60]}). Retrying in {wait_time}s...")
                    if self.ui:
                        self.ui.write_log(f"SYS: {role} busy. Rotating key...")
                    await asyncio.sleep(wait_time)
                    continue

                if ("token count exceeds" in error_str or "429" in error_str
                        or "RESOURCE_EXHAUSTED" in error_str) and role != "ANALYST":
                    self._logger.info("Token/quota limit. Retrying with ANALYST (1M context)...")
                    return await self.delegate_task("ANALYST", prompt, file_path)

                if role == "CTO" and any(w in prompt.lower() for w in ["error", "bug", "fix", "code", "install"]):
                    return await self._self_heal(role, prompt, file_path)

                if attempt == retries - 1:
                    local_result = await self._try_local_fallback(prompt)
                    if local_result:
                        return local_result

                err_msg = f"{role} failed after {attempt + 1} attempts: {error_str[:120]}"
                self._logger.error(err_msg)
                if self.ui:
                    self.ui.write_log(f"ERR: {err_msg}")
                return f"Task delegation failed: {error_str[:200]}"

        return "Task delegation failed after multiple retries."

    async def _execute_single(self, contents: list, model_name: str, role: str) -> str:
        parts_text = "".join(p.text for c in contents for p in c.parts if p.text)
        estimated_tokens = self._estimate_tokens(parts_text)

        current_model = model_name
        if estimated_tokens > 200000 and role == "CTO":
            self._logger.warning(f"File too large ({estimated_tokens} tokens). Switching to ANALYST...")
            current_model = self.registry.get_model_name("ANALYST")

        if current_model.startswith("nvidia/"):
            return await self._execute_nvidia(current_model, parts_text)

        client = self.registry.get_client()
        if not client:
            return "Error: No API keys available."

        response = client.models.generate_content(
            model=current_model,
            contents=contents
        )
        return response.text

    async def _execute_nvidia(self, model_name: str, parts_text: str) -> str:
        nv_client = self.registry.get_nvidia_client()
        if not nv_client:
            return "Error: NVIDIA API Key not configured."

        actual_model = model_name[7:]
        response = await asyncio.to_thread(
            nv_client.chat.completions.create,
            model=actual_model,
            messages=[{"role": "user", "content": parts_text}],
            temperature=0.2,
            top_p=0.7,
            max_tokens=4096
        )
        result = response.choices[0].message.content

        if "deepseek-r1" in actual_model:
            import re
            if "<think>" in result:
                if "</think>" in result:
                    think_match = re.search(r"<think>(.*?)</think>", result, re.DOTALL)
                    if think_match:
                        thinking_content = think_match.group(1).strip()
                        self._logger.info(f"DeepSeek-R1 Thinking Process:\n{thinking_content}")
                        if self.ui:
                            self.ui.write_log(f"REASONER THINKING:\n{thinking_content}", "plain")
                    result = re.sub(r"<think>.*?</think>", "", result, flags=re.DOTALL).strip()
                else:
                    think_match = re.search(r"<think>(.*)", result, re.DOTALL)
                    if think_match:
                        thinking_content = think_match.group(1).strip()
                        self._logger.info(f"DeepSeek-R1 Thinking Process (Incomplete):\n{thinking_content}")
                        if self.ui:
                            self.ui.write_log(f"REASONER THINKING:\n{thinking_content}", "plain")
                    result = re.sub(r"<think>.*", "", result, flags=re.DOTALL).strip()

        return result

    async def _self_heal(self, role: str, prompt: str, file_path: Optional[str]) -> str:
        self._logger.info("CTO snagged. Invoking REASONER (DeepSeek-R1) for advanced technical self-healing...")
        if self.ui:
            self.ui.write_log("SYS: CTO snagged. Launching REASONER (DeepSeek-R1) self-healing loop...")
        
        reasoner_prompt = (
            f"The primary CTO agent encountered a failure while trying to complete this task:\n"
            f"'{prompt}'\n\n"
            f"Please perform a deep thinking diagnostic of the problem, identify any logical or technical bugs, "
            f"and provide a complete, pristine, and corrected technical solution."
        )
        try:
            # Check if nvidia client and key is available before invoking
            nv_key = self.registry.key_manager.get_nvidia_key()
            if not nv_key:
                raise ValueError("NVIDIA key not configured.")

            reasoner_context = await self.delegate_task("REASONER", reasoner_prompt, file_path)
            self._logger.info("Self-healing: Successfully obtained REASONER diagnostic solution.")
            if self.ui:
                self.ui.write_log("SYS: REASONER diagnostic solution retrieved. Finalizing fix with CTO...")
            
            healed_prompt = (
                f"{prompt}\n\n"
                f"[REASONER DIAGNOSTIC & FIX]:\n{reasoner_context}\n\n"
                f"Please synthesize the final corrected output using the above expert solution."
            )
            return await self.delegate_task("CTO", healed_prompt, file_path)
        except Exception as e:
            self._logger.warning(f"REASONER self-healing skipped or failed ({e}). Using standard RESEARCHER fallback...")
            research_prompt = (
                f"The CTO is struggling with this task: '{prompt[:200]}'. "
                f"Please search for the latest documentation or community fixes."
            )
            research_context = await self.delegate_task("RESEARCHER", research_prompt)
            healed_prompt = f"{prompt}\n\n[RESEARCHER FEEDBACK]:\n{research_context}"
            return await self.delegate_task("CTO", healed_prompt, file_path)

    async def _try_local_fallback(self, prompt: str) -> Optional[str]:
        self._logger.info("Attempting local fallback via Ollama...")
        try:
            import requests
            preferred_models = [
                "qwen2.5-coder:3b", "qwen2.5-coder", "llama3.2:3b",
                "llama3.2", "qwen2.5:3b", "qwen2.5", "gemma2:2b"
            ]
            selected = "qwen2.5-coder:3b"

            try:
                tags_resp = requests.get("http://localhost:11434/api/tags", timeout=3)
                if tags_resp.status_code == 200:
                    installed = [m.get("name") for m in tags_resp.json().get("models", [])]
                    for pm in preferred_models:
                        if pm in installed or any(pm.split(":")[0] in im for im in installed):
                            selected = pm
                            break
            except Exception:
                pass

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": selected, "prompt": prompt, "stream": False},
                timeout=30
            )
            if response.status_code == 200:
                self._logger.info(f"Local fallback succeeded with '{selected}'")
                return f"[OFFLINE MODE - {selected}]: {response.json().get('response', '')}"
        except Exception as e:
            self._logger.warning(f"Local fallback unavailable: {e}")
        return None

    def _estimate_tokens(self, text: str) -> int:
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            return len(text) // 4

    async def analyze_file_automatically(self, file_path: str) -> str:
        prompt = (
            "Analyze this file in depth. If it's code, review it for bugs and optimization. "
            "If it's data, provide key insights. If it's a document, summarize the main points. "
            "Return a concise 'CTO Executive Summary' for the CEO."
        )
        cto_summary = await self.delegate_task("CTO", prompt, file_path)
        
        # Fire-and-forget task to asynchronously extract technical projects and persist to memory
        asyncio.create_task(self._extract_and_save_project_info(file_path))
        
        return cto_summary

    async def _extract_and_save_project_info(self, file_path: str):
        self._logger.info(f"Starting automatic background project metadata extraction for: {file_path}")
        prompt = (
            "You are analyzing a user-uploaded file or document. "
            "Identify any technical, academic, or professional projects described in this file. "
            "For each distinct project found, extract: "
            "1. A concise identifier/name (1-3 words, all lowercase with underscores, e.g., 'luxestay_system' or 'acpf_framework'). "
            "2. A concise high-impact description (1-2 sentences capturing description, tech stack, and goals). "
            "Return your findings strictly as a valid JSON object of key-value pairs where keys are the concise "
            "identifiers and values are the concise descriptions. Do not output any markdown formatting, backticks, "
            "headers, or conversational text. Example format: "
            '{\n  "luxestay_system": "Hotel Management System built using React, NestJS, and PostgreSQL for reservations."\n}'
        )
        try:
            result = await self.delegate_task("ANALYST", prompt, file_path)
            if not result or "Task delegation failed" in result:
                self._logger.warning("Project metadata extraction skipped: ANALYST delegation failed or empty response.")
                return

            import re
            import json
            
            clean_text = result.strip()
            # Handle markdown fence blocks
            if clean_text.startswith("```"):
                clean_text = re.sub(r"^```(?:json)?\n?", "", clean_text, flags=re.IGNORECASE)
                clean_text = re.sub(r"\n?```$", "", clean_text)
                clean_text = clean_text.strip()

            try:
                data = json.loads(clean_text)
            except Exception:
                # Fallback regex search for outer-most braces
                match = re.search(r"(\{.*\})", clean_text, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group(1))
                    except Exception:
                        data = {}
                else:
                    data = {}

            if isinstance(data, dict) and data:
                from memory.memory_manager import remember
                for k, v in data.items():
                    if k and v:
                        remember(k, str(v), category="projects")
                self._logger.info(f"Successfully extracted and remembered projects: {list(data.keys())}")
                if self.ui:
                    self.ui.write_log(f"SYS: Asynchronously extracted project characteristics: {', '.join(data.keys())}")
            else:
                self._logger.info("No projects identified or successfully parsed in document.")
        except Exception as e:
            self._logger.error(f"Error extracting and saving project information: {e}", exc_info=True)
