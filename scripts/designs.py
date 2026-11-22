"""Shared inventory of printable designs; artwork and body geometry live in OpenSCAD."""

VARIANTS = {
    "git-branch": ("git_branch", "01-git-branch", "Git branch"),
    "invertocat": ("octocat", "02-octocat", "Invertocat"),
    "hatsu": ("hatsu", "03-hatsu", "Hatsu contribution"),
    "chun": ("chun", "04-chun", "Red Chun and red cat without circle"),
    "haku": ("haku", "05-haku", "Haku - supplied face icon, no text"),
    "iisou": ("iisou", "06-iisou", "Iisou - mirrored three-quarter green Ducky with peacock tail"),
}
ADDITIONS = ("haku", "iisou")
PROJECTS = {
    "all-three": ["git-branch", "invertocat", "hatsu"],
    **{key: [key] for key in VARIANTS},
}


def parts_for(variant):
    parts = ["black_back", "white_body", "inlay"]
    if variant == "hatsu":
        parts.append("light_inlay")
    return parts


PRINTED_PART_COUNT = sum(len(parts_for(value[0])) for value in VARIANTS.values())
