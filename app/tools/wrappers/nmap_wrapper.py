import subprocess

from app.tools.base import BaseTool


class NmapWrapper(BaseTool):
    name = "nmap"
    timeout_seconds = 120

    def run(self, target: str) -> dict:
        command = ["nmap", "-Pn", "-sV", target]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.timeout_seconds,
            )
            return {
                "tool": self.name,
                "command": " ".join(command),
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "tool": self.name,
                "command": " ".join(command),
                "stdout": "",
                "stderr": f"nmap timed out after {self.timeout_seconds} seconds.",
                "returncode": 124,
            }
        except FileNotFoundError:
            return {
                "tool": self.name,
                "command": " ".join(command),
                "stdout": "",
                "stderr": "nmap is not installed or not in PATH.",
                "returncode": 127,
            }