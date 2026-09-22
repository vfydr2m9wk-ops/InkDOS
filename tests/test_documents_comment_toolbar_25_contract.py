#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/"apps"/"documents"
def r(p): return p.read_text(encoding="utf-8")
def test_comment_toolbar_contract():
    html=r(DOC/"index.html"); app=r(DOC/"app.js"); controller=r(DOC/"ui"/"command-controller.js"); d2=r(DOC/"ui"/"d2-tools.js")
    assert 'id="commentBtn"' in html and 'aria-label="Comment"' in html
    assert "commandRegistry.register('insert.comment',()=>d2.openComments())" in app
    assert "execute('insert.comment')" in controller and "editor.rememberSelection()" in controller
    assert 'function openComments()' in d2 and "$('d2CommentText')?.focus()" in d2
    assert 'addComment' in d2 and 'data-d2-comment-id' in d2
if __name__=='__main__': test_comment_toolbar_contract(); print('Documents 2.5 direct Comment toolbar contract passed.')
