from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "goal3-native-checkpoint.yml"


def main() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    # AppImage must remain a single portable InkDOS application identity.
    # DEB/RPM retain the six installed workspace launchers, but the AppImage
    # inspection must explicitly reject those auxiliary identities instead of
    # requiring them to be embedded.
    obsolete_desktop_expectation = (
        'test "$(find "$appdir/squashfs-root/usr/share/applications" '
        "-name 'inkdos-*.desktop' -type f | wc -l | tr -d ' ')\" = \"6\""
    )
    obsolete_icon_expectation = (
        'test "$(find "$appdir/squashfs-root/usr/share/inkdos/workspace-icons" '
        "-type f | wc -l | tr -d ' ')\" = \"6\""
    )
    assert obsolete_desktop_expectation not in workflow, (
        "AppImage inspection must not require six workspace .desktop entries"
    )
    assert obsolete_icon_expectation not in workflow, (
        "AppImage inspection must not require six workspace icons"
    )

    assert "AppImage must expose exactly one canonical desktop identity" in workflow
    assert "AppImage must not contain auxiliary inkdos-* workspace desktop entries" in workflow
    assert "AppImage must not contain the package-manager workspace icon tree" in workflow


if __name__ == "__main__":
    main()
