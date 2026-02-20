"""bot.py — V6: Score-Filtered YES (híbrido V3 + V4).

Cycle:
  1. Gamma discovery → candidates (NO 0.88-0.97 = YES 0.03-0.12)
  2. CLOB YES price → record en MarketScorer
  3. Entry gate: YES en 0.06-0.12 AND score >= MIN_ENTRY_SCORE
  4. Open positions para entradas confirmadas
  5. Update prices para posiciones abiertas
  6. Exits: YES >= 0.15 (TP), YES >= 0.99 (WON), NO >= 0.99 (LOST)
  7. Purge stale scorer history
"""

import threading
import logging
from datetime import datetime, timezone

from app.scanner import (
    scan_opportunities, fetch_live_prices, fetch_yes_price_clob,
)
from app.config import (
    MONITOR_INTERVAL, POSITION_SIZE_MIN, POSITION_SIZE_MAX,
    MIN_YES_PRICE, MAX_YES_PRICE, TAKE_PROFIT_YES,
    MIN_ENTRY_SCORE, PRICE_UPDATE_INTERVAL, MAX_POSITIONS,
)

log = logging.getLogger(__name__)

MAX_CLOB_VERIFY = 15


def calc_position_size(capital_disponible, yes_price):
    """0.5%–1.0% de capital_disponible, inversamente proporcional al YES price.

    YES=0.06 → 1.0%  (más barato → más tokens → más upside)
    YES=0.12 → 0.5%  (más caro → menos upside)
    """
    price_range = MAX_YES_PRICE - MIN_YES_PRICE
    if price_range <= 0:
        pct = POSITION_SIZE_MAX
    else:
        t   = (MAX_YES_PRICE - yes_price) / price_range  # invertido: menor precio = más %
        t   = max(0.0, min(1.0, t))
        pct = POSITION_SIZE_MIN + t * (POSITION_SIZE_MAX - POSITION_SIZE_MIN)
    return capital_disponible * pct


class BotRunner:
    def __init__(self, portfolio, scorer):
        self.portfolio     = portfolio
        self.scorer        = scorer
        self._stop_event   = threading.Event()
        self._thread       = None
        self._price_thread = None
        self.scan_count    = 0
        self.last_opportunities = []
        self.status        = "stopped"
        self.last_price_update = None

    @property
    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    # ── Thread management ──────────────────────────────────────────────────────

    def start(self):
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread       = threading.Thread(target=self._run,        daemon=True)
        self._price_thread = threading.Thread(target=self._run_prices, daemon=True)
        self._thread.start()
        self._price_thread.start()
        self.status = "running"

    def stop(self):
        self._stop_event.set()
        self.status = "stopped"

    # ── Main scan loop ─────────────────────────────────────────────────────────

    def _run(self):
        log.info("Bot V6 iniciado — Score-Filtered YES (híbrido V3+V4)")
        while not self._stop_event.is_set():
            try:
                self._cycle()
            except Exception:
                log.exception("Error en ciclo V6")
            self._stop_event.wait(MONITOR_INTERVAL)
        log.info("Bot V6 detenido")

    def _cycle(self):
        self.scan_count += 1
        portfolio = self.portfolio
        scorer    = self.scorer

        # Watchdog
        if self._price_thread is not None and not self._price_thread.is_alive():
            log.warning("Price thread caído — reiniciando")
            self._price_thread = threading.Thread(target=self._run_prices, daemon=True)
            self._price_thread.start()

        # 1. IDs a saltar
        with portfolio.lock:
            existing_ids = set(portfolio.positions.keys())
            closed_ids   = {
                p["condition_id"] for p in portfolio.closed_positions
                if p.get("condition_id")
            }
            existing_ids |= closed_ids

        # 2. Gamma discovery (YES 0.03-0.12)
        opportunities = scan_opportunities(existing_ids)

        # 3. CLOB + scoring
        with portfolio.lock:
            open_count = len(portfolio.positions)
        slots_available = max(0, MAX_POSITIONS - open_count)
        verify_n   = min(len(opportunities), max(slots_available, MAX_CLOB_VERIFY))
        candidates = opportunities[:verify_n]

        verified_opps = []
        display_opps  = []
        clob_ok       = True
        clob_fails    = 0

        for opp in candidates:
            if self._stop_event.is_set():
                return
            yes_tid = opp.get("yes_token_id")
            rt_yes, rt_no = None, None

            if clob_ok and yes_tid:
                rt_yes, rt_no = fetch_yes_price_clob(yes_tid)
                if rt_yes is not None and rt_yes > 0.50:
                    log.debug("CLOB sanity fail YES=%.3f — posible token invertido", rt_yes)
                    rt_yes, rt_no = None, None
                if rt_yes is None:
                    clob_fails += 1
                    if clob_fails >= 5:
                        clob_ok = False

            if rt_yes is None:
                display_opps.append({**opp, "score": 0, "zone": "-"})
                continue

            # Registrar en scorer (siempre, para acumular historial)
            scorer.record(opp["condition_id"], rt_yes, opp["volume"], opp.get("city", ""))

            opp = {**opp, "yes_price": rt_yes, "no_price": rt_no or round(1 - rt_yes, 4)}

            # Calcular score
            sc = scorer.score(opp["condition_id"], opp.get("city", ""))
            score_total = sc["total"]

            display_opps.append({**opp, "score": score_total, "zone": sc["zone"]})

            # Entry gate: precio en rango Y score suficiente
            if not (MIN_YES_PRICE <= rt_yes <= MAX_YES_PRICE):
                log.info(
                    "Skip %s — YES=%.1f¢ fuera de rango",
                    opp["question"][:35], rt_yes * 100,
                )
                continue

            if score_total < MIN_ENTRY_SCORE:
                log.info(
                    "Skip %s — YES=%.1f¢ score=%d (mín %d) zona=%s",
                    opp["question"][:35], rt_yes * 100, score_total, MIN_ENTRY_SCORE, sc["zone"],
                )
                continue

            log.info(
                "Entrada %s — YES=%.1f¢ score=%d zona=%s",
                opp["question"][:35], rt_yes * 100, score_total, sc["zone"],
            )
            verified_opps.append(opp)

        display_opps.extend(opportunities[verify_n:verify_n + (20 - len(display_opps))])

        self.last_opportunities = [
            {
                "question":  o["question"],
                "yes_price": o["yes_price"],
                "no_price":  o["no_price"],
                "volume":    o["volume"],
                "profit_cents": o.get("profit_cents", 0),
                "score":     o.get("score", 0),
                "zone":      o.get("zone", "-"),
            }
            for o in display_opps[:20]
        ]

        # 4. Precios posiciones abiertas
        with portfolio.lock:
            pos_data = [
                (cid, pos.get("yes_token_id"), pos.get("slug"))
                for cid, pos in portfolio.positions.items()
            ]

        price_map     = {}
        clob_ok_pos   = True
        clob_fail_pos = 0
        for cid, yes_tid, slug in pos_data:
            if self._stop_event.is_set():
                return
            yes_p, no_p = None, None
            if clob_ok_pos and yes_tid:
                yes_p, no_p = fetch_yes_price_clob(yes_tid)
                if yes_p is not None and yes_p > 0.50:
                    yes_p, no_p = None, None
                if yes_p is None:
                    clob_fail_pos += 1
                    if clob_fail_pos >= 2:
                        clob_ok_pos = False
            if yes_p is None:
                yes_p, no_p = fetch_live_prices(slug)
            if yes_p is not None and no_p is not None:
                price_map[cid] = (yes_p, no_p)

        # 5. Portfolio operations (con lock)
        with portfolio.lock:
            for opp in verified_opps:
                if not portfolio.can_open_position():
                    break
                city = opp.get("city", "")
                if not portfolio.region_has_capacity(city):
                    log.info("Región llena, skip %s (%s)", city, opp["question"][:30])
                    continue
                amount = calc_position_size(portfolio.capital_disponible, opp["yes_price"])
                if amount >= 0.50:
                    portfolio.open_position(opp, amount)
                    sc = scorer.score(opp["condition_id"], city)
                    log.info(
                        "Abierta YES: %s @ %.1f¢  $%.2f  score=%d zona=%s",
                        opp["question"][:40], opp["yes_price"] * 100,
                        amount, sc["total"], sc["zone"],
                    )

            if price_map:
                portfolio.apply_price_updates(price_map)

            # Auto-liquidar posiciones fuera de rango
            for cid, pos in list(portfolio.positions.items()):
                entry_yes = pos.get("entry_yes", 0.0)
                if not (MIN_YES_PRICE <= entry_yes <= MAX_YES_PRICE):
                    current_yes = pos.get("current_yes", entry_yes)
                    pnl = round(pos["tokens"] * current_yes - pos["allocated"], 2)
                    log.warning(
                        "Auto-liquidar %s — entrada YES=%.1f¢ fuera de rango",
                        pos["question"][:40], entry_yes * 100,
                    )
                    portfolio._close_position(
                        cid, "LIQUIDATED", pnl,
                        resolution=(
                            f"Auto-liquidación: YES entrada {entry_yes*100:.1f}¢ "
                            f"fuera del rango ({MIN_YES_PRICE*100:.0f}–{MAX_YES_PRICE*100:.0f}¢)"
                        ),
                    )

            portfolio.record_capital()

        scorer.purge_old()

    # ── Price update loop ──────────────────────────────────────────────────────

    def _run_prices(self):
        log.info("Price updater V6 iniciado")
        while not self._stop_event.is_set():
            self._stop_event.wait(PRICE_UPDATE_INTERVAL)
            if self._stop_event.is_set():
                break
            try:
                self._refresh_prices()
            except Exception:
                log.exception("Error actualizando precios")
        log.info("Price updater V6 detenido")

    def _refresh_prices(self):
        with self.portfolio.lock:
            pos_data = [
                (cid, pos.get("yes_token_id"), pos.get("slug"))
                for cid, pos in self.portfolio.positions.items()
            ]

        clob_ok       = True
        clob_failures = 0

        for cid, yes_tid, slug in pos_data:
            if self._stop_event.is_set():
                return

            yes_p, no_p = None, None
            source = "Gamma"

            if clob_ok and yes_tid:
                yes_p, no_p = fetch_yes_price_clob(yes_tid)
                if yes_p is not None:
                    if yes_p > 0.50:
                        yes_p, no_p = None, None
                        clob_failures += 1
                    else:
                        source = "CLOB"
                        clob_failures = 0
                else:
                    clob_failures += 1

                if clob_failures >= 2:
                    clob_ok = False
                    log.warning("CLOB no confiable — usando Gamma para posiciones restantes")

            if yes_p is None:
                yes_p, no_p = fetch_live_prices(slug)

            if yes_p is None:
                continue

            with self.portfolio.lock:
                if cid in self.portfolio.positions:
                    pos = self.portfolio.positions[cid]
                    old = pos["current_yes"]
                    pos["current_yes"] = yes_p
                    if abs(yes_p - old) >= 0.001:
                        log.info(
                            "Precio YES [%s] %s: %.4f → %.4f",
                            source, slug[:30] if slug else cid[:20], old, yes_p,
                        )

        self.last_price_update = datetime.now(timezone.utc)
