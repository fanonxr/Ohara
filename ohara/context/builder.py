from __future__ import annotations

from ohara.context.models import ScanResult


class ContextBuilder:
    """Build compact markdown context packages optimized for LLM reasoning."""

    def build(self, scan: ScanResult, template_name: str = "architecture-review") -> str:
        lines: list[str] = [
            "# Ohara Repository Context Package",
            "",
            "This package is a compressed repository intelligence summary for deep AI review.",
            "It intentionally avoids raw repository dumps and focuses on architecture signals.",
            "Scanner heuristics are labeled as candidates, not confirmed findings.",
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
                    "### Repository Briefing",
                    "",
                    f"- Product/app purpose: {repo.briefing.product_purpose}",
                    f"- Monorepo structure: {repo.briefing.monorepo_structure}",
                    f"- Main runtime components: {repo.briefing.main_runtime_components}",
                    f"- Known architectural invariants: {repo.briefing.architectural_invariants}",
                    "- Current shipped state vs scaffold/stub areas: "
                    f"{repo.briefing.shipped_state}",
                    f"- Local development expectations: {repo.briefing.local_development}",
                    f"- CI/deployment expectations: {repo.briefing.ci_expectations}",
                    f"- Intentional tradeoffs or deferred work: {repo.briefing.tradeoffs}",
                    "",
                    "### Repository Guidance",
                    "",
                ]
            )
            if repo.guidance:
                for item in repo.guidance:
                    lines.append(f"- `{item.path}` - {item.title}: {item.summary}")
            else:
                lines.append("- No repository instruction or architecture guidance files detected.")
            lines.extend(["", "### Review Mode Context Rules", ""])
            lines.extend(f"- {rule}" for rule in self._mode_rules(template_name))
            lines.extend(["", "### High-Signal Source Summaries", ""])
            summaries = self._prioritized_source_summaries(repo.source_summaries, template_name)
            if summaries:
                for summary in summaries:
                    lines.append(f"- `{summary.path}` ({summary.kind}): {summary.summary}")
                    for evidence in summary.evidence[:4]:
                        lines.append(f"  - Evidence: {evidence}")
            else:
                lines.append("- No high-signal source summaries detected.")
            lines.extend(["", "### Directory Structure", ""])
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
                    f"- Heuristic candidate `{risk.path}:{risk.line}` - "
                    f"{risk.kind}: {risk.description}"
                    for risk in repo.risks
                )
            else:
                lines.append("- None detected.")
            lines.extend(["", "### Excluded Noise", ""])
            visible_excluded = [
                excluded
                for excluded in repo.excluded_paths
                if not excluded.path.startswith(".git/")
                and not (
                    template_name != "security-audit" and excluded.path.startswith(".sqlx/")
                )
            ]
            if visible_excluded:
                for excluded in visible_excluded[:60]:
                    lines.append(f"- `{excluded.path}` - {excluded.reason}")
            else:
                lines.append("- No paths excluded by default rules.")
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

    def _mode_rules(self, template_name: str) -> list[str]:
        if template_name == "security-audit":
            return [
                "Security audit context rules: prioritize auth, authorization, env/config, "
                "secret handling, dependency manifests, CI secrets, webhook validation, CORS, "
                "logging, and data export/deletion flows.",
                "Treat detected secret patterns as scanner heuristic candidates unless literal "
                "credential material is visible in evidence.",
                "Include `.sqlx` metadata as database-shape context without treating query text "
                "alone as a confirmed vulnerability.",
            ]
        if template_name == "startup-readiness":
            return [
                "Startup readiness context rules: prioritize CI/CD, local setup friction, "
                "deployability, observability, tests, product stubs, operational runbooks, "
                "infrastructure completeness, and release risks.",
                "Separate production blockers from polish and long-term maintainability work.",
            ]
        return [
            "Architecture review context rules: prioritize design docs, module boundaries, "
            "entrypoints, route structure, state management, CI, and deployment topology.",
            "Deprioritize generated metadata and raw asset lists unless they reveal "
            "architecture risk.",
        ]

    def _prioritized_source_summaries(self, summaries, template_name: str):
        if template_name == "security-audit":
            tokens = ("auth", "middleware", "dependency", "CI", "Docker", "Terraform")
        elif template_name == "startup-readiness":
            tokens = ("CI", "Docker", "Terraform", "dependency", "entrypoint")
        else:
            tokens = ("entrypoint", "router", "Terraform", "Docker", "CI", "dependency")

        def key(summary):
            preferred = 0 if any(token.lower() in summary.kind.lower() for token in tokens) else 1
            return preferred, summary.priority, summary.path

        return sorted(summaries, key=key)[:24]
