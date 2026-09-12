from pathlib import Path
import json
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RealDeviceDocumentsSheetsReviewTests(unittest.TestCase):
    def _read(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_documents_and_spreadsheets_web_share_send_only_the_file(self):
        """A file-only Share payload must not expose a companion text item to Apple hosts."""
        for app in ("documents", "spreadsheets"):
            source = self._read(f"apps/{app}/io/file-delivery.js")
            self.assertIn(
                "navigator.share({files:[file]})",
                source,
                f"{app}: Web Share must hand off the file without a title/text companion payload",
            )
            self.assertNotIn(
                "navigator.share({files:[file],title:",
                source,
                f"{app}: a title beside files can materialize as an extra text item on Apple hosts",
            )

    def test_mobile_sum_shorthand_is_committed_as_a_real_formula(self):
        """The exact real-device entry =sum:A1;A2 is normalized before WorkbookEditor receives it."""
        formula_bar = ROOT / "apps/spreadsheets/ui/formula-bar.js"
        script = r"""
const fs = require('fs');
const vm = require('vm');
const path = process.argv[1];
class Target {
  constructor(){ this.value=''; this.handlers={}; }
  addEventListener(type, fn){ this.handlers[type]=fn; }
  fire(type, event){ this.handlers[type]?.(event); }
  focus(){}
  setSelectionRange(){}
}
globalThis.LocalXLSX = {
  encodeRef(r,c){ return String.fromCharCode(65+c)+(r+1); },
  decodeRef(ref){ return {r:Number(ref.slice(1))-1,c:ref.charCodeAt(0)-65}; }
};
vm.runInThisContext(fs.readFileSync(path,'utf8'), {filename:path});
const nameBox=new Target(), input=new Target(), functions=new Target();
const sheet={cells:new Map()};
const session={book:{loaded:true},activeSheet(){return sheet}};
const selection={active:{r:0,c:1},range:{r1:0,c1:1,r2:0,c2:1},select(){}};
let committed=null;
const editor={commitValue(value){committed=value}};
globalThis.InkDOS2Spreadsheets.FormulaBar.create({nameBox,input,functions,session,selection,editor});
input.value='=sum:A1;A2';
input.fire('keydown',{key:'Enter',preventDefault(){}});
process.stdout.write(JSON.stringify({committed}));
"""
        proc = subprocess.run(
            ["node", "-e", script, str(formula_bar)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        result = json.loads(proc.stdout)
        self.assertEqual(result["committed"], "=SUM(A1,A2)")


if __name__ == "__main__":
    unittest.main()
