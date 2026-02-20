const ctx = document.getElementById("capitalChart").getContext("2d");
const capitalChart = new Chart(ctx, {
    type: "line",
    data: {
        labels: [],
        datasets: [{
            label: "Capital ($)",
            data: [],
            borderColor: "#f59e0b",
            backgroundColor: "rgba(245,158,11,0.1)",
            fill: true, tension: 0.3, pointRadius: 2,
        }],
    },
    options: {
        responsive: true,
        scales: {
            x: { ticks: { color: "#64748b", maxTicksLimit: 10 }, grid: { color: "#1e293b" } },
            y: { ticks: { color: "#64748b", callback: v => "$" + v }, grid: { color: "#1e293b" } },
        },
        plugins: { legend: { display: false } },
    },
});

const $id = id => document.getElementById(id);
const pnlColor = v => v >= 0 ? "text-emerald-400" : "text-red-400";
const pnlSign  = v => v >= 0 ? "+" : "";
function esc(s) { return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
function formatTime(iso) {
    if (!iso) return "-";
    return new Date(iso).toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" });
}

function scoreColor(score) {
    if (score >= 80) return "text-emerald-400 font-bold";
    if (score >= 60) return "text-amber-400 font-semibold";
    return "text-gray-500";
}

function updateUI(data) {
    const running = data.bot_status === "running";
    const badge = $id("bot-status-badge");
    badge.className = "flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium " +
        (running ? "bg-amber-900/50 text-amber-300" : "bg-red-900/50 text-red-300");
    $id("status-dot").className = "w-2 h-2 rounded-full " + (running ? "bg-amber-400 pulse-dot" : "bg-red-400");
    $id("status-text").textContent = running ? "Corriendo" : "Detenido";
    $id("btn-start").classList.toggle("hidden", running);
    $id("btn-stop").classList.toggle("hidden", !running);

    $id("m-capital").textContent    = "$" + data.capital_total.toFixed(2);
    $id("m-disponible").textContent = "$" + data.capital_disponible.toFixed(2);

    const pnlEl = $id("m-pnl");
    pnlEl.textContent = pnlSign(data.pnl) + "$" + data.pnl.toFixed(2);
    pnlEl.className   = "text-xl font-bold mt-1 " + pnlColor(data.pnl);

    const roiEl = $id("m-roi");
    roiEl.textContent = pnlSign(data.roi) + data.roi.toFixed(2) + "%";
    roiEl.className   = "text-xl font-bold mt-1 " + pnlColor(data.roi);

    $id("m-wl").textContent        = data.won + " / " + data.lost;
    $id("m-tracked").textContent   = data.tracked_markets || 0;
    $id("m-highscore").textContent = data.high_score_count || 0;
    $id("m-scans").textContent     = data.scan_count;

    lastPriceUpdateISO = data.last_price_update || null;
    priceThreadAlive   = data.price_thread_alive ?? true;
    updatePriceBadge();
    updateInsights(data.insights);

    const hist = data.capital_history || [];
    capitalChart.data.labels           = hist.map(h => formatTime(h.time));
    capitalChart.data.datasets[0].data = hist.map(h => h.capital);
    capitalChart.update();

    // Open positions
    const openTb  = $id("table-open");
    const openPos = data.open_positions || [];
    if (openPos.length === 0) {
        openTb.innerHTML = "";
        $id("no-open").classList.remove("hidden");
    } else {
        $id("no-open").classList.add("hidden");
        openTb.innerHTML = openPos.map(p => {
            const progress = Math.min(100, Math.max(0,
                (p.current_yes - p.entry_yes) / (p.take_profit - p.entry_yes) * 100
            ));
            const progressColor = progress >= 80 ? "bg-emerald-500" : progress >= 40 ? "bg-amber-500" : "bg-gray-600";
            return `
            <tr class="border-b border-gray-800">
                <td class="q py-2 pr-3">
                    ${esc(p.question)}
                    <div class="mt-1 bg-gray-700 rounded-full h-1" title="${progress.toFixed(0)}% hacia TP">
                        <div class="${progressColor} h-1 rounded-full" style="width:${progress}%"></div>
                    </div>
                </td>
                <td class="num py-2 pr-3 text-amber-300">${(p.entry_yes * 100).toFixed(1)}&cent;</td>
                <td class="num py-2 pr-3 font-semibold">${(p.current_yes * 100).toFixed(1)}&cent;</td>
                <td class="num py-2 pr-3 text-emerald-400">${(p.take_profit * 100).toFixed(1)}&cent;</td>
                <td class="num py-2 pr-3">$${p.allocated.toFixed(2)}</td>
                <td class="num py-2 ${pnlColor(p.pnl)}">${pnlSign(p.pnl)}$${p.pnl.toFixed(2)}</td>
            </tr>`;
        }).join("");
    }

    // Opportunities
    const oppsTb = $id("table-opps");
    const opps   = data.last_opportunities || [];
    if (opps.length === 0) {
        oppsTb.innerHTML = "";
        $id("no-opps").classList.remove("hidden");
    } else {
        $id("no-opps").classList.add("hidden");
        oppsTb.innerHTML = opps.map(o => {
            const inRange  = o.yes_price >= 0.06 && o.yes_price <= 0.12;
            const ready    = inRange && o.score >= 60;
            const rowClass = ready
                ? "border-b border-amber-900/40 bg-amber-900/10"
                : inRange
                    ? "border-b border-gray-700 bg-gray-800/30"
                    : "border-b border-gray-800";
            const zoneColor = o.zone === "A" ? "text-emerald-400" : o.zone === "B" ? "text-amber-400" : "text-gray-500";
            return `
            <tr class="${rowClass}">
                <td class="q py-2 pr-3">${esc(o.question)}</td>
                <td class="num py-2 pr-3 ${inRange ? 'text-amber-300 font-semibold' : ''}">${(o.yes_price * 100).toFixed(1)}&cent;</td>
                <td class="num py-2 pr-3 ${scoreColor(o.score)}">${o.score || 0}</td>
                <td class="num py-2 pr-3 text-xs ${zoneColor}">${o.zone || '-'}</td>
                <td class="num py-2">$${(o.volume || 0).toLocaleString()}</td>
            </tr>`;
        }).join("");
    }

    // Closed trades
    const closedTb = $id("table-closed");
    const closed   = data.closed_positions || [];
    if (closed.length === 0) {
        closedTb.innerHTML = "";
        $id("no-closed").classList.remove("hidden");
    } else {
        $id("no-closed").classList.add("hidden");
        closedTb.innerHTML = closed.map(c => {
            const statusColor =
                c.status === "WON"         ? "text-emerald-400" :
                c.status === "TAKE_PROFIT" ? "text-amber-400"   :
                c.status === "LOST"        ? "text-red-400"     : "text-gray-400";
            return `
            <tr class="border-b border-gray-800">
                <td class="q py-2 pr-3">${esc(c.question)}</td>
                <td class="num py-2 pr-3 text-amber-300">${(c.entry_yes * 100).toFixed(1)}&cent;</td>
                <td class="num py-2 pr-3">$${c.allocated.toFixed(2)}</td>
                <td class="num py-2 pr-3 ${pnlColor(c.pnl)}">${pnlSign(c.pnl)}$${c.pnl.toFixed(2)}</td>
                <td class="num py-2 pr-3 font-semibold ${statusColor}">${c.status}</td>
                <td class="res py-2 pr-3">${esc(c.resolution || "-")}</td>
                <td class="num py-2">${formatTime(c.close_time)}</td>
            </tr>`;
        }).join("");
    }
}

async function fetchStatus() {
    try {
        const res = await fetch("/api/status");
        if (res.ok) updateUI(await res.json());
    } catch(e) { console.error(e); }
}

function winRateBar(rate) {
    const pct   = (rate * 100).toFixed(0);
    const color = rate >= 0.7 ? "bg-emerald-500" : rate >= 0.5 ? "bg-yellow-500" : "bg-red-500";
    return `<div class="flex items-center gap-2">
        <div class="flex-1 bg-gray-700 rounded-full h-1.5">
            <div class="${color} h-1.5 rounded-full" style="width:${pct}%"></div>
        </div>
        <span class="text-xs text-gray-300 w-8 text-right">${pct}%</span>
    </div>`;
}

function updateInsights(ins) {
    const panel = $id("insights-panel");
    if (!ins) { panel.classList.add("hidden"); return; }
    panel.classList.remove("hidden");
    $id("insights-trades").textContent =
        `Win rate: ${(ins.overall_win_rate*100).toFixed(0)}% (${ins.total_trades} trades)`;
    $id("insights-city").innerHTML = ins.by_city.map(c =>
        `<div class="mb-1"><div class="flex justify-between text-xs text-gray-400 mb-0.5">
            <span>${c.city}</span><span class="text-gray-500">${c.trades} trades</span>
        </div>${winRateBar(c.win_rate)}</div>`
    ).join("") || '<p class="text-gray-600 text-xs">Mínimo 2 trades por ciudad</p>';
    $id("insights-hour").innerHTML = ins.by_hour.map(h =>
        `<div class="mb-1"><div class="flex justify-between text-xs text-gray-400 mb-0.5">
            <span>${String(h.hour).padStart(2,"0")}:00 UTC</span><span class="text-gray-500">${h.trades} trades</span>
        </div>${winRateBar(h.win_rate)}</div>`
    ).join("") || '<p class="text-gray-600 text-xs">Mínimo 2 trades por hora</p>';
}

async function startBot() { await fetch("/api/bot/start", {method:"POST"}); fetchStatus(); }
async function stopBot()  { await fetch("/api/bot/stop",  {method:"POST"}); fetchStatus(); }

let lastPriceUpdateISO = null;
let priceThreadAlive   = false;

function updatePriceBadge() {
    const dot = $id("price-badge-dot"), txt = $id("price-badge-txt"), badge = $id("price-badge");
    if (!lastPriceUpdateISO) {
        badge.className = "flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-400";
        dot.className = "w-1.5 h-1.5 rounded-full bg-gray-500";
        txt.textContent = "Precios: sin datos"; return;
    }
    const secAgo = Math.round((Date.now() - new Date(lastPriceUpdateISO).getTime()) / 1000);
    txt.textContent = "Precios: hace " + secAgo + "s";
    if (!priceThreadAlive) {
        badge.className = "flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full bg-red-900/60 text-red-300";
        dot.className = "w-1.5 h-1.5 rounded-full bg-red-400";
    } else if (secAgo < 60) {
        badge.className = "flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full bg-amber-900/60 text-amber-300";
        dot.className = "w-1.5 h-1.5 rounded-full bg-amber-400 pulse-dot";
    } else if (secAgo < 120) {
        badge.className = "flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full bg-yellow-900/60 text-yellow-300";
        dot.className = "w-1.5 h-1.5 rounded-full bg-yellow-400";
    } else {
        badge.className = "flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full bg-red-900/60 text-red-300";
        dot.className = "w-1.5 h-1.5 rounded-full bg-red-400";
    }
}

setInterval(updatePriceBadge, 1000);
fetchStatus();
setInterval(fetchStatus, 5000);
