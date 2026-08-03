# Release runbook

本页面向仓库维护者。普通用户只需看 README 的固定版本安装命令。

## 发布边界

- GitHub 是源码、tag、wheel、Skill ZIP 和校验和的唯一公开事实源。
- tag 必须与 `chanlun_visual.__version__` 一致，例如应用 `0.1.0` 只能使用 `v0.1.0`。
- GitHub Actions 只创建 draft Release；维护者检查制品和日志后再手动公开。
- SkillHub 更新是独立外部动作。确认 GitHub Release 公共回读成功后再更新，且不得在仓库、日志或回复中保存 API key。

## 发布前

```bash
uv sync --all-extras
npm --prefix ui ci
npm --prefix ui run test
npm --prefix ui run lint
npm --prefix ui run build
uv run pytest
uv build
uv run python tools/build_skill_package.py --output-dir dist
uv run python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" .
uv run python tools/check_release_tag.py --tag v0.1.0
```

检查 `git diff --check`、敏感信息扫描和工作树范围。不要把 `.venv`、`node_modules`、本机路径、凭据、持仓或私有研究数据放入提交。

## 创建候选版本

维护者确认版本后再提交和创建 tag。推送 `v*.*.*` tag 会运行 `release.yml`，生成：

- `chanlun_visual-<version>-py3-none-any.whl`
- `chanlun_visual-<version>.tar.gz`
- `chanlun-trading-system-skill.zip`
- `SHA256SUMS`

工作流生成的是 draft Release，不会自动对外公开。

## 发布验收

1. CI 全部通过。
2. 从 draft 下载 wheel，在全新 Python 3.9 环境运行 `chanlun-visual --version`、`doctor --json` 和 `/api/health`。
3. 解压 Skill ZIP，确认只有 `SKILL.md`、`agents/`、`scripts/` 和 `references/`。
4. 核对 `SHA256SUMS`，确认 Release tag、包版本和 README 命令一致。
5. 手动公开 GitHub Release，并从公开页面重新下载一次验证。
6. 如需更新 SkillHub，使用 `skillhub.cn` 的既有条目并做公开详情页回读；失败或仍在审核时不得称为已发布。
