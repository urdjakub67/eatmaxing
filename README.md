# EatMaxing – automatické letáky

Stránka (`index.html`) si při každém otevření načte `deals.json`. Ten každé 2 dny obnoví skript `scrape.py`, který běží v GitHub Actions.

## Nasazení

1. Vytvoř na GitHubu nový repozitář a nahraj všechny soubory z balíčku, včetně složky `.github`.
2. Settings → Pages → Source: Deploy from a branch → `main` / root. Stránka poběží na `https://<jméno>.github.io/<repo>/`.
3. Actions → „Update leaflets“ → Run workflow (první spuštění ručně, vynutí aktualizaci).
4. Otevři log. Když některý obchod hlásí „CHYBA“, uprav v `scrape.py` jeho URL a selektor `card` (F12 v prohlížeči).

## Jak funguje „každé 2 dny“

- Workflow se spouští **každý den** v 5:00 UTC.
- `scrape.py` data obnoví jen tehdy, když jsou starší než 40 hodin, takže aktualizace proběhne přesně každý druhý den (i na přelomu měsíce).
- Pokud se aktualizace nepovede u všech obchodů, zkusí se znovu hned další den. U obchodu, který selže, zůstanou předchozí data.
- Na stránce Potraviny je nahoře vidět čas poslední aktualizace a upozornění, když jsou data starší než 2 dny. Stránka se při návratu do aplikace znovu načte.

Lidl vydává pondělní a čtvrteční leták, ostatní obchody mění letáky podobně týdně, takže 2denní interval stačí.

## Co si ověřit

- URL a selektory ve `scrape.py` jsou odhad a skript nebyl testován proti živým webům.
- Zkontroluj podmínky používání a `robots.txt` webů obchodů, než scraping nasadíš trvale.
- Ceny ve stránce jsou orientační, závazné jsou ceny v prodejně.

## Přihlášení (Google, Apple, e-mail)

Přihlášení běží přes [Supabase](https://supabase.com) (zdarma pro malé projekty). Bez nastavení se tlačítka jen informují, že služba není připojená.

1. Vytvoř projekt v Supabase. V Project Settings → API zkopíruj **Project URL** a **anon public key**.
2. V `index.html` doplň `var AC={url:"…",key:"…"}`.
3. Authentication → Providers: zapni **Email**. Pro **Google** vytvoř OAuth Client ID v Google Cloud Console. Pro **Apple** potřebuješ placený Apple Developer účet.
4. Authentication → URL Configuration: přidej adresu své stránky do Site URL a Redirect URLs.
5. Po přihlášení se profil (údaje, alergie, oblíbené, úspory) synchronizuje mezi zařízeními. Deník jídel zůstává v prohlížeči.
