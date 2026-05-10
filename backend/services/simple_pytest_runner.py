import importlib.util
import inspect
import sys
import traceback
from pathlib import Path


def _load_module(path):
    module_name = "simple_test_" + "_".join(path.with_suffix("").parts[-4:])
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    sys.path.insert(0, str(Path.cwd()))
    tests_dir = Path.cwd() / "tests"

    if not tests_dir.exists():
        print("No tests/ directory found.")
        return 0

    total = 0
    failures = []

    for path in sorted(tests_dir.rglob("test_*.py")):
        module = _load_module(path)
        setup_function = getattr(module, "setup_function", None)

        for name, candidate in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("test_"):
                continue

            total += 1

            try:
                if setup_function:
                    setup_function()
                candidate()
                print(f"PASS {path.relative_to(Path.cwd())}::{name}")
            except Exception:
                failures.append(f"{path.relative_to(Path.cwd())}::{name}")
                print(f"FAIL {path.relative_to(Path.cwd())}::{name}")
                traceback.print_exc()

    print(f"\n{total - len(failures)} passed, {len(failures)} failed")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
