#!/usr/bin/env python3
"""Rebuild assets/tokens.json and assets/components.json from an installed Optics package.

Usage:
    python3 scripts/regenerate_data.py <path-to-node_modules/@rolemodel/optics>

Run it from this skill's folder after an Optics upgrade, then review the diff. Tokens that match no
category are reported on stderr and filed under "uncategorized" so a new token family isn't lost.
"""

import json
import re
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

TOKEN_DEFINITION = re.compile(r"(--op-[a-z0-9-]+)\s*:")
COMMENT = re.compile(r"/\*.*?\*/", re.S)
RULE_SELECTOR = re.compile(r"([^{};]+)\{")
CLASS = re.compile(r"\.([a-z][a-z0-9_-]*)")
ATTRIBUTE = re.compile(r"\[data-[a-z-]+(?:=['\"][^'\"]*['\"])?\]")

COLOR_SCALES = ["primary", "neutral", "alerts-warning", "alerts-danger", "alerts-info", "alerts-notice"]
SEMANTIC_COLORS = ["--op-color-background", "--op-color-on-background", "--op-color-on-background-alt",
                   "--op-color-border"]
BORDER_SHADOWS = ["none", "all", "top", "right", "bottom", "left", "x", "y"]


def ordered_unique(items):
    return list(dict.fromkeys(items))


def categorize(token):
    """Return the path inside optics_design_tokens that a token belongs to."""
    if token in ("--op-color-white", "--op-color-black"):
        return ["colors", "basic"]
    if token in SEMANTIC_COLORS:
        return ["colors", "semantic"]
    for scale in COLOR_SCALES:
        prefix = f"--op-color-{scale}-"
        if token.startswith(prefix):
            path = ["colors", *scale.split("-")]
            rest = token[len(prefix):]
            if rest in ("h", "s", "l", "original"):
                return path + ["base"]
            return path + (["on_scale"] if rest.startswith("on-") else ["scale"])

    simple = [
        ("--op-font-family", ["typography", "font_family"]),
        ("--op-font-weight-", ["typography", "font_weight"]),
        ("--op-font-", ["typography", "font_size"]),
        ("--op-line-height-", ["typography", "line_height"]),
        ("--op-letter-spacing-", ["typography", "letter_spacing"]),
        ("--op-space-", ["spacing", "scale"]),
        ("--op-gap", ["spacing", "gap"]),
        ("--op-size-unit", ["base_unit"]),
        ("--op-radius-", ["borders", "radius"]),
        ("--op-border-width", ["borders", "width"]),
        ("--op-shadow-", ["shadows"]),
        ("--op-opacity-", ["opacity"]),
        ("--op-breakpoint-", ["breakpoints"]),
        ("--op-input-height-", ["inputs", "heights"]),
        ("--op-input-", ["inputs", "focus"]),
        ("--op-transition-", ["transitions"]),
        ("--op-animation-", ["animations"]),
        ("--op-z-index-", ["z_index"]),
        ("--op-encoded-images-", ["encoded_images"]),
    ]
    for prefix, path in simple:
        if token.startswith(prefix):
            return path
    if token.startswith("--op-border-") and token[len("--op-border-"):] in BORDER_SHADOWS:
        return ["borders", "shadow"]
    if token.startswith("--op-") and token.endswith("-z-index"):
        return ["z_index"]
    return None


def insert(tree, path, token):
    node = tree
    for key in path[:-1]:
        node = node.setdefault(key, {})
    node.setdefault(path[-1], []).append(token)


def count(node):
    return len(node) if isinstance(node, list) else sum(count(child) for child in node.values())


def seed(previous):
    """Empty copy of the previous tree, so categories keep their order and the diff shows only real changes."""
    return {key: seed(child) for key, child in previous.items()} if isinstance(previous, dict) else []


def prune(tree, previous):
    """Drop empty categories and keep each list's previous order, with new tokens at the end."""
    result = {}
    for key, child in tree.items():
        if not count(child):
            continue
        before = previous.get(key, {} if isinstance(child, dict) else [])
        if isinstance(child, dict):
            result[key] = prune(child, before)
        else:
            position = {token: index for index, token in enumerate(before)}
            result[key] = sorted(child, key=lambda token: position.get(token, len(position)))
    return result


def build_tokens(css_dir, version, previous):
    css = COMMENT.sub("", (css_dir / "optics.css").read_text())
    tokens = ordered_unique(TOKEN_DEFINITION.findall(css))
    previous_meta = previous.pop("meta")

    tree = seed(previous)
    for token in tokens:
        path = categorize(token)
        if path is None:
            print(f"uncategorized token: {token}", file=sys.stderr)
            path = ["uncategorized"]
        insert(tree, path, token)
    tree = prune(tree, previous)

    meta = {
        "description": "Complete list of Optics Design System CSS custom properties (tokens)",
        "optics_version": version,
        "total_tokens": len(tokens),
        "categories": {name: count(node) for name, node in tree.items()},
        "color_scale_notes": previous_meta.get("color_scale_notes", {}),
    }
    return {"optics_design_tokens": {"meta": meta, **tree}}


def build_components(css_dir, version):
    source_files = []
    class_counts = {}
    attributes = {}
    for import_name in re.findall(r"@import '([^']+)'", (css_dir / "components" / "index.css").read_text()):
        source_files.append(f"node_modules/@rolemodel/optics/dist/css/components/{import_name}")
        key = Path(import_name).stem.replace("-", "_")
        css = COMMENT.sub("", (css_dir / "components" / import_name).read_text())
        selectors = [s for s in RULE_SELECTOR.findall(css) if not s.strip().startswith("@")]
        class_counts[key] = {}
        attributes[key] = set()
        for selector in selectors:
            for name in CLASS.findall(selector):
                class_counts[key][name] = class_counts[key].get(name, 0) + 1
            attributes[key].update(ATTRIBUTE.findall(selector))

    components = {}
    for key, counts in class_counts.items():
        groups = {"base": set(), "modifiers": set(), "elements": set(), "attributes": attributes[key]}
        for name in counts:
            # A file also styles other components' classes in context (e.g. `.icon` inside a segmented
            # control). Leave those to the file named after their block.
            block = re.split(r"__|--", name)[0].replace("-", "_")
            if block != key and block in class_counts:
                continue
            # An element modifier (`block__element--modifier`) is listed under both.
            if "--" in name:
                groups["modifiers"].add(name)
            if "__" in name:
                groups["elements"].add(name)
            if "--" not in name and "__" not in name:
                groups["base"].add(name)
        components[key] = {group: sorted(names) for group, names in groups.items() if names}

    counts = {key: sum(len(names) for names in groups.values()) for key, groups in components.items()}
    meta = {
        "description": "Complete list of Optics Design System CSS component classes. This does not include "
                       "app specific overrides or app components.",
        "optics_version": version,
        "source_files": sorted(source_files),
        "total_components": len(components),
        "total_classes": sum(counts.values()),
        "components": dict(sorted(counts.items())),
        "notes": {
            "base_classes": "Primary component classes that define the core component styling",
            "modifiers": "Modifier classes that change the appearance or behavior of components",
            "elements": "Sub-element classes that style specific parts within a component",
            "attributes": "Data attributes used for component functionality (like tooltips)",
        },
    }
    return {"optics_component_classes": {"meta": meta, **dict(sorted(components.items()))}}


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    package = Path(sys.argv[1])
    version = json.loads((package / "package.json").read_text())["version"]
    css_dir = package / "dist" / "css"

    tokens_path = ASSETS / "tokens.json"
    previous = json.loads(tokens_path.read_text())["optics_design_tokens"]

    tokens_path.write_text(json.dumps(build_tokens(css_dir, version, previous), indent=2) + "\n")
    (ASSETS / "components.json").write_text(json.dumps(build_components(css_dir, version), indent=2) + "\n")
    print(f"Wrote Optics {version} data to {ASSETS}")


if __name__ == "__main__":
    main()
