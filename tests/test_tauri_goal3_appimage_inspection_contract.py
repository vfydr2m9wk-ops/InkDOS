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
    physical_desktop_count_expectation = (
        'test "$(find "$appdir/squashfs-root" -name \'*.desktop\' -type f | wc -l | tr -d \' \')" = "1"'
    )
    assert obsolete_desktop_expectation not in workflow, (
        "AppImage inspection must not require six workspace .desktop entries"
    )
    assert obsolete_icon_expectation not in workflow, (
        "AppImage inspection must not require six workspace icons"
    )
    assert physical_desktop_count_expectation not in workflow, (
        "AppImage identity must not be inferred from the physical .desktop file count; "
        "linuxdeploy can expose the same canonical desktop identity at multiple paths"
    )

    assert "AppImage must expose one canonical desktop identity" in workflow
    assert "AppImage canonical desktop entries must share one basename" in workflow
    assert "AppImage must not contain auxiliary inkdos-* workspace desktop entries" in workflow
    assert "AppImage must not contain the package-manager workspace icon tree" in workflow

    # Package-manager formats must inspect the actual freedesktop icon paths
    # declared by tauri.conf.json. Five canonical workspace icons are SVGs in
    # the scalable tree; Presentations is the existing PNG in 256x256.
    obsolete_all_png_check = 'test -f "$root/usr/share/icons/hicolor/256x256/apps/inkdos-$workspace.png"'
    assert obsolete_all_png_check not in workflow, (
        "DEB/RPM inspection must not pretend all workspace icons are 256x256 PNG files"
    )

    scalable_workspaces = ("documents", "spreadsheets", "pdf", "epub", "txt")
    for workspace in scalable_workspaces:
        expected = f'test -f "$root/usr/share/icons/hicolor/scalable/apps/inkdos-{workspace}.svg"'
        assert workflow.count(expected) == 2, (
            f"DEB and RPM inspection must verify the configured scalable SVG for {workspace}"
        )

    presentations = 'test -f "$root/usr/share/icons/hicolor/256x256/apps/inkdos-presentations.png"'
    assert workflow.count(presentations) == 2, (
        "DEB and RPM inspection must verify the configured Presentations PNG"
    )

    obsolete_package_icon_root = 'find "$root/usr/share/inkdos/workspace-icons"'
    assert obsolete_package_icon_root not in workflow, (
        "DEB/RPM inspection must not require the removed /usr/share/inkdos/workspace-icons tree"
    )


if __name__ == "__main__":
    main()
