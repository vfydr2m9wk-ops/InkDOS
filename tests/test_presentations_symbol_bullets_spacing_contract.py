"""Regression contract: symbol-font bullets, master style inheritance, picture backgrounds,
PPTX arrow connectors and reduced line spacing in Presentations."""
from pathlib import Path
import json
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "presentations"
PPT = (APP / "io" / "ppt-legacy-reader.js").read_text(encoding="utf-8")
PPTX = (APP / "io" / "pptx-open-controller.js").read_text(encoding="utf-8")
SURFACE = (APP / "view" / "slide-surface.js").read_text(encoding="utf-8")


def block(source: str, start: str, end: str) -> str:
    i = source.index(start)
    return source[i : source.index(end, i)]


def run_node(script: str):
    return json.loads(subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True).stdout)


@unittest.skipUnless(shutil.which("node"), "node is required for the behavioural probes")
class SymbolBulletBehaviourTests(unittest.TestCase):
    CASES = [["Wingdings", "Ø"], ["Wingdings 2", ""], ["wingdings 3", ""], ["Symbol", ""],
             ["Wingdings", ""], ["Arial", "•"], [None, ""], ["Arial", "–"]]
    EXPECTED = ["➢", "●", "▸", "•", "•", "•", "•", "–"]

    def check(self, source: str):
        start = source.index("const SYMBOL_BULLETS=")
        helper = source[start : source.index("\n", source.index("function symbolBullet(", start))]
        out = run_node(helper + f"\nprocess.stdout.write(JSON.stringify({json.dumps(self.CASES)}.map(([f,c])=>symbolBullet(f,c))))")
        self.assertEqual(out, self.EXPECTED)

    def test_legacy_ppt_maps_symbol_bullets(self):
        self.check(PPT)
        self.assertIn("out.bulletFontRef=take(2)", PPT)
        self.assertIn("symbolBullet(bfRef!=null?fontTable[bfRef]:null", PPT)

    def test_pptx_maps_symbol_bullets_through_bu_font(self):
        self.check(PPTX)
        self.assertIn("child(x,'buFont')", PPTX)


@unittest.skipUnless(shutil.which("node"), "node is required for the behavioural probes")
class MasterStyleInheritanceTests(unittest.TestCase):
    def test_center_title_inherits_title_style_and_keeps_own_values(self):
        fn = block(PPT, "function masterStyleFor(", "\n")
        probe = fn + """
let ACTIVE_MASTER_STYLES=new Map([[0,{color:'#ffffff',fontSizePt:46,levels:[{pf:{align:'center'},cf:{colorRef:{index:0}}}]}],
  [6,{color:null,fontSizePt:null,levels:[{pf:{align:null},cf:{colorRef:null}}]}],
  [1,{color:'#595959',levels:[{pf:{},cf:{}}]}],[5,{color:'#123456',levels:[]}]]);
const t=masterStyleFor(6),b=masterStyleFor(5),o=masterStyleFor(0),n=masterStyleFor(7);
process.stdout.write(JSON.stringify([t.color,t.fontSizePt,t.levels[0].pf.align,t.levels[0].cf.colorRef.index,b.color,o.color,n.color]))"""
        self.assertEqual(run_node(probe), ["#ffffff", 46, "center", 0, "#123456", "#ffffff", "#595959"])


class StaticContracts(unittest.TestCase):
    def test_legacy_picture_background_follows_master(self):
        helper = block(PPT, "function backgroundImageFromContainer", "\nfunction backgroundColorFromContainer")
        self.assertIn("ft===2||ft===3", helper)
        self.assertIn("0x0186", helper)
        self.assertIn("backgroundImageFromContainer(master,pictures)", PPT)
        self.assertIn("slide.backgroundImage&&map.has(slide.backgroundImage)", PPT)

    def test_pptx_straight_connectors_are_lines_with_arrowheads(self):
        self.assertIn("shapeName(node)==='straightConnector1'?'line'", PPTX)
        line = block(PPTX, "function lineInfo(", "\nfunction ownAttr(")
        self.assertIn("child(ln,'headEnd')", line)
        self.assertIn("child(ln,'tailEnd')", line)
        self.assertIn("t==='arrow'?'open':'triangle'", line)

    def test_reduced_line_spacing_is_not_clamped_by_paragraph_min_height(self):
        self.assertIn("if(parseFloat(line.style.lineHeight)<lineFont)line.style.minHeight=line.style.lineHeight;", SURFACE)


if __name__ == "__main__":
    unittest.main()
