# =========================================================
# project_tool.py - Project / code folder help
# =========================================================

import os

DEFAULT_ROOT = os.path.join(os.path.expanduser("~"), "Desktop", "FRIDAY X")

CODE_EXT = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".md", ".txt",
    ".html", ".css", ".java", ".cpp", ".c", ".rs", ".go",
}


class ProjectTool:
    def __init__(self, root=None):
        self.root = os.path.abspath(root or DEFAULT_ROOT)

    def set_root(self, path):
        if path and os.path.isdir(path):
            self.root = os.path.abspath(path)
            return True
        return False

    def list_structure(self, max_files=80):
        if not os.path.isdir(self.root):
            return f"Project folder not found: {self.root}"
        lines = [f"Project: {self.root}", ""]
        count = 0
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in {
                ".git", "__pycache__", "node_modules", ".venv", "venv", "captures"
            }]
            rel = os.path.relpath(dirpath, self.root)
            if rel == ".":
                rel = ""
            for f in filenames:
                if count >= max_files:
                    lines.append("... (more files)")
                    return "\n".join(lines)
                ext = os.path.splitext(f)[1].lower()
                if ext in CODE_EXT or f in ("requirements.txt", "README.md", "config.py"):
                    lines.append(os.path.join(rel, f).replace("\\", "/"))
                    count += 1
        return "\n".join(lines) if count else f"No code files under {self.root}"

    def read_file(self, rel_path, max_chars=12000):
        path = rel_path
        if not os.path.isabs(path):
            path = os.path.join(self.root, rel_path)
        path = os.path.abspath(path)
        if not path.startswith(self.root):
            return "Access denied outside project folder."
        if not os.path.isfile(path):
            return f"File not found: {rel_path}"
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read(max_chars)
            return f"File: {path}\n\n{data}"
        except Exception as e:
            return f"Read error: {e}"

    def find_files(self, keyword, max_hits=30):
        keyword = (keyword or "").lower()
        hits = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in {
                ".git", "__pycache__", "node_modules", ".venv", "venv"
            }]
            for f in filenames:
                if keyword in f.lower():
                    hits.append(os.path.relpath(os.path.join(dirpath, f), self.root))
                    if len(hits) >= max_hits:
                        return hits
        return hits

    def context_summary(self):
        return self.list_structure()