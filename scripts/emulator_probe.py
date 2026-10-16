"""Read-only inventory of relevant installed emulator packages and common paths."""
import json
import os
import platform
import re
import winreg
from pathlib import Path


def main():
    matches, denied = [], 0
    pattern = re.compile(r"MuMu|雷电|LDPlayer|BlueStacks|Nox|夜神|MEmu|逍遥|Android Studio|模拟器", re.I)
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 0, winreg.KEY_READ | view) as root:
                    for i in range(winreg.QueryInfoKey(root)[0]):
                        try:
                            name = winreg.EnumKey(root, i)
                            with winreg.OpenKey(root, name, 0, winreg.KEY_READ | view) as sub:
                                label = winreg.QueryValueEx(sub, "DisplayName")[0]
                                if not isinstance(label, str) or not pattern.search(label):
                                    continue
                                try:
                                    location = winreg.QueryValueEx(sub, "InstallLocation")[0]
                                except OSError:
                                    location = None
                                row = {"name": label, "install_location": location}
                                if row not in matches:
                                    matches.append(row)
                        except FileNotFoundError:
                            continue
                        except PermissionError:
                            denied += 1
            except FileNotFoundError:
                continue
            except PermissionError:
                denied += 1
    candidates = [r"C:\Program Files\MuMuVMM", r"C:\Program Files\Netease\MuMuPlayer",
                  r"C:\LDPlayer", r"D:\LDPlayer", r"E:\LDPlayer", r"C:\Program Files\BlueStacks_nxt",
                  r"C:\Program Files\Nox", str(Path(os.environ["LOCALAPPDATA"]) / "Android/Sdk/emulator/emulator.exe")]
    result = {"host_architecture": platform.machine(), "registered_emulators": matches,
              "registry_denied_count": denied, "existing_known_paths": [p for p in candidates if Path(p).exists()],
              "hardware_acceleration": "UNKNOWN (no emulator accel-check available yet)",
              "installed_or_started_by_this_probe": False}
    output = Path("output/phone/emulator_probe.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
