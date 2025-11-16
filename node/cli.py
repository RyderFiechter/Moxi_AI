"""Command line interface for the storage node."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import time

import typer
from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.table import Table

from .api_client import (
    NodeAPIClient,
    NodeAPIError,
    DEFAULT_API_BASE,
    API_ENVVAR,
)
from .main import load_config, run_node

API_HELP = "Base URL for the running storage node API."

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
    help="Storage node CLI.\n\n"
    "Run the node locally and interact with the same operations exposed in the dapp dashboard.",
)

config_app = typer.Typer(help="Inspect or update node configuration.")
storage_app = typer.Typer(help="Manage storage lending state.")
registry_app = typer.Typer(help="Interact with the StorageRegistry contract via the node.")
rewards_app = typer.Typer(help="Trigger payout operations.")

app.add_typer(config_app, name="config")
app.add_typer(storage_app, name="storage")
app.add_typer(registry_app, name="registry")
app.add_typer(rewards_app, name="rewards")


def _print_json(payload: Any) -> None:
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


def _format_gb(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f} GB"


def _ensure_wallet(address: str) -> None:
    if not address.startswith("0x") or len(address) < 6:
        raise typer.BadParameter("Wallet addresses must be 0x-prefixed hex strings.")


def _print_status(status: Dict[str, Any]) -> None:
    typer.echo(f"Wallet:          {status.get('wallet_address', 'unknown')}")
    typer.echo(
        f"Payment Wallet:  {status.get('payment_wallet') or status.get('wallet_address', '-')}"
    )
    typer.echo(f"Online:          {'yes' if status.get('is_online') else 'no'}")
    typer.echo(f"Uptime:          {status.get('uptime_formatted', 'n/a')}")
    typer.echo(f"Total Storage:   {_format_gb(status.get('total_storage_gb'))}")
    typer.echo(f"Used Storage:    {_format_gb(status.get('used_storage_gb'))}")
    typer.echo(f"Available:       {_format_gb(status.get('available_storage_gb'))}")

    committed = status.get("committed_storage_gb")
    if committed is not None:
        typer.echo(f"Committed:       {_format_gb(committed)}")

    if status.get("storage_lending_enabled") is not None:
        typer.echo(
            f"Lending:         {'enabled' if status.get('storage_lending_enabled') else 'disabled'}"
        )

    earnings = status.get("total_earned_moxi")
    pending = status.get("pending_earnings_moxi")
    if earnings is not None or pending is not None:
        typer.echo("Rewards:")
        if earnings is not None:
            typer.echo(f"  Lifetime:      {earnings:.4f} MOXI")
        if pending is not None:
            typer.echo(f"  Pending:       {pending:.4f} MOXI")
        rate = status.get("payout_rate_moxi_per_second")
        if rate is not None:
            typer.echo(f"  Pay Rate:      {rate:.4f} MOXI/sec")

    registry = status.get("registry") or {}
    typer.echo("Registry:")
    typer.echo(
        f"  Registered:    {'yes' if registry.get('registered') else 'no'}"
    )
    if registry.get("registered"):
        typer.echo(
            f"  Storage:       {_format_gb(registry.get('registered_storage_gb'))}"
        )
        price = registry.get("price_per_gb_eth")
        if price is not None:
            typer.echo(f"  Price:         {price:.6f} ETH/GB")
        typer.echo(
            f"  Active:        {'yes' if registry.get('is_active') else 'no'}"
        )
    elif registry.get("message"):
        typer.echo(f"  Message:       {registry['message']}")
    elif registry.get("error"):
        typer.echo(f"  Error:         {registry['error']}")


class DashboardApp:
    """Interactive terminal dashboard mirroring the dapp storage page."""

    def __init__(self, api_base: str, auto_refresh: Optional[float] = None) -> None:
        self.api_base = api_base
        self.auto_refresh = auto_refresh
        self.console = Console()
        self.last_message: Optional[str] = None
        self.last_state: str = "info"
        self.client = NodeAPIClient(api_base=api_base)

    def run(self) -> None:
        """Run the interactive dashboard loop."""
        try:
            while True:
                try:
                    status, config, registry = self._load_data()
                except NodeAPIError as exc:
                    self.console.print(f"[bold red]Error:[/] {exc}")
                    retry = self.console.input("Press Enter to retry or type 'q' to exit: ").strip().lower()
                    if retry in {"q", "quit", "exit"}:
                        break
                    continue

                self._render(status, config, registry)

                if self.auto_refresh and self.auto_refresh > 0:
                    self.console.print(
                        f"[dim]Auto refresh in {self.auto_refresh:.1f}s. Press Ctrl+C to exit.[/dim]"
                    )
                    time.sleep(self.auto_refresh)
                    continue

                choice = self.console.input(
                    "\n[bold cyan]Select action[/] (Enter=Refresh, q=Quit): "
                ).strip().lower()
                if choice in {"", "r", "refresh"}:
                    self._set_message("Storage metrics refreshed", "info")
                    continue
                if choice in {"q", "quit", "exit"}:
                    break
                self._handle_action(choice, status)
        except KeyboardInterrupt:
            self.console.print("\n[bold yellow]Dashboard closed by user.[/]")

    def _load_data(self) -> Tuple[Dict[str, Any], Dict[str, Any], Optional[Dict[str, Any]]]:
        status = self.client.get_status()
        config = self.client.get_config()
        registry = None
        try:
            registry = self.client.get_registry_status()
        except NodeAPIError:
            registry = None
        return status, config, registry

    def _render(self, status: Dict[str, Any], config: Dict[str, Any], registry: Optional[Dict[str, Any]]) -> None:
        self.console.clear()
        self.console.rule("[bold cyan]Storage Provider Dashboard[/bold cyan]")
        self.console.print(Align(self._status_panel(status), align="left"))
        self.console.print(Align(self._config_panel(status, config), align="left"))
        self.console.print(Align(self._registry_panel(status, registry), align="left"))
        self.console.print(self._actions_panel())
        if self.last_message:
            border = {"success": "green", "error": "red", "info": "blue"}.get(self.last_state, "blue")
            self.console.print(
                Panel(self.last_message, title="Last Action", border_style=border)
            )

    def _status_panel(self, status: Dict[str, Any]) -> Panel:
        table = Table.grid(expand=True)
        table.add_column(justify="right", style="cyan", width=24)
        table.add_column(style="white")
        table.add_row("Wallet", status.get("wallet_address", "—"))
        table.add_row(
            "Payment Wallet",
            status.get("payment_wallet") or status.get("wallet_address") or "—",
        )
        table.add_row("Online", "Online ✅" if status.get("is_online") else "Offline ❌")
        table.add_row("Uptime", status.get("uptime_formatted", "—"))
        table.add_row("Total Storage", _format_gb(status.get("total_storage_gb")))
        table.add_row("Available Storage", _format_gb(status.get("available_storage_gb")))
        table.add_row("Used Storage", _format_gb(status.get("used_storage_gb")))
        committed = status.get("committed_storage_gb")
        if committed is not None:
            table.add_row("Committed Storage", _format_gb(committed))
        pending = status.get("pending_earnings_moxi")
        rate = status.get("payout_rate_moxi_per_second")
        total = status.get("total_earned_moxi")
        if pending is not None or total is not None or rate is not None:
            table.add_row("—", "—")
            if pending is not None:
                table.add_row("Pending Earnings", f"{pending:.4f} MOXI")
            if total is not None:
                last_payout = status.get("last_payout_at")
                payout_info = (
                    f"{total:.4f} MOXI (Last payout: {last_payout})"
                    if last_payout
                    else f"{total:.4f} MOXI"
                )
                table.add_row("Lifetime Earnings", payout_info)
            if rate is not None:
                table.add_row("Payout Rate", f"{rate:.4f} MOXI/sec")
        lending = status.get("storage_lending_enabled")
        if lending is not None:
            table.add_row(
                "Storage Lending", "Enabled ✅" if lending else "Disabled ❌"
            )
        return Panel(table, title="Node Status", border_style="cyan", box=box.ROUNDED)

    def _config_panel(self, status: Dict[str, Any], config: Dict[str, Any]) -> Panel:
        table = Table.grid(expand=True)
        table.add_column(justify="right", style="magenta", width=24)
        table.add_column(style="white")
        table.add_row("Configured Wallet", config.get("payment_wallet") or "—")
        table.add_row(
            "Storage Lending",
            "Enabled ✅" if config.get("storage_lending_enabled") else "Disabled ❌",
        )
        table.add_row("Ping Interval", f"{config.get('ping_interval', '—')} seconds")
        if status.get("storage_volume"):
            storage_volume = status["storage_volume"]
            table.add_row("Volume Path", storage_volume.get("mount_path", "—"))
            table.add_row("Encrypted File", storage_volume.get("backing_file", "—"))
            table.add_row("Reserved Size", _format_gb(storage_volume.get("size_gb")))
        return Panel(
            table,
            title="Configuration",
            border_style="magenta",
            box=box.ROUNDED,
        )

    def _registry_panel(
        self, status: Dict[str, Any], registry: Optional[Dict[str, Any]]
    ) -> Panel:
        table = Table.grid(expand=True)
        table.add_column(justify="right", style="green", width=28)
        table.add_column(style="white")
        registry_status = status.get("registry") or registry or {}
        registered = registry_status.get("registered", False)
        table.add_row("Registered", "Yes ✅" if registered else "No ❌")
        if registered:
            table.add_row(
                "Registered Storage",
                _format_gb(registry_status.get("registered_storage_gb") or registry_status.get("storageGB")),
            )
            price = registry_status.get("price_per_gb_eth")
            if price is None and registry_status.get("provider_info"):
                price_raw = registry_status["provider_info"].get("pricePerGB")
                if price_raw is not None:
                    price = float(price_raw) / 1e18
            if price is not None:
                table.add_row("Price", f"{price:.6f} ETH/GB")
            is_active = registry_status.get("is_active")
            if is_active is None and registry_status.get("provider_info"):
                is_active = registry_status["provider_info"].get("isActive")
            if is_active is not None:
                table.add_row("Active", "Yes ✅" if is_active else "No ❌")
        else:
            message = registry_status.get("message") or registry_status.get("error")
            if message:
                table.add_row("Status", message)
        return Panel(
            table,
            title="Storage Registry",
            border_style="green",
            box=box.ROUNDED,
        )

    def _actions_panel(self) -> Panel:
        table = Table.grid(padding=(0, 2))
        table.add_column(style="yellow", justify="right", width=4)
        table.add_column(style="white")
        table.add_row("1", "Update payment wallet")
        table.add_row("2", "Enable storage lending")
        table.add_row("3", "Disable storage lending")
        table.add_row("4", "Register / update storage offer")
        table.add_row("5", "Activate registry provider")
        table.add_row("6", "Deactivate registry provider")
        table.add_row("7", "Send pending payout")
        table.add_row("R", "Refresh metrics")
        table.add_row("Q", "Quit dashboard")
        return Panel(
            table,
            title="Actions",
            border_style="yellow",
            box=box.ROUNDED,
        )

    def _set_message(self, message: str, state: str) -> None:
        self.last_message = message
        self.last_state = state

    def _handle_action(self, choice: str, status: Dict[str, Any]) -> None:
        handlers = {
            "1": self._action_set_payment_wallet,
            "2": lambda: self._post_message(self.client.set_storage_lending, "Storage lending enabled", True),
            "3": lambda: self._post_message(self.client.set_storage_lending, "Storage lending disabled", False),
            "4": lambda: self._action_register(status),
            "5": lambda: self._post_message(self.client.activate_registry, "Provider activated"),
            "6": lambda: self._post_message(self.client.deactivate_registry, "Provider deactivated"),
            "7": lambda: self._post_message(self.client.send_payout, "Payout triggered"),
        }
        handler = handlers.get(choice)
        if handler is None:
            self._set_message("Unknown action. Press Enter to refresh.", "error")
            return
        try:
            handler()
        except NodeAPIError as exc:
            self._set_message(str(exc), "error")

    def _action_set_payment_wallet(self) -> None:
        wallet = Prompt.ask("New payment wallet (0x...)").strip()
        _ensure_wallet(wallet)
        response = self.client.update_payment_wallet(wallet)
        self._set_message(
            response.get("message") or f"Payment wallet updated to {wallet}",
            "success",
        )

    def _action_register(self, status: Dict[str, Any]) -> None:
        default_storage = int(max(status.get("available_storage_gb") or 0, 1))
        storage_gb = IntPrompt.ask(
            "Storage to commit (GB)",
            default=str(default_storage),
            show_choices=False,
            show_default=True,
        )
        price_default = status.get("registry", {}).get("price_per_gb_eth") or 0.001
        price_input = Prompt.ask(
            "Price per GB (ETH)",
            default=f"{price_default:.6f}",
            show_default=True,
        )
        try:
            price_value = float(price_input)
        except ValueError:
            self._set_message("Price must be a number.", "error")
            return
        response = self.client.register_storage(int(storage_gb), float(price_value))
        self._set_message(
            response.get("message")
            or f"Registered {storage_gb} GB at {price_value:.6f} ETH/GB",
            "success",
        )

    def _post_message(self, func, fallback: str, *args) -> None:
        response = func(*args) if args else func()
        if isinstance(response, dict):
            self._set_message(response.get("message") or fallback, "success")
        else:
            self._set_message(fallback, "success")


@app.command()
def run(
    config: Path = typer.Option(
        Path("config.json"),
        "--config",
        "-c",
        help="Path to the node configuration JSON file.",
    ),
    port: Optional[int] = typer.Option(
        None, "--port", "-p", help="Override the API port defined in the config file."
    ),
    ping_interval: Optional[int] = typer.Option(
        None,
        "--ping-interval",
        help="Override the ping interval defined in the config file.",
    ),
) -> None:
    """Start the storage node and its HTTP API."""
    config_data = load_config(str(config))

    if port is not None:
        config_data["port"] = port
    if ping_interval is not None:
        config_data["ping_interval"] = ping_interval

    try:
        asyncio.run(run_node(config_data))
    except NodeAPIError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except KeyboardInterrupt:
        typer.echo("Stopping node...")


@app.command()
def status(
    api_base: str = typer.Option(
        DEFAULT_API_BASE,
        "--api-base",
        envvar=API_ENVVAR,
        help=API_HELP,
    ),
    as_json: bool = typer.Option(
        False, "--json", help="Return the raw JSON payload from /status."
    ),
) -> None:
    """Show real-time node status (matches the storage dashboard)."""
    client = NodeAPIClient(api_base=api_base)
    try:
        data = client.get_status()
    except NodeAPIError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    if as_json:
        _print_json(data)
        return

    _print_status(data)


@app.command()
def dashboard(
    api_base: str = typer.Option(
        DEFAULT_API_BASE,
        "--api-base",
        envvar=API_ENVVAR,
        help=API_HELP,
    ),
    auto_refresh: Optional[float] = typer.Option(
        None,
        "--auto-refresh",
        help="Seconds between automatic refreshes (press Ctrl+C to exit).",
    ),
) -> None:
    """Launch an interactive dashboard mirroring the dapp storage page."""
    DashboardApp(api_base=api_base, auto_refresh=auto_refresh).run()


@config_app.command("show")
def config_show(
    api_base: str = typer.Option(
        DEFAULT_API_BASE,
        "--api-base",
        envvar=API_ENVVAR,
        help=API_HELP,
    ),
    as_json: bool = typer.Option(
        False, "--json", help="Return the raw JSON payload from /config."
    ),
) -> None:
    """Display the currently running node configuration."""
    client = NodeAPIClient(api_base=api_base)
    try:
        data = client.get_config()
    except NodeAPIError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    if as_json:
        _print_json(data)
        return

    typer.echo(f"Wallet:          {data.get('wallet_address', '-')}")
    typer.echo(f"Payment Wallet:  {data.get('payment_wallet', '-')}")
    typer.echo(
        f"Storage Lending: {'enabled' if data.get('storage_lending_enabled') else 'disabled'}"
    )
    typer.echo(f"Ping Interval:   {data.get('ping_interval')} seconds")


@config_app.command("set-payment")
def config_set_payment(
    wallet: str = typer.Argument(..., help="0x-prefixed wallet to receive payouts."),
    api_base: str = typer.Option(
        DEFAULT_API_BASE,
        "--api-base",
        envvar=API_ENVVAR,
        help=API_HELP,
    ),
) -> None:
    """Update the node's payment wallet."""
    _ensure_wallet(wallet)
    client = NodeAPIClient(api_base=api_base)
    try:
        data = client.update_payment_wallet(wallet)
    except NodeAPIError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho(
        f"Payment wallet updated to {data.get('payment_wallet', wallet)}.",
        fg=typer.colors.GREEN,
    )


@storage_app.command("enable")
def storage_enable(
    api_base: str = typer.Option(
        DEFAULT_API_BASE,
        "--api-base",
        envvar=API_ENVVAR,
        help=API_HELP,
    ),
) -> None:
    """Enable storage lending (same as the dashboard toggle)."""
    client = NodeAPIClient(api_base=api_base)
    try:
        response = client.set_storage_lending(True)
    except NodeAPIError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho(response.get("message", "Storage lending enabled."), fg=typer.colors.GREEN)


@storage_app.command("disable")
def storage_disable(
    api_base: str = typer.Option(
        DEFAULT_API_BASE,
        "--api-base",
        envvar=API_ENVVAR,
        help=API_HELP,
    ),
) -> None:
    """Disable storage lending."""
    client = NodeAPIClient(api_base=api_base)
    try:
        response = client.set_storage_lending(False)
    except NodeAPIError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho(response.get("message", "Storage lending disabled."), fg=typer.colors.YELLOW)


@registry_app.command("status")
def registry_status(
    api_base: str = typer.Option(
        DEFAULT_API_BASE,
        "--api-base",
        envvar=API_ENVVAR,
        help=API_HELP,
    ),
    as_json: bool = typer.Option(
        False, "--json", help="Return the raw JSON payload from /registry/status."
    ),
) -> None:
    """Display the node's registry registration details."""
    client = NodeAPIClient(api_base=api_base)
    try:
        data = client.get_registry_status()
    except NodeAPIError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    if as_json:
        _print_json(data)
        return

    if data.get("registered"):
        provider = data.get("provider_info", {})
        typer.secho("Registered ✅", fg=typer.colors.GREEN)
        typer.echo(f"Storage: {provider.get('storageGB')} GB")
        typer.echo(
            f"Price:   {float(provider.get('pricePerGB', 0)) / 1e18:.6f} ETH/GB"
        )
        typer.echo(f"Active:  {'yes' if provider.get('isActive') else 'no'}")
    else:
        typer.secho("Not registered", fg=typer.colors.YELLOW)
        message = data.get("message") or data.get("error")
        if message:
            typer.echo(message)


@registry_app.command("register")
def registry_register(
    storage_gb: int = typer.Option(
        ...,
        "--storage-gb",
        "-s",
        min=1,
        help="Amount of storage to commit/register.",
    ),
    price_per_gb_eth: float = typer.Option(
        ...,
        "--price-per-gb",
        "-p",
        min=0.000000000000000001,
        help="Price per GB in ETH.",
    ),
    api_base: str = typer.Option(
        DEFAULT_API_BASE,
        "--api-base",
        envvar=API_ENVVAR,
        help=API_HELP,
    ),
) -> None:
    """Register or update a provider offer on the StorageRegistry."""
    payload = {"storage_gb": storage_gb, "price_per_gb_eth": price_per_gb_eth}
    client = NodeAPIClient(api_base=api_base)
    try:
        data = client.register_storage(storage_gb, price_per_gb_eth)
    except NodeAPIError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho(data.get("message", "Registration submitted."), fg=typer.colors.GREEN)
    if data.get("registry", {}).get("transaction_hash"):
        typer.echo(f"Tx: {data['registry']['transaction_hash']}")


@registry_app.command("update")
def registry_update(
    api_base: str = typer.Option(
        DEFAULT_API_BASE,
        "--api-base",
        envvar=API_ENVVAR,
        help=API_HELP,
    ),
) -> None:
    """Force a storage update on the registry (same as Refresh Storage)."""
    client = NodeAPIClient(api_base=api_base)
    try:
        data = client.update_registry_storage()
    except NodeAPIError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho("Storage updated in registry.", fg=typer.colors.GREEN)
    typer.echo(f"Registered Storage: {data.get('storage_gb')} GB")
    if data.get("transaction_hash"):
        typer.echo(f"Tx: {data['transaction_hash']}")


@registry_app.command("activate")
def registry_activate(
    api_base: str = typer.Option(
        DEFAULT_API_BASE,
        "--api-base",
        envvar=API_ENVVAR,
        help=API_HELP,
    ),
) -> None:
    """Activate the provider in the StorageRegistry."""
    client = NodeAPIClient(api_base=api_base)
    try:
        data = client.activate_registry()
    except NodeAPIError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho("Provider activated.", fg=typer.colors.GREEN)
    if data.get("transaction_hash"):
        typer.echo(f"Tx: {data['transaction_hash']}")


@registry_app.command("deactivate")
def registry_deactivate(
    api_base: str = typer.Option(
        DEFAULT_API_BASE,
        "--api-base",
        envvar=API_ENVVAR,
        help=API_HELP,
    ),
) -> None:
    """Deactivate the provider in the StorageRegistry."""
    client = NodeAPIClient(api_base=api_base)
    try:
        data = client.deactivate_registry()
    except NodeAPIError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho("Provider deactivated.", fg=typer.colors.YELLOW)
    if data.get("transaction_hash"):
        typer.echo(f"Tx: {data['transaction_hash']}")


@rewards_app.command("payout")
def rewards_payout(
    api_base: str = typer.Option(
        DEFAULT_API_BASE,
        "--api-base",
        envvar=API_ENVVAR,
        help=API_HELP,
    ),
) -> None:
    """Send pending MOXI earnings to the configured payment wallet."""
    client = NodeAPIClient(api_base=api_base)
    try:
        data = client.send_payout()
    except NodeAPIError as exc:
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    amount = data.get("amount_moxi")
    wallet = data.get("payout_wallet")
    if amount is not None:
        typer.secho(
            f"Sent {amount:.4f} MOXI to {wallet}.",
            fg=typer.colors.GREEN,
        )
    else:
        typer.secho("Payout requested.", fg=typer.colors.GREEN)
    if data.get("transaction", {}).get("hash"):
        typer.echo(f"Tx: {data['transaction']['hash']}")


if __name__ == "__main__":
    app()
