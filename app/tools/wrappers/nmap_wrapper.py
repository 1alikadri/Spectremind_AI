import subprocess

from app.tools.base import BaseTool


class NmapWrapper(BaseTool):
    name = "nmap"

    def run(self, target: str) -> dict:
        command = ["nmap", "-Pn", "-sV", target]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )
            return {
                "tool": self.name,
                "command": " ".join(command),
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except FileNotFoundError:
            return {
                "tool": self.name,
                "command": " ".join(command),
                "stdout": "",
                "stderr": "nmap is not installed or not in PATH.",
                "returncode": 127,
            }