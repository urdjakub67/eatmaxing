"""Stahne akce z letaku Albert, Lidl, Billa a zapise deals.json.

Spousti se kazdy den v GitHub Actions, ale data skutecne obnovi jen tehdy, kdyz jsou
starsi nez ~2 dny (nebo kdyz se pusti s --force). Diky tomu probehne aktualizace presne
kazdy druhy den, i na prelomu mesicu. Kdyz jeden obchod selze, zustanou jeho stara data."""
import json, re, sys, pathlib, datetime as dt
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

OUT = pathlib.Path("deals.json")
MAX_AGE = dt.timedelta(hours=40)   # denni cron + prah 40 h = beh kazdy 2. den

# TODO pri prvnim spusteni over URL a selektory v prohlizeci (F12). Weby je casto meni.
STORES = {
    "Albert": {"url": "https://www.albert.cz/akce", "card": "article, [class*='product']"},
    "Lidl":   {"url": "https://www.lidl.cz/c/nabidky/s10008433", "card": "article, [class*='product']"},
    "Billa":  {"url": "https://www.billa.cz/akce", "card": "article, [class*='product']"},
}
EMOJI = {"kuř": "🍗", "maso": "🥩", "mlet": "🥩", "sýr": "🧀", "eidam": "🧀", "mléko": "🥛", "smetan": "🥛",
         "rajč": "🍅", "brambor": "🥔", "cibul": "🧅", "mrkv": "🥕", "vejce": "🥚", "rýž": "🍚",
         "těst": "🍝", "špaget": "🍝", "žampion": "🍄", "chléb": "🍞", "jablk": "🍎", "ryb": "🐟"}
PRICE = re.compile(r"(\d{1,4}(?:[.,]\d{1,2})?)\s*(?:Kč|,-)?")
VALID = re.compile(r"do\s+(\d{1,2})\.\s?(\d{1,2})\.")


def num(s):
    return float(s.replace(",", "."))


def parse_card(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    name = next((l for l in lines if len(l) > 3 and not re.fullmatch(r"[\d\s.,%Kč−-]+", l)), None)
    prices = [num(m.group(1)) for l in lines if re.search(r"Kč|,-", l) for m in PRICE.finditer(l)]
    prices = [p for p in prices if 1 <= p < 5000]
    if not name or len(set(prices)) < 2:
        return None
    emoji = next((e for k, e in EMOJI.items() if k in name.lower()), "🛒")
    deal = {"n": name[:60], "e": emoji, "p": min(prices), "o": max(prices)}
    m = VALID.search(text)
    if m:
        deal["v"] = f"do {int(m.group(1))}.{int(m.group(2))}."
    return deal


def accept_cookies(page):
    try:
        page.get_by_role("button", name=re.compile("Přijmout|Souhlas|Povolit", re.I)).first.click(timeout=3000)
    except Exception:
        pass


def scrape(page, cfg):
    page.goto(cfg["url"], wait_until="networkidle", timeout=60000)
    accept_cookies(page)
    for _ in range(6):                      # dociteni lazy-load produktu
        page.mouse.wheel(0, 3000)
        page.wait_for_timeout(500)
    deals, seen = [], set()
    for el in page.query_selector_all(cfg["card"]):
        d = parse_card(el.inner_text())
        if not d or d["n"] in seen:
            continue
        img = el.query_selector("img")
        src = img and (img.get_attribute("src") or img.get_attribute("data-src"))
        if src and not src.startswith("data:"):
            d["img"] = urljoin(page.url, src)
        seen.add(d["n"])
        deals.append(d)
    return deals[:80]


def main():
    force = "--force" in sys.argv
    data = json.loads(OUT.read_text("utf-8")) if OUT.exists() else {"stores": {}}
    now = dt.datetime.now(dt.timezone.utc)
    last = data.get("run")
    if last and not force and now - dt.datetime.fromisoformat(last) < MAX_AGE:
        print("Data jsou cerstva, preskakuji. (--force vynuti aktualizaci)")
        return
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="cs-CZ", user_agent="Mozilla/5.0 (EatMaxing leaflet bot)")
        for name, cfg in STORES.items():
            old = data["stores"].get(name, {})
            try:
                deals = scrape(page, cfg)
                if len(deals) < 5:
                    raise RuntimeError(f"nasel jen {len(deals)} akci, selektory asi nesedi")
                data["stores"][name] = {"updated": now.isoformat(), "valid": "aktuální", "status": "ok", "deals": deals}
                print(name, "OK", len(deals))
            except Exception as e:
                print(name, "CHYBA:", e)
                old["status"] = "error"
                data["stores"][name] = old or {"status": "error", "deals": []}
        browser.close()
    if any(s.get("status") == "ok" and s.get("updated") == now.isoformat() for s in data["stores"].values()):
        data["run"] = now.isoformat()      # pri uplnem selhani se zkusi znovu hned dalsi den
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), "utf-8")


if __name__ == "__main__":
    main()
