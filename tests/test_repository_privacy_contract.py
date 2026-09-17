#!/usr/bin/env python3
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

FORBIDDEN_USER_FILE_SUFFIXES = {
    ".doc", ".docx", ".rtf", ".xls", ".xlsx", ".ppt", ".pptx",
    ".pdf", ".epub", ".pages", ".numbers", ".key", ".heic", ".heif",
    ".mov", ".mp4", ".m4v", ".zip", ".7z", ".rar",
}

HISTORICAL_USER_CONTENT_SUFFIXES = {
    ".doc", ".docx", ".rtf", ".xls", ".xlsx", ".ppt", ".pptx",
    ".pdf", ".epub", ".pages", ".numbers", ".key", ".heic", ".heif",
    ".mov", ".mp4", ".m4v",
}

# These historical namespaces are documented as generated/synthetic regression fixtures.
# They are grandfathered for history classification only; the current tree still rejects
# all committed user-document/media/archive formats above.
HISTORICAL_SYNTHETIC_PREFIXES = (
    "tests/fixtures/",
    "tests/compatibility-fixtures/",
)

ARCHIVE_SUFFIXES = {".zip", ".7z", ".rar"}
QA_ARCHIVE_TOKENS = {
    "qa", "private", "lab", "fixture", "fixtures", "sample", "samples",
    "screenshot", "screenshots", "testdata", "test-data",
}

FORBIDDEN_PATH_PARTS = {
    ".private", "private", "qa-private", "private-qa", "local-qa",
    "fixtures-private", "qa-screenshots", "screenshots",
}

TEXT_SUFFIXES = {
    ".css", ".html", ".js", ".json", ".md", ".py", ".txt", ".yml", ".yaml",
}

FORBIDDEN_PUBLIC_ATTACHMENT_HOSTS = (
    "private-user-images.githubusercontent.com",
    "user-images.githubusercontent.com",
    "github.com/user-attachments/assets/",
)

SECRET_PATTERNS = (
    re.compile(r"\bghp_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)

REQUIRED_IGNORE_RULES = (
    ".private/", "private-qa/", "qa-screenshots/", "playwright-report/",
    "*.doc", "*.docx", "*.rtf", "*.xls", "*.xlsx", "*.ppt", "*.pptx",
    "*.pdf", "*.epub", "*.pages", "*.numbers", "*.key", "*.heic", "*.heif",
    "*.mov", "*.mp4", "*.m4v", "*.zip", "*.7z", "*.rar", ".env", ".env.*",
)

REQUIRED_SECURITY_FRAGMENTS = (
    "synthetic",
    "Do not attach real user documents",
    "screenshots",
    "medical",
    "educational",
    "GitHub Actions artifacts",
)

REQUIRED_BUG_TEMPLATE_FRAGMENTS = (
    "Do not attach real user files",
    "synthetic",
    "personal, medical, or educational data",
)


def tracked_paths() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=ROOT
    ).decode("utf-8")
    return [ROOT / item for item in output.split("\0") if item]


def historical_privacy_counts() -> tuple[int, int, int, int]:
    """Return category counts only; never disclose historical paths in public CI."""
    output = subprocess.check_output(
        ["git", "rev-list", "--objects", "--all"], cwd=ROOT, text=True
    )
    unclassified_content_hits: set[str] = set()
    known_synthetic_hits: set[str] = set()
    private_path_hits: set[str] = set()
    qa_archive_hits: set[str] = set()

    for line in output.splitlines():
        if " " not in line:
            continue
        object_id, raw_path = line.split(" ", 1)
        normalized_path = raw_path.replace("\\", "/")
        path = Path(normalized_path)
        suffix = path.suffix.lower()
        lower_parts = {part.lower() for part in path.parts}
        stem_tokens = {
            token for token in re.split(r"[^a-z0-9-]+", path.stem.lower()) if token
        }

        if suffix in HISTORICAL_USER_CONTENT_SUFFIXES:
            if normalized_path.startswith(HISTORICAL_SYNTHETIC_PREFIXES):
                known_synthetic_hits.add(object_id)
            else:
                unclassified_content_hits.add(object_id)
        if lower_parts & FORBIDDEN_PATH_PARTS:
            private_path_hits.add(object_id)
        if suffix in ARCHIVE_SUFFIXES and stem_tokens & QA_ARCHIVE_TOKENS:
            qa_archive_hits.add(object_id)

    return (
        len(unclassified_content_hits),
        len(private_path_hits),
        len(qa_archive_hits),
        len(known_synthetic_hits),
    )


def main() -> None:
    tracked = tracked_paths()

    forbidden_files = [
        path.relative_to(ROOT).as_posix()
        for path in tracked
        if path.suffix.lower() in FORBIDDEN_USER_FILE_SUFFIXES
    ]
    assert not forbidden_files, (
        "User-document/media/archive formats must not be tracked; use synthetic in-memory fixtures instead: "
        f"{forbidden_files}"
    )

    forbidden_paths = []
    for path in tracked:
        rel = path.relative_to(ROOT)
        parts = {part.lower() for part in rel.parts[:-1]}
        if parts & FORBIDDEN_PATH_PARTS:
            forbidden_paths.append(rel.as_posix())
    assert not forbidden_paths, f"Private QA paths must not be tracked: {forbidden_paths}"

    attachment_hits = []
    secret_hits = []
    for path in tracked:
        if path.resolve() == SELF or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if any(host in text for host in FORBIDDEN_PUBLIC_ATTACHMENT_HOSTS):
            attachment_hits.append(rel)
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            secret_hits.append(rel)

    assert not attachment_hits, (
        "Repository text must not embed GitHub user-upload attachment URLs: "
        f"{attachment_hits}"
    )
    assert not secret_hits, f"Credential-like material found in tracked text: {secret_hits}"

    (
        history_unclassified,
        history_private_paths,
        history_qa_archives,
        history_known_synthetic,
    ) = historical_privacy_counts()
    assert (history_unclassified, history_private_paths, history_qa_archives) == (0, 0, 0), (
        "Historical privacy candidates detected without disclosing filenames: "
        f"unclassified user-content objects={history_unclassified}, "
        f"private-path objects={history_private_paths}, QA-archive objects={history_qa_archives}. "
        "History rewrite requires separate approval."
    )

    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    missing_ignore = [rule for rule in REQUIRED_IGNORE_RULES if rule not in ignore]
    assert not missing_ignore, f".gitignore is missing privacy rules: {missing_ignore}"

    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    missing_security = [item for item in REQUIRED_SECURITY_FRAGMENTS if item not in security]
    assert not missing_security, f"SECURITY.md is missing privacy guidance: {missing_security}"

    bug_template = (ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").read_text(encoding="utf-8")
    missing_template = [item for item in REQUIRED_BUG_TEMPLATE_FRAGMENTS if item not in bug_template]
    assert not missing_template, f"Bug template is missing privacy guidance: {missing_template}"

    print(
        "Repository privacy contract passed "
        f"(historical synthetic fixture objects recognized: {history_known_synthetic})."
    )


if __name__ == "__main__":
    main()
