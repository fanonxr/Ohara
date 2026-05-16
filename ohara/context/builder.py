from __future__ import annotations

from ohara.context.models import ScanResult


class ContextBuilder:
    """Build compact markdown context packages optimized for LLM reasoning."""

    def build(self, scan: ScanResult) -> str:
        lines: list[str] = [
            "# Ohara Repository Context Package",
            "",
            "This package is a compressed repository intelligence summary for deep AI review.",
            "It intentionally avoids raw repository dumps and focuses on architecture signals.",
            "",
        ]
        for repo in scan.repositories:
            lines.extend(
                [
                    f"## Repository: {repo.name}",
                    "",
                    f"- Path: `{repo.path}`",
                    f"- Stack: {self._join(repo.stack)}",
                    f"- Frameworks: {self._join(repo.frameworks)}",
                    f"- Dependencies: {self._join(repo.dependencies)}",
                    "",
                    "### Directory Structure",
                    "",
                ]
            )
            lines.extend(f"- `{entry}`" for entry in repo.directory_tree[:120])
            lines.extend(["", "### Important Files", ""])
            for file in repo.important_files:
                lines.append(
                    f"- `{file.relative_path}` ({file.reason}, {file.size_bytes} bytes)"
                )
            lines.extend(["", "### TODOs and Work Markers", ""])
            if repo.todos:
                lines.extend(
                    f"- `{todo.path}:{todo.line}` - {todo.text}" for todo in repo.todos
                )
            else:
                lines.append("- None detected.")
            lines.extend(["", "### Identified Risks", ""])
            if repo.risks:
                lines.extend(
                    f"- `{risk.path}:{risk.line}` - {risk.kind}: {risk.description}"
                    for risk in repo.risks
                )
            else:
                lines.append("- None detected.")
            lines.extend(["", "### System Description", ""])
            lines.append(self._system_description(repo.stack, repo.frameworks))
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def _join(self, values: list[str]) -> str:
        return ", ".join(values) if values else "Not detected"

    def _system_description(self, stack: list[str], frameworks: list[str]) -> str:
        if not stack and not frameworks:
            return "No dominant stack detected from repository metadata."
        return (
            "Detected technologies suggest a system centered on "
            f"{self._join(frameworks or stack)}. Review should verify boundaries, "
            "operational maturity, security posture, and maintainability."
        )
