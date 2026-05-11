from unittest.mock import MagicMock, patch
from core.orchestrator import Orchestrator


class TestOrchestrator:
    def setup_method(self):
        self.mock_ui = MagicMock()
        self.mock_registry = MagicMock()
        self.mock_registry.get_model_name.return_value = "gemini-2.5-flash"
        self.mock_registry.get_client.return_value = MagicMock()
        self.mock_registry.mark_key_failed = MagicMock()

        with patch("core.orchestrator.get_registry", return_value=self.mock_registry):
            self.orchestrator = Orchestrator(ui=self.mock_ui)

    def test_init(self):
        assert self.orchestrator is not None
        assert self.orchestrator.ui is not None

    def test_estimate_tokens(self):
        text = "Hello, world!"
        tokens = self.orchestrator._estimate_tokens(text)
        assert tokens > 0

    def test_estimate_tokens_empty(self):
        tokens = self.orchestrator._estimate_tokens("")
        assert tokens == 0

    def test_build_contents_no_file(self):
        contents = self.orchestrator._build_contents("CTO", "test prompt", None)
        assert len(contents) == 1
        assert contents[0].parts[0].text == "test prompt"

    def test_build_contents_with_text_file(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("file content", encoding="utf-8")
        contents = self.orchestrator._build_contents("CTO", "analyze", str(test_file))
        assert len(contents) == 1
        assert "file content" in contents[0].parts[0].text

    def test_build_contents_with_image(self, tmp_path):
        test_img = tmp_path / "test.png"
        test_img.write_bytes(b"fake-png-data")

        with patch("mimetypes.guess_type", return_value=("image/png", None)):
            contents = self.orchestrator._build_contents("CTO", "describe", str(test_img))
            assert len(contents) == 1
            assert any(p.inline_data for p in contents[0].parts)
            assert any(p.text for p in contents[0].parts if p.text)

    def test_execute_single_no_client(self):
        self.mock_registry.get_client.return_value = None
        import asyncio
        result = asyncio.run(self.orchestrator._execute_single(
            [], "gemini-2.5-flash", "CTO"
        ))
        assert "No API keys available" in result

    @patch("core.orchestrator.get_registry")
    def test_self_heal(self, mock_get_registry):
        mock_get_registry.return_value = self.mock_registry
        import asyncio
        with patch.object(self.orchestrator, 'delegate_task') as mock_delegate:
            mock_delegate.side_effect = [
                "research results",
                "fixed code after research"
            ]
            result = asyncio.run(self.orchestrator._self_heal(
                "CTO", "fix this code bug", None
            ))
            assert mock_delegate.call_count == 2
            assert result == "fixed code after research"
            second_call_prompt = mock_delegate.call_args_list[1][0][1]
            assert "DIAGNOSTIC" in second_call_prompt
