from pathlib import Path

frontend = Path("/app/.venv/lib/python3.14/site-packages/langflow/frontend")
assets = frontend / "assets"

bundles = []
for candidate in assets.glob("index-*.js"):
    text = candidate.read_text(encoding="utf-8")
    if "Welcome to Langflow" in text:
        bundles.append((candidate, text))

if len(bundles) != 1:
    raise RuntimeError(
        f"Expected exactly one Langflow welcome bundle, found {len(bundles)}"
    )

bundle, text = bundles[0]

replacements = {
    "Welcome to Langflow": "Welcome to Algomotive Workflow Studio",
    "Your new favorite way to ship Agents":
        "Design, orchestrate, and govern enterprise AI workflows",
    "Create first flow": "Create first workflow",
    "logo_dark-DEVbuISE.png": "algomotive-mark.svg",
    "logo_light-CIlityAH.png": "algomotive-mark.svg",
}

for old, new in replacements.items():
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one occurrence of {old!r}, found {count}"
        )
    text = text.replace(old, new, 1)

assistant_label_old = "Langflow Assistant"
assistant_label_new = "AlgoFlow Assistant"
assistant_label_count = text.count(assistant_label_old)

if assistant_label_count != 4:
    raise RuntimeError(
        "Expected exactly 4 Langflow Assistant labels, "
        f"found {assistant_label_count}"
    )

text = text.replace(
    assistant_label_old,
    assistant_label_new,
)

if text.count(assistant_label_new) != 4:
    raise RuntimeError(
        "Expected exactly 4 AlgoFlow Assistant labels after replacement"
    )

bundle.write_text(text, encoding="utf-8")

expected_counts = {
    "Welcome to Algomotive Workflow Studio": 1,
    "Design, orchestrate, and govern enterprise AI workflows": 1,
    "Create first workflow": 1,
    "algomotive-mark.svg": 2,
}

for expected, expected_count in expected_counts.items():
    actual_count = text.count(expected)
    if actual_count != expected_count:
        raise RuntimeError(
            f"Expected {expected_count} occurrence(s) of {expected!r}, "
            f"found {actual_count}"
        )

print(f"Patched Langflow frontend bundle: {bundle.name}")

# Give the customized bundle a new deterministic filename so browsers and
# reverse proxies cannot reuse the immutable upstream bundle from cache.
branded_bundle = assets / "index-algomotive-workflow-studio.js"
if branded_bundle.exists():
    branded_bundle.unlink()

bundle.rename(branded_bundle)

index = frontend / "index.html"
index_text = index.read_text(encoding="utf-8")

old_favicon = (
    chr(60)
    + 'link rel="icon" href="./favicon.ico" /'
    + chr(62)
)
new_favicon = (
    chr(60)
    + 'link rel="icon" type="image/png" '
      'href="./algomotive-favicon-v1.png" /'
    + chr(62)
)

favicon_count = index_text.count(old_favicon)
if favicon_count != 1:
    raise RuntimeError(
        f"Expected exactly one original favicon element, found {favicon_count}"
    )

index_text = index_text.replace(
    old_favicon,
    new_favicon,
    1,
)

old_reference = f"./assets/{bundle.name}"
new_reference = f"./assets/{branded_bundle.name}"

if index_text.count(old_reference) != 1:
    raise RuntimeError(
        f"Expected exactly one HTML reference to {old_reference!r}, "
        f"found {index_text.count(old_reference)}"
    )

index.write_text(
    index_text.replace(old_reference, new_reference, 1),
    encoding="utf-8",
)

if new_reference not in index.read_text(encoding="utf-8"):
    raise RuntimeError("Cache-busted branded bundle was not linked from index.html")


controls_reference = (
    chr(60)
    + 'script src="./assets/algomotive-workspace-shell-v12.js"'
    + chr(62)
    + chr(60)
    + "/script"
    + chr(62)
)

index_text = index.read_text(encoding="utf-8")
if controls_reference not in index_text:
    if "</body>" not in index_text:
        raise RuntimeError("Expected closing body tag was not found")
    index.write_text(
        index_text.replace("</body>", f"  {controls_reference}\n  </body>", 1),
        encoding="utf-8",
    )

if controls_reference not in index.read_text(encoding="utf-8"):
    raise RuntimeError("Algomotive workspace controls were not linked")

loading_style = (
    chr(60)
    + "style"
    + chr(62)
    + "#algomotive-initial-loader{position:fixed;inset:0;z-index:2147483647;"
      "display:flex;align-items:center;justify-content:center;background:#fff}"
      "#algomotive-initial-loader img{width:76px;height:76px;object-fit:contain}"
    + chr(60)
    + "/style"
    + chr(62)
)

loading_markup = (
    chr(60)
    + 'div id="algomotive-initial-loader" aria-label="Loading Algomotive Workflow Studio"'
    + chr(62)
    + chr(60)
    + 'img src="./assets/algomotive-mark.svg" alt="Algomotive"'
    + chr(62)
    + chr(60)
    + "/div"
    + chr(62)
)

loading_script = (
    chr(60)
    + "script"
    + chr(62)
    + "(function(){"
      "var started=Date.now();"
      "var timer=window.setInterval(function(){"
      "var overlay=document.getElementById('algomotive-initial-loader');"
      "if(!overlay){window.clearInterval(timer);return;}"
      "var loadingVisible=Array.from(document.querySelectorAll('body *')).some(function(element){"
      "return element.textContent&&element.children.length===0&&element.textContent.trim()==='Loading...';"
      "});"
      "var appReady=document.querySelector('[data-testid],main,[role=main]');"
      "var minimumElapsed=Date.now()-started>700;"
      "var maximumElapsed=Date.now()-started>15000;"
      "if(maximumElapsed||(minimumElapsed&&!loadingVisible&&appReady)){"
      "overlay.style.opacity='0';"
      "window.setTimeout(function(){"
      "if(overlay&&overlay.parentNode){overlay.parentNode.removeChild(overlay);}"
      "},180);"
      "window.clearInterval(timer);"
      "}"
      "},100);"
      "})();"
    + chr(60)
    + "/script"
    + chr(62)
)

index_text = index.read_text(encoding="utf-8")

if "algomotive-initial-loader" not in index_text:
    import re

    if "</head>" not in index_text:
        raise RuntimeError("Expected closing head boundary was not found")

    body_match = re.search(r"<body(?:\s[^>]*)?>", index_text)
    if body_match is None:
        raise RuntimeError("Expected opening body element was not found")

    index_text = index_text.replace(
        "</head>",
        loading_style + chr(10) + "</head>",
        1,
    )

    body_tag = body_match.group(0)
    index_text = index_text.replace(
        body_tag,
        body_tag + chr(10) + loading_markup + chr(10) + loading_script,
        1,
    )

    index.write_text(index_text, encoding="utf-8")

final_index_text = index.read_text(encoding="utf-8")
if final_index_text.count("algomotive-initial-loader") < 2:
    raise RuntimeError("Algomotive initial loading identity was not applied")

print(f"Cache-busted Langflow bundle: {branded_bundle.name}")
