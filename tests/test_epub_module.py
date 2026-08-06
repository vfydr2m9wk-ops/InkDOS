from pathlib import Path
import json, shutil, subprocess, unittest
ROOT=Path(__file__).resolve().parents[1]
class EpubModuleTests(unittest.TestCase):
    def test_assets(self):
        for rel in ('apps/epub/module.json','apps/epub/index.html','apps/epub/styles.css','apps/epub/epub-parser.js','apps/epub/app.js','docs/EPUB_READER.md','EPUB.html'):
            self.assertTrue((ROOT/rel).is_file(),rel)
    def test_manifest(self):
        m=json.loads((ROOT/'apps/epub/module.json').read_text());self.assertTrue(m['enabled']);self.assertTrue(m['optional']);self.assertEqual(m['extensions'],['epub']);self.assertIn('lateral-pagination',m['capabilities']);self.assertIn('simple-images',m['capabilities'])
    def test_controls(self):
        h=(ROOT/'apps/epub/index.html').read_text()
        for marker in ('id="openBtn"','id="saveBtn"','id="docTitle"','id="tocPanel"','id="previousPage"','id="nextPage"','id="fontDecrease"','id="fontIncrease"','data-theme="paper"','data-theme="night"'):
            self.assertIn(marker,h)
        self.assertIn('id="tocPanel" class="toc-panel" hidden',h);self.assertIn('shared/vendor/jszip.min.js',h)
    def test_parser(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        script=r'''require('./apps/epub/epub-parser.js');const api=globalThis.InkDeskEpubParser;if(!api||api.version!=='0.19.4.15')process.exit(10);if(api.resolvePath('OPS/package.opf','text/ch1.xhtml')!=='OPS/text/ch1.xhtml')process.exit(11);if(api.resolvePath('OPS/text/ch1.xhtml','../images/cover.png')!=='OPS/images/cover.png')process.exit(12);const c='<container><rootfiles><rootfile full-path="OPS/package.opf"/></rootfiles></container>';if(api.parseContainer(c)!=='OPS/package.opf')process.exit(13);const opf='<package><metadata><dc:title>Sample</dc:title><dc:creator>Author</dc:creator><meta name="cover" content="cover"/></metadata><manifest><item id="cover" href="images/c.png" media-type="image/png"/><item id="c1" href="text/1.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="c1"/></spine></package>';const b=api.parsePackage(opf,'OPS/package.opf');if(b.title!=='Sample'||b.creator!=='Author'||b.sections.length!==1||b.sections[0].path!=='OPS/text/1.xhtml'||!b.cover)process.exit(14);'''
        r=subprocess.run([node,'-e',script],cwd=ROOT,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
    def test_runtime(self):
        s=(ROOT/'apps/epub/app.js').read_text()
        for marker in ('MAX_FILE_BYTES=100*1024*1024','global.JSZip.loadAsync(file)','META-INF/container.xml','sanitize(section,source)','REMOVED','resourceUrl','paginate()','touchstart','ArrowRight','InkDeskFileLifecycle.create','requestDownload(state.file,state.fileName)',"extensions:['epub']",'InkDeskEpubDebug'):
            self.assertIn(marker,s)
    def test_integration(self):
        router=(ROOT/'shared/file-router.js').read_text();reg=(ROOT/'modules/module-registry.js').read_text();home=(ROOT/'index.html').read_text();sw=(ROOT/'service-worker.js').read_text()
        self.assertIn("epub:'./apps/epub/index.html'",router);self.assertIn('"id": "epub"',reg);self.assertIn('./apps/epub/index.html',home);self.assertIn('.epub',home)
        for asset in ('./EPUB.html','./apps/epub/module.json','./apps/epub/index.html','./apps/epub/styles.css','./apps/epub/epub-parser.js','./apps/epub/app.js'):self.assertIn(repr(asset),sw)
        self.assertIn('modules-0.19.4.15',sw)
    def test_contract(self):
        m=json.loads((ROOT/'app-manifest.json').read_text());c=m['epubReaderSystem'];self.assertEqual(c['version'],'0.19.4.15');self.assertTrue(c['localProcessing']);self.assertFalse(c['contentEditing']);self.assertEqual(len(c['themes']),4);self.assertEqual(m['documentSessionSystem']['editableTitles']['epub'],'.epub');self.assertNotIn('epub',m['iconSystem']['plannedModuleIcons'])
    def test_syntax(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        for rel in ('apps/epub/epub-parser.js','apps/epub/app.js','shared/file-router.js','modules/module-registry.js'):
            r=subprocess.run([node,'--check',str(ROOT/rel)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
    def test_package_script(self):
        p=json.loads((ROOT/'package.json').read_text());self.assertEqual(p['scripts']['test:epub'],'python3 -m unittest tests.test_epub_module')
if __name__=='__main__':unittest.main()
