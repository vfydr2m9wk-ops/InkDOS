from pathlib import Path
R=Path(__file__).resolve().parents[1]
def txt(p): return (R/p).read_text(encoding='utf-8')
def test_p8_package_inventory_is_relationship_driven_and_read_only():
    s=txt('apps/presentations/io/ppt-p2-package.js')
    assert "relatedPart(zip,'ppt/presentation.xml','/commentAuthors')" in s
    assert "relatedPart(zip,slidePart,'/comments')" in s
    assert "comments.push({authorId" in s
    assert "return {transitions,notes,themes,comments,commentAuthorsPart:authorInfo.part}" in s
def test_p8_hydrates_comments_without_marking_edits():
    s=txt('apps/presentations/ui/ppt-p2-tools.js')
    assert "slide.comments=Array.isArray(metadata.comments" in s
    assert "slide.commentsPart=metadata.comments?.[index]?.part||null" in s
    assert "slide.commentsEdited=false" in s
def test_p8_writer_not_enabled_until_authors_relationship_policy_exists():
    s=txt('apps/presentations/io/ppt-p2-package.js')
    assert 'applyCommentsMutation' not in s
