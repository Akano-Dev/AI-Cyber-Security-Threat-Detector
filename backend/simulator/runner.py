"""Simulator runner — sends events through an AnalyzeClient and prints results."""
import random
import time

from .scenarios import SCENARIOS, pick_mixed


class Simulator:
    def __init__(self, client, delay=(1.0, 2.0), dry_run=False, verbose=True):
        self.client = client
        self.delay = delay          # (min, max) seconds between scenarios
        self.dry_run = dry_run
        self.verbose = verbose
        self._n = 0

    # ── output ────────────────────────────────────────────────────────────
    def _print(self, ev, result):
        if not self.verbose:
            return
        if "error" in result:
            verdict = f"ERROR ({result['error']})"
        else:
            verdict = result.get("verdict", "?")
            ttype = result.get("threat_type")
            if ttype:
                verdict += f" ({ttype})"
        tag = "SAFE" if ev.category == "Safe" else ev.category.upper()
        print(f"[{self._n:>4}] {tag:<18} {ev.source_ip:<16} {ev.payload[:44]:<46} -> {verdict}")

    # ── sending ───────────────────────────────────────────────────────────
    def _send(self, ev):
        if self.dry_run:
            result = {"verdict": "dry-run"}
        else:
            result = self.client.send(ev.payload, ev.user_agent, ev.source_ip)
        self._print(ev, result)
        self._n += 1
        return result

    def run_scenario(self, name, **kwargs):
        """Run one scenario (all of its events) by registry name."""
        fn = SCENARIOS[name]
        for ev in fn(**kwargs):
            self._send(ev)
            if ev.gap:
                time.sleep(ev.gap)

    def run_mixed(self, count=None):
        """Stream weighted scenarios. count=None runs until interrupted."""
        i = 0
        while count is None or i < count:
            self.run_scenario(pick_mixed())
            i += 1
            time.sleep(random.uniform(*self.delay))
