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


@unittest.skipUnless(shutil.which("node"), "node is required for the behavioural probes")
class PptxColourTransformTests(unittest.TestCase):
    def test_lum_mod_off_shade_and_tint_apply_to_solid_colours(self):
        start = PPTX.index("function colorFrom(")
        src = PPTX[start : PPTX.index("\n", PPTX.index("function colorTransforms(", start))]
        lum = PPTX[PPTX.index("function lumAdjust(") :]
        lum = lum[: lum.index("\n")]
        probe = r"""
const kids=n=>n.kids||[],first=(n,name)=>{for(const k of kids(n)){if(k.localName===name)return k;const f=first(k,name);if(f)return f}return null},child=(n,name)=>kids(n).find(k=>k.localName===name)||null,attr=(n,k,d=null)=>n&&n.a&&n.a[k]!=null?n.a[k]:d,num=(v,d)=>Number.isFinite(Number(v))?Number(v):d,hex=v=>/^[0-9a-f]{6}$/i.test(v||'')?'#'+v.toUpperCase():null;
const el=(localName,a={},k=[])=>({localName,a,kids:k});
""" + lum + "\n" + src + r"""
const theme={colors:{tx2:'#C0504D'}};
const pink=el('solidFill',{},[el('schemeClr',{val:'tx2'},[el('lumMod',{val:'20000'}),el('lumOff',{val:'80000'})])]);
const shade=el('solidFill',{},[el('srgbClr',{val:'808080'},[el('shade',{val:'50000'})])]);
const tint=el('solidFill',{},[el('srgbClr',{val:'000000'},[el('tint',{val:'50000'})])]);
const plain=el('solidFill',{},[el('srgbClr',{val:'123456'})]);
process.stdout.write(JSON.stringify([colorFrom(pink,theme),colorFrom(shade,theme),colorFrom(tint,theme),colorFrom(plain,theme)]))"""
        out = run_node(probe)
        self.assertEqual(out[1:], ["#404040", "#808080", "#123456"])
        r, g, b = (int(out[0][i : i + 2], 16) for i in (1, 3, 5))
        self.assertTrue(r > 230 and g > 205 and b > 205 and r > g, out[0])


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

    def test_bullet_colour_and_size_flow_from_readers_to_renderer(self):
        self.assertIn("child(x,'buClr')", PPTX)
        self.assertIn("child(x,'buSzPct')", PPTX)
        self.assertIn("out.bulletColorRef=", PPT)
        self.assertIn("bulletSizePct:bsz", PPT)
        model = (APP / "engine" / "presentation-session.js").read_text(encoding="utf-8")
        self.assertIn("bulletColor:p.bulletColor", model)
        self.assertIn("bulletSizePct:Math.max(25,Math.min(400", model)
        self.assertIn("bullet.style.color=bc", SURFACE)

    def test_legacy_master_shapes_fonts_and_names(self):
        self.assertIn("skipPlaceholders:true}).filter(o=>o.type==='image'||o.type==='shape'||(o.type==='text'&&String(o.text||'').trim()))", PPT)
        self.assertIn("function footerObjects(", PPT)
        self.assertIn("props[0x00c0]?.complex&&includeText?officeComplex(optRec):null", PPT)  # WordArt text
        self.assertIn("x.type===0x0bc3", PPT)
        self.assertIn("(mcf.fontRef!=null&&fontTable[mcf.fontRef])", PPT)
        self.assertIn("utf16(record.data.subarray(0,64)).split('\\u0000')[0]", PPT)

    def test_missing_fonts_fall_back_by_design_class(self):
        self.assertIn("SERIF_FACES=/^(constantia|georgia|times", SURFACE)
        self.assertIn("MONO_FACES.test(n)?'\"Courier New\", monospace':WIDE_SERIF_FACES.test(n)?'Georgia,", SURFACE)
        self.assertIn("SERIF_FACES.test(n)?'\"Times New Roman\"", SURFACE)

    def test_pptx_percentage_paragraph_spacing_becomes_points(self):
        self.assertIn("spaceBeforePt:paraSpacePt(before,runs),spaceAfterPt:paraSpacePt(after,runs)", PPTX)
        helper = block(PPTX, "function paraSpacePt(", "\n")
        self.assertIn("(sp.rawRatio??sp.ratio??0)*size*1.2", helper)

    def test_group_members_are_never_the_legacy_background_shape(self):
        helper = block(PPT, "function groupChildSp(", "\n")
        self.assertIn("u32(sp.data,4)&0x2", helper)
        for fn in ("backgroundImageFromContainer", "backgroundGradientFromContainer", "backgroundColorFromContainer"):
            self.assertIn("groupChildSp(own)", block(PPT, f"function {fn}(", "\nfunction "))
        color = block(PPT, "function backgroundColorFromContainer(", "\nfunction ")
        self.assertIn("u32(shape.data,4)&0x400", color)  # the flagged background shape comes first
        self.assertIn("if(ft===1&&props[0x0183])", color)  # fillBackColor only for pattern fills
        self.assertIn("function followMasterBackground(slide)", PPT)

    def test_pptx_texture_fill_with_gradient_overlay_uses_the_overlay(self):
        helper = block(PPTX, "function fillEffects(", "const sf=child(spPr,'solidFill')")
        self.assertIn("child(spPr,'blipFill')?first(child(spPr,'effectLst'),'fillOverlay')", helper)
        self.assertIn("(ov&&child(ov,'gradFill'))", helper)

    def test_gradient_stops_keep_their_own_transparency(self):
        self.assertIn("...stopAlpha(gs)", PPTX)
        model = (APP / "engine" / "presentation-session.js").read_text(encoding="utf-8")
        self.assertIn("...(x.opacity!=null&&x.opacity<1?{opacity:", model)
        self.assertIn("(o.fillOpacity??1)*(st.opacity??1)", SURFACE)

    def test_shape_picture_fill_is_drawn_as_a_texture(self):
        self.assertIn("fillImage=connector?null:await textureFill(zip,spPr,rels,g)", PPTX)
        self.assertIn("function texturePattern(", SURFACE)
        self.assertIn("n.style.mixBlendMode='multiply'", SURFACE)

    def test_text_geometry_presets_and_unknown_preset_fallback(self):
        for name in ("ellipse:", "roundRect:", "cloudCallout:", "leftArrowCallout:", "downArrowCallout:", "snipRoundRect:"):
            self.assertIn("\n " + name + "(W,H)=>", SURFACE)
        self.assertIn("if((cust||(prst!=='rect'&&prst!=='line'))&&(fill||line)&&!ph)obj.geometry", PPTX)
        self.assertIn("else if(!/Brace$/.test(o.shapeType||'')){add('path',{d:P([[0,0],[W,0],[W,H],[0,H]]),fill:F", SURFACE)

    def test_no_wrap_keeps_explicit_breaks_and_long_words_wrap(self):
        self.assertIn("if(o.wrap==='none')line.style.whiteSpace='pre';", SURFACE)
        self.assertIn("else if(o.richSource)content.style.overflowWrap='break-word';", SURFACE)

    def test_vertical_text_flow_is_read_and_rendered(self):
        self.assertIn("function textDir(v,fallback)", PPTX)
        self.assertIn("const TEXT_FLOW={1:'vert',2:'vert270',3:'wordArtVert',5:'wordArtVert'}", PPT)
        self.assertIn("content.style.writingMode=o.textDirection==='wordArtVert'?'vertical-lr':'vertical-rl'", SURFACE)

    def test_legacy_ppt_reads_live_records_and_outline_text(self):
        live = block(PPT, "function liveRecords(", "\nfunction masterLookup(")
        for needle in ("RT.UserEditAtom", "RT.PersistDirectory", "h&0xfffff", "h>>>20", "if(!map.has(id+k))", "(r.opt>>>4)===inst"):
            self.assertIn(needle, live)
        self.assertIn("slidesRaw=live?.slides?.length?live.slides:", PPT)
        self.assertIn("mainMaster=master&&master.type===RT.Slide?", PPT)
        self.assertIn("textbox=outlineTextbox(container,own.find(r=>r.type===ES.ClientTextbox))", PPT)
        self.assertIn("function outlineTexts(list)", PPT)

    def test_legacy_ppt_dual_storage_and_password_message(self):
        self.assertIn("function pickDocumentStream(cfb)", PPT)
        self.assertIn("streams(name){", PPT)
        self.assertIn("This .ppt is password-protected", PPT)

    def test_pptx_slide_list_ignores_section_ids(self):
        self.assertIn("ids=kids(child(pd.documentElement,'sldIdLst'),'sldId')", PPTX)

    def test_reduced_line_spacing_is_not_clamped_by_paragraph_min_height(self):
        self.assertIn("if(parseFloat(line.style.lineHeight)<lineFont)line.style.minHeight=line.style.lineHeight;", SURFACE)


if __name__ == "__main__":
    unittest.main()
