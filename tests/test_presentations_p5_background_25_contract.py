from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_p5_background_ui_and_model():
 s=(ROOT/'apps/presentations/ui/ppt-p1-tools.js').read_text()
 assert "pptP1Background" in s and "backgroundEdited=true" in s and "applyBackground" in s
def test_p5_background_control_survives_build_for_sync():
 s=(ROOT/'apps/presentations/ui/ppt-p1-tools.js').read_text()
 assert "imageInput=null,colorControls={},backgroundCtl=null" in s
 assert "backgroundCtl=colorControl('pptP1Background'" in s
 assert "const backgroundCtl=colorControl('pptP1Background'" not in s
def test_p5_background_roundtrip_writer():
 s=(ROOT/'apps/presentations/io/ppt-p2-package.js').read_text()
 assert "writeSlideBackground" in s and "slide.backgroundEdited===true" in s and "a:srgbClr" in s
