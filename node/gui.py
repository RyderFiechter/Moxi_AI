"""Desktop GUI for controlling the storage node (mirrors the dapp storage page)."""

from __future__ import annotations

import argparse
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional

from .api_client import NodeAPIClient, NodeAPIError, DEFAULT_API_BASE


class NodeDashboardApp(tk.Tk):
    """Tkinter desktop app mirroring the storage dashboard experience."""

    def __init__(self, api_base: str, refresh_seconds: int = 5) -> None:
        super().__init__()
        self.title("Moxi Storage Node")
        self.geometry("960x720")
        self.minsize(820, 640)

        self.client = NodeAPIClient(api_base=api_base)
        self.refresh_seconds = max(2, refresh_seconds)

        self.status_vars: Dict[str, tk.StringVar] = {}
        self.config_vars: Dict[str, tk.StringVar] = {}
        self.registry_vars: Dict[str, tk.StringVar] = {}

        self.payment_wallet_var = tk.StringVar()
        self.storage_var = tk.StringVar(value="0")
        self.message_var = tk.StringVar(value="Welcome to the storage node dashboard.")
        self.current_price_eth: float = 0.001
        self.payout_destination_var = tk.StringVar(value="Destination: —")
        self.payout_button: Optional[ttk.Button] = None

        self._build_layout()
        self._schedule_refresh(initial=True)

    # ------------------------------------------------------------------ UI
    def _build_layout(self) -> None:
        container = ttk.Frame(self, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(
            container,
            text="Storage Provider Dashboard",
            font=("Helvetica", 20, "bold"),
        )
        title.pack(anchor=tk.W, pady=(0, 12))

        subtitle = ttk.Label(
            container,
            text="Monitor your local storage node and manage blockchain registration.",
        )
        subtitle.pack(anchor=tk.W, pady=(0, 20))

        # Upper grid: status + configuration
        grid = ttk.Frame(container)
        grid.pack(fill=tk.BOTH, expand=True)
        grid.columnconfigure(0, weight=1, uniform="col")
        grid.columnconfigure(1, weight=1, uniform="col")

        self._build_status_card(grid).grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._build_config_card(grid).grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self._build_registry_card(container).pack(fill=tk.BOTH, expand=True, pady=(16, 0))
        self._build_message_bar(container).pack(fill=tk.X, pady=(16, 0))

    def _build_status_card(self, parent: tk.Widget) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text="Node Status")
        entries = [
            ("Wallet", "wallet"),
            ("Payment Wallet", "payment_wallet"),
            ("Uptime", "uptime"),
            ("Online", "online"),
            ("Total Storage", "total_storage"),
            ("Available Storage", "available_storage"),
            ("Used Storage", "used_storage"),
            ("Committed Storage", "committed_storage"),
            ("Storage Lending", "storage_lending"),
            ("Pending Earnings", "pending_earnings"),
            ("Lifetime Earnings", "lifetime_earnings"),
            ("Pay Rate", "pay_rate"),
        ]

        for idx, (label, key) in enumerate(entries):
            ttk.Label(frame, text=label, font=("Helvetica", 10, "bold")).grid(
                row=idx, column=0, sticky=tk.W, padx=8, pady=4
            )
            var = tk.StringVar(value="—")
            ttk.Label(frame, textvariable=var).grid(
                row=idx, column=1, sticky=tk.W, padx=8, pady=4
            )
            self.status_vars[key] = var

        return frame

    def _build_config_card(self, parent: tk.Widget) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text="Configuration")

        # Payment wallet entry
        ttk.Label(frame, text="Payment Wallet", font=("Helvetica", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, padx=8, pady=(8, 4)
        )
        wallet_entry = ttk.Entry(frame, textvariable=self.payment_wallet_var)
        wallet_entry.grid(row=1, column=0, sticky="ew", padx=8)
        ttk.Button(frame, text="Update Payment Wallet", command=self._update_payment_wallet).grid(
            row=2, column=0, sticky=tk.W, padx=8, pady=4
        )

        # Storage lending controls
        ttk.Label(frame, text="Storage Lending", font=("Helvetica", 10, "bold")).grid(
            row=3, column=0, sticky=tk.W, padx=8, pady=(12, 4)
        )
        lending_frame = ttk.Frame(frame)
        lending_frame.grid(row=4, column=0, sticky=tk.W, padx=8)
        ttk.Button(lending_frame, text="Enable", command=lambda: self._toggle_lending(True)).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(lending_frame, text="Disable", command=lambda: self._toggle_lending(False)).pack(
            side=tk.LEFT
        )

        # Rewards card
        rewards_frame = ttk.LabelFrame(frame, text="Rewards & Payouts")
        rewards_frame.grid(row=5, column=0, sticky="ew", padx=8, pady=(16, 8))
        ttk.Label(rewards_frame, text="Pending MOXI:", font=("Helvetica", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, padx=8, pady=4
        )
        pending_var = tk.StringVar(value="0.0000")
        ttk.Label(rewards_frame, textvariable=pending_var).grid(
            row=0, column=1, sticky=tk.W, padx=8, pady=4
        )
        self.payout_button = ttk.Button(rewards_frame, text="Send Payout", command=self._send_payout)
        self.payout_button.grid(row=1, column=0, sticky=tk.W, padx=8, pady=4)
        ttk.Label(rewards_frame, textvariable=self.payout_destination_var).grid(
            row=1, column=1, sticky=tk.W, padx=8, pady=4
        )
        self.status_vars["pending_label"] = pending_var

        return frame

    def _build_registry_card(self, parent: tk.Widget) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text="Storage Registry")

        registry_grid = ttk.Frame(frame)
        registry_grid.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        entries = [
            ("Registered", "registered"),
            ("Registered Storage", "registered_storage"),
            ("Price per GB (ETH)", "price"),
            ("Active", "active"),
            ("Message", "message"),
        ]
        for idx, (label, key) in enumerate(entries):
            ttk.Label(registry_grid, text=label, font=("Helvetica", 10, "bold")).grid(
                row=idx, column=0, sticky=tk.W, pady=4
            )
            var = tk.StringVar(value="—")
            ttk.Label(registry_grid, textvariable=var).grid(
                row=idx, column=1, sticky=tk.W, padx=8, pady=4
            )
            self.registry_vars[key] = var

        # Actions
        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, padx=8, pady=(8, 8))

        form = ttk.Frame(actions)
        form.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(form, text="Storage (GB)").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form, textvariable=self.storage_var, width=12).grid(
            row=1, column=0, sticky=tk.W
        )
        ttk.Button(form, text="Register / Update Offer", command=self._register_storage).grid(
            row=1, column=1, sticky=tk.W, padx=(12, 0)
        )

        button_row = ttk.Frame(actions)
        button_row.pack(fill=tk.X)
        ttk.Button(button_row, text="Activate", command=self._activate_registry).pack(
            side=tk.LEFT
        )
        ttk.Button(button_row, text="Deactivate", command=self._deactivate_registry).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(button_row, text="Refresh Storage", command=self._refresh_manual).pack(
            side=tk.LEFT
        )

        return frame

    def _build_message_bar(self, parent: tk.Widget) -> ttk.Frame:
        frame = ttk.Frame(parent)
        ttk.Label(frame, textvariable=self.message_var, foreground="green").pack(
            anchor=tk.W
        )
        return frame

    # ------------------------------------------------------------ Data loading
    def _schedule_refresh(self, initial: bool = False) -> None:
        if initial:
            self.after(100, self._refresh_async)
        else:
            self.after(self.refresh_seconds * 1000, self._refresh_async)

    def _refresh_async(self) -> None:
        threading.Thread(target=self._refresh_data, daemon=True).start()

    def _refresh_data(self) -> None:
        try:
            status = self.client.get_status()
            config = self.client.get_config()
            registry = None
            try:
                registry = self.client.get_registry_status()
            except NodeAPIError:
                registry = None
        except NodeAPIError as exc:
            self._show_error(str(exc))
            self._schedule_refresh()
            return

        self._update_status(status)
        self._update_config(config)
        self._update_registry(status, registry)
        self.message_var.set("Last refresh succeeded.")
        self.after_idle(self._schedule_refresh)

    # ------------------------------------------------------------ UI updates
    def _update_status(self, status: Dict[str, object]) -> None:
        self.status_vars["wallet"].set(status.get("wallet_address", "—"))
        payment = status.get("payment_wallet") or status.get("wallet_address") or "—"
        self.status_vars["payment_wallet"].set(payment)
        self.status_vars["uptime"].set(status.get("uptime_formatted", "—"))
        self.status_vars["online"].set("Online ✅" if status.get("is_online") else "Offline ❌")
        self.status_vars["total_storage"].set(self._format_gb(status.get("total_storage_gb")))
        self.status_vars["available_storage"].set(self._format_gb(status.get("available_storage_gb")))
        self.status_vars["used_storage"].set(self._format_gb(status.get("used_storage_gb")))
        committed = status.get("committed_storage_gb")
        self.status_vars["committed_storage"].set(self._format_gb(committed))
        lending = status.get("storage_lending_enabled")
        self.status_vars["storage_lending"].set("Enabled ✅" if lending else "Disabled ❌")
        pending = status.get("pending_earnings_moxi")
        lifetime = status.get("total_earned_moxi")
        payout_rate = status.get("payout_rate_moxi_per_second")
        self.status_vars["pending_earnings"].set(
            f"{pending:.4f} MOXI" if isinstance(pending, (int, float)) else "0.0000 MOXI"
        )
        self.status_vars["pending_label"].set(
            f"{pending:.4f} MOXI" if isinstance(pending, (int, float)) else "0.0000"
        )
        if isinstance(lifetime, (int, float)):
            last_payout = status.get("last_payout_at")
            suffix = f" (Last payout: {last_payout})" if last_payout else ""
            self.status_vars["lifetime_earnings"].set(f"{lifetime:.4f} MOXI{suffix}")
        else:
            self.status_vars["lifetime_earnings"].set("0.0000 MOXI")
        if isinstance(payout_rate, (int, float)):
            self.status_vars["pay_rate"].set(f"{payout_rate:.4f} MOXI/sec")
        else:
            self.status_vars["pay_rate"].set("—")
        destination = (
            self.payment_wallet_var.get().strip()
            or status.get("payment_wallet")
            or status.get("wallet_address")
            or "—"
        )
        self.payout_destination_var.set(f"Destination: {destination}")
        if self.payout_button:
            enable = isinstance(pending, (int, float)) and pending > 0
            self.payout_button.configure(state=tk.NORMAL if enable else tk.DISABLED)

    def _update_config(self, config: Dict[str, object]) -> None:
        self.payment_wallet_var.set(config.get("payment_wallet") or "")

    def _update_registry(
        self, status: Dict[str, object], registry: Optional[Dict[str, object]]
    ) -> None:
        registry_info = status.get("registry") or registry or {}
        registered = registry_info.get("registered")
        self.registry_vars["registered"].set("Yes ✅" if registered else "No ❌")
        if registered:
            storage = registry_info.get("registered_storage_gb") or registry_info.get("storageGB")
            self.registry_vars["registered_storage"].set(self._format_gb(storage))
            price = registry_info.get("price_per_gb_eth")
            if price is None and registry_info.get("provider_info"):
                raw = registry_info["provider_info"].get("pricePerGB")
                if raw is not None:
                    price = float(raw) / 1e18
            if isinstance(price, (int, float)):
                self.current_price_eth = float(price)
                self.registry_vars["price"].set(f"{price:.6f}")
            else:
                self.registry_vars["price"].set("—")
            active = registry_info.get("is_active")
            if active is None and registry_info.get("provider_info"):
                active = registry_info["provider_info"].get("isActive")
            self.registry_vars["active"].set("Yes ✅" if active else "No ❌")
            self.registry_vars["message"].set(registry_info.get("message", ""))
        else:
            self.registry_vars["registered_storage"].set("—")
            self.registry_vars["price"].set("—")
            self.registry_vars["active"].set("—")
            self.registry_vars["message"].set(
                registry_info.get("message")
                or registry_info.get("error")
                or "Set registry details in config.json"
            )

    # --------------------------------------------------------------- Actions
    def _update_payment_wallet(self) -> None:
        wallet = self.payment_wallet_var.get().strip()
        if not wallet.startswith("0x"):
            self._show_error("Enter a valid wallet address (0x...).")
            return
        self._run_action(lambda: self.client.update_payment_wallet(wallet), "Payment wallet updated.")

    def _toggle_lending(self, enabled: bool) -> None:
        label = "enabled" if enabled else "disabled"
        self._run_action(lambda: self.client.set_storage_lending(enabled), f"Storage lending {label}.")

    def _register_storage(self) -> None:
        try:
            storage = int(self.storage_var.get())
        except ValueError:
            self._show_error("Enter a numeric storage amount.")
            return
        if storage <= 0:
            self._show_error("Storage amount must be positive.")
            return
        price = self.current_price_eth
        if not isinstance(price, (int, float)) or price <= 0:
            self._show_error("No price configured. Update registry.price_per_gb_eth in config.json.")
            return
        self._run_action(
            lambda: self.client.register_storage(storage, price),
            f"Registered {storage} GB at {price:.6f} ETH/GB.",
        )

    def _activate_registry(self) -> None:
        self._run_action(self.client.activate_registry, "Provider activated.")

    def _deactivate_registry(self) -> None:
        self._run_action(self.client.deactivate_registry, "Provider deactivated.")

    def _send_payout(self) -> None:
        self._run_action(self.client.send_payout, "Payout request sent.")

    def _refresh_manual(self) -> None:
        self._refresh_async()

    # ----------------------------------------------------------- Action helper
    def _run_action(self, fn, success_message: str) -> None:
        def task():
            try:
                result = fn()
            except NodeAPIError as exc:
                self._show_error(str(exc))
                return
            response_message = ""
            if isinstance(result, dict):
                response_message = result.get("message") or ""
            self.message_var.set(response_message or success_message)
            self._refresh_async()

        threading.Thread(target=task, daemon=True).start()

    # ----------------------------------------------------------- utilities
    def _show_error(self, message: str) -> None:
        self.message_var.set(message)
        self.after_idle(lambda: messagebox.showerror("Storage Node", message))

    @staticmethod
    def _format_gb(value: Optional[object]) -> str:
        if isinstance(value, (int, float)):
            return f"{value:.2f} GB"
        return "—"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Desktop GUI for the storage provider node."
    )
    parser.add_argument(
        "--api-base",
        default=DEFAULT_API_BASE,
        help="Base URL for the node API (default: %(default)s).",
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=5,
        help="Seconds between automatic refreshes (default: %(default)s).",
    )
    args = parser.parse_args()

    app = NodeDashboardApp(api_base=args.api_base, refresh_seconds=args.refresh)
    app.mainloop()


if __name__ == "__main__":
    main()
