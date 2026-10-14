<!-- Static deployment instructions; depends on selected-paper builds and the optional manual workflow. -->
# Hosting

## Local use

`npm run dev` hosts the small example locally. `npm run dev:paper` hosts your paper.
You can use and modify the starter entirely locally. No account, secret or deployment
is required. For a production preview, build the selected paper and run preview with
the same `--paper` choice. Stop the current server before switching papers.

## GitHub Pages

Enable GitHub Actions as the Pages source. The supplied workflow is manual-only and
always builds the minimal example. Run it from the Actions tab only when you want to
publish that demonstration. It does not publish the Nobel excerpt.

For your own paper, adapt the workflow's paper selection. A project Pages site usually
needs `BASE_PATH=/repository-name`; a root-domain site uses an empty base. The supplied
workflow derives the project path from the repository name. For a custom domain, adjust
BASE_PATH and configure the domain in Pages settings; never use the official Nobel domain.

Set `siteUrl` in the active paper's configuration to its full published address, including
its subpath, if Markdown downloads should have absolute links. Empty siteUrl uses portable
local paths. Check both root and subpath builds before release.

## Netlify

Create a site from your repository. Use `npm run build:paper` as the build command and
`build` as the publish directory, with Node 22.12+ and Python 3.11+. Leave BASE_PATH empty
when deploying at the domain root. Review Netlify's deployment settings before connecting
a branch; its automatic publishing is separate from this starter's manual GitHub workflow.

## Other static hosts

Upload the selected build's `build/` directory to a static host. No Svelte server, Python
server, database or credentials are required at runtime. Ensure your host serves nested
`index.html` routes. A custom domain is optional.

The reproduction archive and source assets are public files in the build. Inspect them
before publishing. For private drafts, keep deployment private or use local development.
