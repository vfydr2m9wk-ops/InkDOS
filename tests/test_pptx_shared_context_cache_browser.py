#!/usr/bin/env python3
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8799
BASE = f"http://127.0.0.1:{PORT}"
MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local test server did not start")


def main() -> None:
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    if browser_name not in {"chromium", "firefox", "webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={browser_name}")

    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    errors: list[str] = []
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={"width": 1360, "height": 900})
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.on(
                "console",
                lambda msg: errors.append(f"console.error: {msg.text}")
                if msg.type == "error"
                else None,
            )
            page.goto(BASE + "/apps/presentations/", wait_until="load")
            page.wait_for_function(
                "() => !!globalThis.InkDOS2Presentations?.PptxWriter && "
                "!!globalThis.InkDOS2Presentations?.PptxOpenController && "
                "!!globalThis.__inkdosPresentations"
            )

            result = page.evaluate(
                r"""async ({mime}) => {
                  const NS=globalThis.InkDOS2Presentations,M=NS.PresentationModel;
                  const app=globalThis.__inkdosPresentations;

                  const makeSession=(count,prefix)=>{
                    const s=new NS.PresentationSession();s.resetNew();
                    const setTitle=(slide,text)=>{
                      const o=slide.objects[0];
                      o.text=text;
                      o.paragraphs=M.normalizeParagraphs(null,text,o);
                    };
                    setTitle(s.slides[0],prefix+' 1');
                    for(let i=2;i<=count;i++){s.addSlide();setTitle(s.currentSlide,prefix+' '+i)}
                    s.setCurrentByIndex(0);
                    return s;
                  };

                  const source=makeSession(44,'Cache slide');
                  const bytes=await NS.PptxWriter.build(source);
                  const realLoad=JSZip.loadAsync;
                  let loadSeq=0;
                  const decoderTextReads={};
                  JSZip.loadAsync=async function(input,options){
                    const id=++loadSeq;
                    const zip=await realLoad.call(this,input,options);
                    if(id===2){
                      const realFile=zip.file.bind(zip);
                      zip.file=function(path){
                        const obj=realFile(path);
                        if(!obj||typeof path!=='string')return obj;
                        return new Proxy(obj,{
                          get(target,prop){
                            if(prop!=='async')return Reflect.get(target,prop,target);
                            return async function(type,...args){
                              if(type==='text')decoderTextReads[path]=(decoderTextReads[path]||0)+1;
                              return target.async(type,...args);
                            };
                          }
                        });
                      };
                    }
                    return zip;
                  };
                  let decoded;
                  try{
                    decoded=await NS.PptxOpenController.decodePptx(bytes,'cache-44.pptx');
                  }finally{
                    JSZip.loadAsync=realLoad;
                  }

                  const basicTitles=decoded.slides.map(s=>s.objects.filter(o=>o.type==='text').map(o=>o.text).join(' | '));
                  const countMatches=re=>Object.entries(decoderTextReads).filter(([p])=>re.test(p)).reduce((n,[,v])=>n+v,0);

                  const inheritanceSource=makeSession(3,'Inheritance source');
                  const base=await NS.PptxWriter.build(inheritanceSource);
                  const zip=await JSZip.loadAsync(base);
                  const themePath='ppt/theme/theme1.xml';
                  let theme=await zip.file(themePath).async('text');
                  theme=theme
                    .replace('DF542C','123ABC')
                    .replace('4F81BD','456DEF')
                    .replace('Aptos Display','Cache Major')
                    .replace('Aptos','Cache Minor');
                  zip.file(themePath,theme);

                  const titleLayout=`<p:sp><p:nvSpPr><p:cNvPr id="8" name="Cached Title"/><p:cNvSpPr/><p:nvPr><p:ph type="title" idx="1"/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm><a:off x="1000000" y="700000"/><a:ext cx="9000000" cy="1400000"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr sz="3200"><a:solidFill><a:schemeClr val="accent1"/></a:solidFill><a:latin typeface="+mj-lt"/></a:rPr><a:t>Layout title</a:t></a:r></a:p></p:txBody></p:sp>`;
                  let layout=await zip.file('ppt/slideLayouts/slideLayout1.xml').async('text');
                  layout=layout.replace('</p:spTree>',titleLayout+'</p:spTree>');
                  zip.file('ppt/slideLayouts/slideLayout1.xml',layout);

                  const bodyMaster=`<p:sp><p:nvSpPr><p:cNvPr id="9" name="Cached Body"/><p:cNvSpPr/><p:nvPr><p:ph type="body" idx="2"/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm><a:off x="1200000" y="3000000"/><a:ext cx="8500000" cy="2200000"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr sz="2200"><a:solidFill><a:schemeClr val="accent2"/></a:solidFill><a:latin typeface="+mn-lt"/></a:rPr><a:t>Master body</a:t></a:r></a:p></p:txBody></p:sp>`;
                  let master=await zip.file('ppt/slideMasters/slideMaster1.xml').async('text');
                  master=master.replace('</p:spTree>',bodyMaster+'</p:spTree>');
                  zip.file('ppt/slideMasters/slideMaster1.xml',master);

                  const group=`<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>`;
                  const placeholder=(id,type,idx,text)=>`<p:sp><p:nvSpPr><p:cNvPr id="${id}" name="${type}"/><p:cNvSpPr/><p:nvPr><p:ph type="${type}" idx="${idx}"/></p:nvPr></p:nvSpPr><p:spPr><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>${text}</a:t></a:r></a:p></p:txBody></p:sp>`;
                  const backgrounds=['112233','223344','334455'];
                  for(let i=1;i<=3;i++){
                    const path=`ppt/slides/slide${i}.xml`;
                    let xml=await zip.file(path).async('text');
                    const tree=`<p:spTree>${group}${placeholder(2,'title',1,'Title '+i)}${placeholder(3,'body',2,'Body '+i)}</p:spTree>`;
                    xml=xml.replace(/<p:spTree>[\s\S]*?<\/p:spTree>/,tree);
                    xml=xml.replace('<p:cSld>','<p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="'+backgrounds[i-1]+'"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>');
                    zip.file(path,xml);
                  }
                  const inheritanceBytes=await zip.generateAsync({type:'uint8array',compression:'DEFLATE',compressionOptions:{level:6}});
                  const inherited=await NS.PptxOpenController.decodePptx(inheritanceBytes,'inheritance-cache.pptx');

                  const semantic=inherited.slides.map(slide=>{
                    const title=slide.objects.find(o=>o.placeholder==='title');
                    const body=slide.objects.find(o=>o.placeholder==='body');
                    return {
                      width:slide.widthEmu,height:slide.heightEmu,background:slide.background,
                      title:title&&{text:title.text,x:title.x,y:title.y,w:title.w,h:title.h,fontSizePt:title.fontSizePt,fontFamily:title.fontFamily,color:title.color},
                      body:body&&{text:body.text,x:body.x,y:body.y,w:body.w,h:body.h,fontSizePt:body.fontSizePt,fontFamily:body.fontFamily,color:body.color}
                    };
                  });

                  const opened=await app.open(new File([inheritanceBytes],'inheritance-cache.pptx',{type:mime}));
                  const exported=await NS.PptxWriter.build(app.session);
                  const reopened=await NS.PptxOpenController.decodePptx(exported,'cache-roundtrip.pptx');
                  const reopenedTexts=reopened.slides.map(s=>s.objects.filter(o=>o.type==='text').map(o=>o.text));

                  return {
                    cache:{
                      loads:loadSeq,
                      layoutXml:decoderTextReads['ppt/slideLayouts/slideLayout1.xml']||0,
                      layoutRels:decoderTextReads['ppt/slideLayouts/_rels/slideLayout1.xml.rels']||0,
                      masterXml:decoderTextReads['ppt/slideMasters/slideMaster1.xml']||0,
                      masterRels:decoderTextReads['ppt/slideMasters/_rels/slideMaster1.xml.rels']||0,
                      themeXml:decoderTextReads['ppt/theme/theme1.xml']||0,
                      slideXml:countMatches(/^ppt\/slides\/slide\d+\.xml$/i),
                      slideRels:countMatches(/^ppt\/slides\/_rels\/slide\d+\.xml\.rels$/i)
                    },
                    basic:{slides:decoded.slides.length,titles:basicTitles},
                    semantic,
                    opened:!!opened,
                    reopened:{slides:reopened.slides.length,texts:reopenedTexts}
                  };
                }""",
                {"mime": MIME},
            )
            browser.close()

        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})

        cache = result["cache"]
        assert result["basic"]["slides"] == 44, result
        assert len(set(result["basic"]["titles"])) == 44, result
        assert cache["loads"] == 2, cache
        assert cache["layoutXml"] == 1, cache
        assert cache["layoutRels"] == 1, cache
        assert cache["masterXml"] == 1, cache
        assert cache["masterRels"] == 1, cache
        assert cache["themeXml"] == 1, cache
        assert cache["slideXml"] == 44, cache
        assert cache["slideRels"] == 44, cache

        semantic = result["semantic"]
        assert len(semantic) == 3, semantic
        assert [x["background"].lower() for x in semantic] == ["#112233", "#223344", "#334455"], semantic
        for index, slide in enumerate(semantic, 1):
            assert slide["width"] == 12192000 and slide["height"] == 6858000, slide
            title = slide["title"]
            body = slide["body"]
            assert title and title["text"] == f"Title {index}", slide
            assert body and body["text"] == f"Body {index}", slide
            assert title["x"] == 1000000 and title["y"] == 700000, title
            assert body["x"] == 1200000 and body["y"] == 3000000, body
            assert abs(title["fontSizePt"] - 32) < 0.01, title
            assert abs(body["fontSizePt"] - 22) < 0.01, body
            assert title["fontFamily"] == "Cache Major", title
            assert body["fontFamily"] == "Cache Minor", body
            assert title["color"].lower() == "#123abc", title
            assert body["color"].lower() == "#456def", body

        assert result["opened"] is True, result
        assert result["reopened"]["slides"] == 3, result
        for index, texts in enumerate(result["reopened"]["texts"], 1):
            joined = "\n".join(texts)
            assert f"Title {index}" in joined and f"Body {index}" in joined, result

        print(
            f"PPTX shared-context cache regression passed on {browser_name}: "
            "shared layout/master/theme processed once; slide-local semantics preserved."
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
