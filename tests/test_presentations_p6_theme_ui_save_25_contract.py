from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_p6_theme_ui_and_command_are_policy_gated():
 s=(ROOT/'apps/presentations/ui/ppt-p2-tools.js').read_text()
 assert "presentation.theme.set" in s and "themePolicy.writable" in s and "pptP2ThemeBtn" in s
 assert "session.themePatch" in s and "session.themeEdited=true" in s
def test_p6_theme_save_pipeline_uses_safe_package_writer():
 s=(ROOT/'apps/presentations/io/ppt-p2-package.js').read_text()
 assert "session?.themeEdited" in s and "applyThemeMutation(out,parts,session.themePatch)" in s
