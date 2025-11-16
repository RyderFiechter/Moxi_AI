#!/usr/bin/env bash
set -euo pipefail

MODE=${1:-create}
VOLUME_FILE=${VOLUME_FILE:-/var/moxi-node/storage-node.img}
VOLUME_SIZE_GB=${VOLUME_SIZE_GB:-100}
MAPPER_NAME=${MAPPER_NAME:-moxi-node}
MOUNT_POINT=${MOUNT_POINT:-/mnt/moxi-node}
FILESYSTEM=${FILESYSTEM:-ext4}
CONTROLLER_PRIVATE_KEY=${CONTROLLER_PRIVATE_KEY:-${PRIVATE_KEY:-}}

if [[ $EUID -ne 0 ]]; then
  echo "[!] Please run this script as root (sudo)." >&2
  exit 1
fi

if [[ -z "$CONTROLLER_PRIVATE_KEY" ]]; then
  echo "[!] Set CONTROLLER_PRIVATE_KEY (or PRIVATE_KEY) so we can derive the LUKS passphrase." >&2
  exit 1
fi

if ! command -v cryptsetup >/dev/null 2>&1; then
  echo "[!] cryptsetup is required. Install it via 'sudo apt install cryptsetup' (or distro equivalent)." >&2
  exit 1
fi

if ! command -v sha256sum >/dev/null 2>&1; then
  echo "[!] sha256sum is required." >&2
  exit 1
fi

if ! command -v mountpoint >/dev/null 2>&1; then
  echo "[!] mountpoint is required (usually part of util-linux)." >&2
  exit 1
fi

PASSPHRASE=$(echo -n "$CONTROLLER_PRIVATE_KEY" | sha256sum | awk '{print $1}')

derive_mapper() {
  echo "/dev/mapper/${MAPPER_NAME}"
}

create_volume() {
  if [[ -e "$VOLUME_FILE" ]]; then
    echo "[!] $VOLUME_FILE already exists. Refusing to overwrite; set VOLUME_FILE to a new path or delete it manually." >&2
    exit 1
  fi

  mkdir -p "$(dirname "$VOLUME_FILE")"
  truncate -s "${VOLUME_SIZE_GB}G" "$VOLUME_FILE"
  printf '%s' "$PASSPHRASE" | cryptsetup luksFormat --batch-mode "$VOLUME_FILE" -
  printf '%s' "$PASSPHRASE" | cryptsetup open "$VOLUME_FILE" "$MAPPER_NAME" -
  mkfs -t "$FILESYSTEM" "$(derive_mapper)"
  mkdir -p "$MOUNT_POINT"
  mount "$(derive_mapper)" "$MOUNT_POINT"
  chown -R "${SUDO_UID:-0}:${SUDO_GID:-0}" "$MOUNT_POINT"
  echo "[+] Created and mounted encrypted volume at $MOUNT_POINT"
}

open_volume() {
  if [[ ! -e "$VOLUME_FILE" ]]; then
    echo "[!] $VOLUME_FILE is missing. Nothing to open." >&2
    exit 1
  fi
  if mountpoint -q "$MOUNT_POINT"; then
    echo "[i] $MOUNT_POINT is already mounted."
    return
  fi
  printf '%s' "$PASSPHRASE" | cryptsetup open "$VOLUME_FILE" "$MAPPER_NAME" -
  mkdir -p "$MOUNT_POINT"
  mount "$(derive_mapper)" "$MOUNT_POINT"
  echo "[+] Mounted $(derive_mapper) at $MOUNT_POINT"
}

close_volume() {
  if mountpoint -q "$MOUNT_POINT"; then
    umount "$MOUNT_POINT"
    echo "[i] Unmounted $MOUNT_POINT"
  fi
  if [[ -e "$(derive_mapper)" ]]; then
    cryptsetup close "$MAPPER_NAME"
    echo "[i] Closed mapper $MAPPER_NAME"
  fi
}

case "$MODE" in
  create)
    create_volume
    ;;
  open)
    open_volume
    ;;
  close)
    close_volume
    ;;
  *)
    echo "Usage: MODE=create|open|close [environment variables]" >&2
    echo "Example: sudo CONTROLLER_PRIVATE_KEY=0xabc... VOLUME_SIZE_GB=200 ./setup_encrypted_volume.sh create" >&2
    exit 1
    ;;
esac

cat <<INFO

Mount point: $MOUNT_POINT
Backing file: $VOLUME_FILE
Mapper: $(derive_mapper)

Share this directory from another machine via SSHFS/NFS after running 'open'.
INFO
