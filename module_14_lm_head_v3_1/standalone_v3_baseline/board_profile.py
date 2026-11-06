"""Bind board timing and build checks to a hash-checked hardware package."""
import hashlib
import json
from pathlib import Path

PROFILES = {0x10008011: 100_000_000, 0x20C08011: 200_000_000}


def load_profile(package_dir=None):
    # Legacy frozen 100 MHz packages predate RUN_PROFILE.json.
    profile = {"build_config": 0x10008011, "ip_clock_hz": 100_000_000,
               "clock_basis": "nominal PL user clock", "profile_source": "legacy_100mhz"}
    if package_dir is None:
        return profile
    package = Path(package_dir)
    path = package / "RUN_PROFILE.json"
    if path.exists():
        entries = [line.split()[0].lower() for line in
                   (package / "ARTIFACTS.sha256").read_text().splitlines()
                   if len(line.split()) == 2 and line.split()[1] == path.name]
        if len(entries) != 1 or entries[0] != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError("RUN_PROFILE.json package hash mismatch")
        profile = json.loads(path.read_text(encoding="utf-8-sig"))
        build = profile["build_config"]
        profile["build_config"] = int(build, 0) if isinstance(build, str) else int(build)
        if PROFILES.get(profile["build_config"]) != profile["ip_clock_hz"]:
            raise ValueError("Unknown or inconsistent build_config / ip_clock_hz")
        profile["profile_source"] = str(path.resolve())
    return profile


def check_loader_pair(package, loader_package, board_ip):
    package, loader_package = Path(package), Path(loader_package)
    profiled = (package / "RUN_PROFILE.json").exists()
    if profiled != (loader_package / "RUN_PROFILE.json").exists():
        raise ValueError("Hardware and loader must both have matching profiles")
    if profiled:
        hardware = load_profile(package)
        loader = load_profile(loader_package)
        for field in ("build_config", "ip_clock_hz", "hardware_xsa_sha256", "psu_init_sha256", "board_ip"):
            if hardware[field] != loader[field]:
                raise ValueError("Hardware/loader profile mismatch: " + field)
        for path, expected in ((package / "m14_v2_single.xsa", hardware["hardware_xsa_sha256"]),
                               (loader_package / "psu_init.tcl", hardware["psu_init_sha256"])):
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError("Hardware/loader binding hash mismatch: " + str(path))
        if board_ip != hardware["board_ip"]:
            raise ValueError("Board IP does not match the selected loader")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("loader_package", type=Path)
    parser.add_argument("board_ip")
    args = parser.parse_args()
    check_loader_pair(args.package, args.loader_package, args.board_ip)
    print("M14_PACKAGE_PAIR=PASS")
