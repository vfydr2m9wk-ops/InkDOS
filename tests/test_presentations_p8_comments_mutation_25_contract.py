from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PKG=(ROOT/'apps/presentations/io/ppt-p2-package.js').read_text()
TOOLS=(ROOT/'apps/presentations/ui/ppt-p2-tools.js').read_text()
SAVE=(ROOT/'apps/presentations/io/save-controller.js').read_text()

def test_classic_comment_writer_is_policy_gated_and_package_complete():
    assert 'async function commentMutationPolicy' in PKG
    assert 'Modern/threaded PowerPoint comments are preserve-only.' in PKG
    assert 'ensureCommentAuthorsPart' in PKG
    assert "ensureRelationship(zip,slidePart,'/comments',commentPart)" in PKG
    assert 'COMMENTS_TYPE' in PKG and 'COMMENT_AUTHORS_TYPE' in PKG
    assert 'applyClassicComments(session,out,receipt)' in PKG

def test_comment_toolbar_uses_command_history_and_preserves_existing_inventory():
    assert "commands.register('slide.comment.add',addComment" in TOOLS
    assert "history.transact('Add comment'" in TOOLS
    assert "slide.comments.push" in TOOLS
    assert 'slide.commentsEdited=true' in TOOLS
    assert "commentPolicy=await P2.commentMutationPolicy(session.sourceBytes,parts)" in TOOLS

def test_confirmed_save_clears_comment_edit_marker():
    assert 'slide.commentsEdited=false' in SAVE
