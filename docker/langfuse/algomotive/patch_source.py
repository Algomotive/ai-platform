from pathlib import Path
import os
import re
import shutil
import subprocess

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = Path(
    os.environ.get(
        "LANGFUSE_SOURCE_ROOT",
        "/tmp/langfuse-algomotive-v4.38.0",
    )
).expanduser().resolve()
WEB = ROOT / "web"
SRC = WEB / "src"
PUBLIC = WEB / "public"
ASSETS = SCRIPT_DIR / "assets"

required = [
    SRC / "components/nav/AppSidebar/AppSidebar.tsx",
    SRC / "components/nav/AppSidebar/utils.ts",
    SRC / "components/layouts/app-layout/hooks/useLayoutMetadata.ts",
    SRC / "components/nav/book-a-call-button.tsx",
    SRC / "components/nav/support-button.tsx",
    PUBLIC / "icon.svg",
    PUBLIC / "wordart-black.svg",
    PUBLIC / "wordart-white.svg",
]

for path in required:
    if not path.exists():
        raise SystemExit(f"Required upstream file missing: {path}")

# Replace deterministic visual assets.
shutil.copy2(ASSETS / "algomotive-mark.svg", PUBLIC / "icon.svg")
shutil.copy2(
    ASSETS / "algomotive-wordmark-dark.svg",
    PUBLIC / "wordart-black.svg",
)
shutil.copy2(
    ASSETS / "algomotive-wordmark-dark.svg",
    PUBLIC / "wordart-white.svg",
)

algomotive_public = PUBLIC / "algomotive"
algomotive_public.mkdir(parents=True, exist_ok=True)

for name in (
    "algomotive-mark.svg",
    "algomotive-wordmark-dark.svg",
    "algomotive-favicon-v1.png",
):
    shutil.copy2(ASSETS / name, algomotive_public / name)

# Remove the customer-facing version/OSS badge while preserving its logic.
sidebar = SRC / "components/nav/AppSidebar/AppSidebar.tsx"
sidebar_text = sidebar.read_text(encoding="utf-8")

version_render = r"""          <div className="ml-auto flex min-w-0 items-center overflow-hidden group-data-[collapsible=icon]:hidden">
            <VersionLabel state={versionState} />
          </div>
"""

if sidebar_text.count(version_render) != 1:
    raise SystemExit(
        "Expected exactly one sidebar VersionLabel render block"
    )

sidebar.write_text(
    sidebar_text.replace(version_render, "", 1),
    encoding="utf-8",
)

# Preserve route structure while disabling upstream sales/support controls.
book_file = SRC / "components/nav/book-a-call-button.tsx"
book_file.write_text(
    'export const BookACallButton = () => null;\n',
    encoding="utf-8",
)

support_file = SRC / "components/nav/support-button.tsx"
support_file.write_text(
    'export const SupportButton = () => null;\n',
    encoding="utf-8",
)

# Disable upstream promotional sidebar notifications at the source.
utils_file = SRC / "components/nav/AppSidebar/utils.ts"
utils_text = utils_file.read_text(encoding="utf-8")

start_marker = (
    "export const SIDEBAR_NOTIFICATIONS: SidebarNotification[] = ["
)
start = utils_text.find(start_marker)

if start == -1:
    raise SystemExit("SIDEBAR_NOTIFICATIONS declaration not found")

array_start = utils_text.find("[", start)
depth = 0
array_end = None

for index in range(array_start, len(utils_text)):
    char = utils_text[index]

    if char == "[":
        depth += 1
    elif char == "]":
        depth -= 1

        if depth == 0:
            array_end = index
            break

if array_end is None:
    raise SystemExit("Could not determine notification array boundary")

patched_utils = (
    utils_text[:array_start]
    + "[]"
    + utils_text[array_end + 1:]
)

utils_file.write_text(patched_utils, encoding="utf-8")

# Apply customer-facing Algomotive branding and authentication behavior.
def replace_exact(path, old, new, expected=1):
    content = path.read_text(encoding="utf-8")
    count = content.count(old)
    if count != expected:
        raise SystemExit(
            f"Expected {expected} occurrence(s) in {path}: {old!r}; found {count}"
        )
    path.write_text(
        content.replace(old, new),
        encoding="utf-8",
    )


logo_file = SRC / "components/design-system/LangfuseLogo/LangfuseLogo.tsx"
topbar_file = SRC / "components/nav/topbar-brand.tsx"
hostname_file = SRC / "features/projects/components/HostNameProject.tsx"
trace_page_file = SRC / "features/traces/TracePage.tsx"
signin_file = SRC / "features/auth/SignInPage.tsx"
signout_file = SRC / "features/auth/lib/signOut.ts"

replace_exact(
    logo_file,
    "-ml-1.5 h-5 max-w-22 translate-y-px",
    "h-7 max-w-36 object-contain",
)
replace_exact(
    logo_file,
    "-ml-1.5 hidden h-5 max-w-22 translate-y-px",
    "hidden h-7 max-w-36 object-contain",
)
replace_exact(
    logo_file,
    'alt="Langfuse Logo"',
    'alt="Algomotive Observability Logo"',
    expected=4,
)
replace_exact(
    topbar_file,
    'alt="Langfuse Logo"',
    'alt="Algomotive Observability Logo"',
    expected=2,
)
replace_exact(
    hostname_file,
    "When connecting to Langfuse, use this hostname / baseurl.",
    "When connecting to Algomotive Observability, use this hostname / base URL.",
)
replace_exact(
    sidebar,
    'tooltip="Your Langfuse Organizations"',
    'tooltip="Your Algomotive Observability Organizations"',
)
replace_exact(
    trace_page_file,
    'title="Back to Langfuse"',
    'title="Back to Algomotive Observability"',
)
replace_exact(
    trace_page_file,
    '>Langfuse</Link>',
    '>Algomotive Observability</Link>',
)
replace_exact(
    trace_page_file,
    'title="Sign in to Langfuse"',
    'title="Sign in to Algomotive Observability"',
)
replace_exact(
    signin_file,
    "  SiKeycloak,\n",
    "",
)
replace_exact(
    signin_file,
    '<SiKeycloak className="mr-3" size={18} />',
    '<TbBrandAzure className="mr-3" size={18} />',
)

provider_label = """label={
                  typeof authProviders.keycloak === "object"
                    ? authProviders.keycloak.name
                    : "Keycloak"
                }"""

replace_exact(
    signin_file,
    provider_label,
    'label="Continue with Microsoft"',
)

signout_callback = (
    'callbackUrl: `${env.NEXT_PUBLIC_BASE_PATH ?? ""}'
    '/auth/sign-in${autoSignInOptOut}`,'
)

replace_exact(
    signout_file,
    signout_callback,
    'callbackUrl: "/logout",',
)

# Rebrand maintained dashboard names at the presentation layer.
dashboard_select = (
    SRC / "features/dashboard/components/HomeDashboardSelect.tsx"
)
project_home = SRC / "features/dashboard/ProjectHomePage.tsx"
home_dashboard = (
    ROOT / "packages/shared/src/domain/home-dashboard.ts"
)
clone_dialog = (
    SRC
    / "features/dashboard/components/CloneFirstDialogController.tsx"
)

dashboard_mapper = """    const toOption = (d: { id: string; name: string; owner: string }) => ({
      value: d.id,
      label: d.name,
      ...(d.owner === "LANGFUSE" ? { icon: <LangfuseIcon size={14} /> } : {}),
      ...(d.id === defaultDashboardId ? { badge: "Default" } : {}),
    });"""

branded_dashboard_mapper = """    const maintainedDashboardNames: Record<string, string> = {
      "Langfuse Agent Dashboard": "Algomotive Agent Dashboard",
      "Langfuse Cost Dashboard": "Algomotive Cost Dashboard",
      "Langfuse Home": "Algomotive Observability Home",
      "Langfuse Latency Dashboard": "Algomotive Latency Dashboard",
      "Langfuse Usage Management": "Algomotive Usage Management",
    };

    const toOption = (d: { id: string; name: string; owner: string }) => ({
      value: d.id,
      label:
        d.owner === "LANGFUSE"
          ? maintainedDashboardNames[d.name] ??
            d.name.replace(/^Langfuse\\s+/, "Algomotive ")
          : d.name,
      ...(d.owner === "LANGFUSE" ? { icon: <LangfuseIcon size={14} /> } : {}),
      ...(d.id === defaultDashboardId ? { badge: "Default" } : {}),
    });"""

replace_exact(
    dashboard_select,
    dashboard_mapper,
    branded_dashboard_mapper,
)
replace_exact(
    dashboard_select,
    'heading: "Langfuse-maintained"',
    'heading: "Algomotive Observability-maintained"',
)
replace_exact(
    project_home,
    '"Langfuse Home"',
    '"Algomotive Observability Home"',
)
replace_exact(
    home_dashboard,
    'name: "Langfuse Home"',
    'name: "Algomotive Observability Home"',
)
replace_exact(
    clone_dialog,
    "Langfuse-maintained tiles",
    "Algomotive Observability-maintained tiles",
)

# Rebrand maintained dashboards in the dashboard table presentation layer.
dashboard_table = (
    SRC / "features/dashboard/components/DashboardTable.tsx"
)

dashboard_row_type = """type DashboardTableRow = {
  id: string;
  name: string;
  description: string;
  createdAt: Date;
  updatedAt: Date;
  owner: "PROJECT" | "LANGFUSE";
};
"""

branded_dashboard_row_type = """type DashboardTableRow = {
  id: string;
  name: string;
  description: string;
  createdAt: Date;
  updatedAt: Date;
  owner: "PROJECT" | "LANGFUSE";
};

const maintainedDashboardNames: Record<string, string> = {
  "Langfuse Agent Dashboard": "Algomotive Agent Dashboard",
  "Langfuse Cost Dashboard": "Algomotive Cost Dashboard",
  "Langfuse Home": "Algomotive Observability Home",
  "Langfuse Latency Dashboard": "Algomotive Latency Dashboard",
  "Langfuse Usage Management": "Algomotive Usage Management",
};

const getDashboardDisplayName = (
  name: string,
  owner: DashboardTableRow["owner"],
) =>
  owner === "LANGFUSE"
    ? maintainedDashboardNames[name] ??
      name.replace(/^Langfuse\\s+/, "Algomotive ")
    : name;
"""

replace_exact(
    dashboard_table,
    dashboard_row_type,
    branded_dashboard_row_type,
)

replace_exact(
    dashboard_table,
    "              value: name,",
    """              value: getDashboardDisplayName(
                name,
                row.original.owner,
              ),""",
)

old_dashboard_owner = """          <span className="flex gap-1 px-2 py-0.5 text-xs">
            <span role="img" aria-label="Langfuse">
              🪢
            </span>
            Langfuse
          </span>"""

new_dashboard_owner = """          <span className="flex items-center gap-1.5 px-2 py-0.5 text-xs">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/icon.svg" alt="" aria-hidden="true" className="h-3.5 w-3.5" />
            Algomotive
          </span>"""

replace_exact(
    dashboard_table,
    old_dashboard_owner,
    new_dashboard_owner,
)

# Replace the authenticated browser-title product suffix.
metadata_file = (
    SRC / "components/layouts/app-layout/hooks/useLayoutMetadata.ts"
)
metadata_text = metadata_file.read_text(encoding="utf-8")

old_title = (
    'const title = activePathName '
    '? `${activePathName} | Langfuse` : "Langfuse";'
)
new_title = (
    'const title = activePathName '
    '? `${activePathName} | Algomotive Observability` '
    ': "Algomotive Observability";'
)

if metadata_text.count(old_title) != 1:
    raise SystemExit(
        "Expected exactly one authenticated layout title expression"
    )

metadata_file.write_text(
    metadata_text.replace(old_title, new_title, 1),
    encoding="utf-8",
)

# Apply the consolidated production-visible UI branding patch.
visible_ui_patch = SCRIPT_DIR / "visible-ui-branding.patch"

if not visible_ui_patch.exists():
    raise SystemExit(
        f"Visible UI branding patch missing: {visible_ui_patch}"
    )

patch_check = subprocess.run(
    [
        "patch",
        "--dry-run",
        "--silent",
        "-p1",
        "-d",
        str(ROOT),
        "-i",
        str(visible_ui_patch),
    ],
    capture_output=True,
    text=True,
)

if patch_check.returncode != 0:
    raise SystemExit(
        "Visible UI branding patch dry run failed:\n"
        + patch_check.stdout
        + patch_check.stderr
    )

subprocess.run(
    [
        "patch",
        "--silent",
        "-p1",
        "-d",
        str(ROOT),
        "-i",
        str(visible_ui_patch),
    ],
    check=True,
)

manifest = ROOT / "ALGOMOTIVE-BRANDING-MANIFEST.txt"
manifest.write_text(
    "\n".join(
        [
            "Base tag: v4.38.0",
            "Base commit: 4ecaabed8d9c39d0d3ba483f02ba1cca020388a9",
            "Product: Algomotive Observability",
            "Replaced: web/public/icon.svg",
            "Replaced: web/public/wordart-black.svg",
            "Replaced: web/public/wordart-white.svg",
            "Removed UI: VersionLabel render",
            "Disabled UI: BookACallButton",
            "Disabled UI: SupportButton",
            "Disabled UI: SIDEBAR_NOTIFICATIONS",
            "Rebranded title: Algomotive Observability",
            "Resized: Algomotive sidebar wordmark",
            "Rebranded visible UI: Algomotive Observability",
            "Rebranded auth provider: Continue with Microsoft",
            "Updated logout callback: /logout",
            "Rebranded maintained dashboards: Algomotive",
            "Rebranded dashboard table owner: Algomotive",
            "Rebranded production UI files: 48",
            "Preserved: organization/project/account/navigation controls",
            "",
        ]
    ),
    encoding="utf-8",
)

print("PATCHED_APP_SIDEBAR=YES")
print("PATCHED_BOOK_A_CALL=YES")
print("PATCHED_SUPPORT=YES")
print("PATCHED_NOTIFICATIONS=YES")
print("PATCHED_VISUAL_ASSETS=YES")
print("PATCHED_BROWSER_TITLE=YES")
print("PATCHED_SIDEBAR_LOGO_SIZE=YES")
print("PATCHED_VISIBLE_PRODUCT_TEXT=YES")
print("PATCHED_MICROSOFT_PROVIDER_BRANDING=YES")
print("PATCHED_COMPLETE_LOGOUT_CALLBACK=YES")
print("PATCHED_MAINTAINED_DASHBOARD_NAMES=YES")
print("PATCHED_DASHBOARD_TABLE_BRANDING=YES")
print("PATCHED_CONSOLIDATED_VISIBLE_UI=YES")
print("LANGFUSE_ALGOMOTIVE_SOURCE_PATCH_APPLIED")
