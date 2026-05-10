import asyncio
from typing import Dict, Any, Optional
from core.model_registry import get_registry
from google.genai import types

class Orchestrator:
    def __init__(self, ui=None):
        self.ui = ui
        self.registry = get_registry()

    async def delegate_task(self, role: str, prompt: str, file_path: Optional[str] = None) -> str:
        """Delegates a task to a specialized model role."""
        model_name = self.registry.get_model_name(role)
        client = self.registry.get_client()
        
        log_msg = f"[Orchestrator] 🚀 Delegating to {role} ({model_name})..."
        print(log_msg)
        if self.ui:
            self.ui.write_log(f"SYS: {log_msg}")

        contents = []
        
        # If file is provided, add it to contents
        if file_path:
            import mimetypes
            from pathlib import Path
            p = Path(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            if mime_type and mime_type.startswith("image/"):
                with open(file_path, "rb") as f:
                    data = f.read()
                contents.append(types.Content(role="user", parts=[
                    types.Part.from_bytes(data=data, mime_type=mime_type),
                    types.Part.from_text(text=prompt)
                ]))
            else:
                # For non-image files, read as text if possible
                try:
                    text_content = p.read_text(encoding="utf-8", errors="ignore")
                    full_prompt = f"FILE: {p.name}\n---\n{text_content}\n---\n{prompt}"
                    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=full_prompt)]))
                except Exception as e:
                    return f"Error reading file: {e}"
        else:
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )
            result = response.text
            
            completion_msg = f"[Orchestrator] ✅ {role} completed task."
            print(completion_msg)
            if self.ui:
                self.ui.write_log(f"SYS: {completion_msg}")
                
            return result
        except Exception as e:
            err_msg = f"[Orchestrator] ❌ {role} failed: {e}"
            print(err_msg)
            if self.ui:
                self.ui.write_log(f"ERR: {err_msg}")
            return str(e)

    async def analyze_file_automatically(self, file_path: str) -> str:
        """Automatically called when a file is uploaded. Routes to CTO for analysis."""
        prompt = (
            "Analyze this file in depth. If it's code, review it for bugs and optimization. "
            "If it's data, provide key insights. If it's a document, summarize the main points. "
            "Return a concise 'CTO Executive Summary' for the CEO."
        )
        return await self.delegate_task("CTO", prompt, file_path)
