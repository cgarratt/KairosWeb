# KairosWeb v1.0.0 — release candidate of independent naming

**Product name/version:** KairosWeb v1.0.0. **Source base:** Kairos Web v5.0.1, preserving UI/Forecast and other routes. **Shared schema:** `KAIROS_V5_MASTER` **5.0.0** (unchanged). GitHub/Render deployment is NOT performed by this ZIP.

## Installation

1. Keep `KAIROS_GOOGLE_SHEET_ID`, `KAIROS_GOOGLE_SERVICE_ACCOUNT_JSON`, `KAIROS_SHEETS_CACHE_SECONDS`, `BINANCE_MCP_URL`, `HYPERLIQUID_MCP_URL` and existing web auth variables in Render; never commit credentials.
2. Upload files in this folder into the root of the `KairosWeb` GitHub repository and commit. **Do not delete or rename Google Sheets.**
3. The Web only reads `PUBLICADO` schema 5.0.0; no JSON fallback. BSI SELL remains blocked; TradingBot WATCH. Forecast and BUY/SELL presentations are simulations, not orders.
4. `/health` should show `version: 1.0.0`; `/api/sheets-status` should show a published snapshot and parameter count; `/api/portfolio` should show source `Binance Spot MCP + Google Sheets PUBLICADO` and fresh quote timestamp. `/api/mcp-diagnostics` checks MCPs.
5. This release accepts historical **reconciled** order/fill ledger rows, but blocks OPEN/partial/unverified or duplicate entries and never applies fills twice. No private exchange API reconciliation implied.

## Audit limitations

Only the shared valuation/weights/custody/liquidity/Balancer core calculations have been compared with the GPT contract under identical synthetic quotes. Actual Render HTTP, Google service-account authentication and full engine parity must be checked in production; `Forecast`, `Compras`, `Ventas`, pivot certification, `BSI SELL` and `TradingBot READY` are not claimed equivalent.

Do not upload source ZIP to Render as a running app. Deploy the contents to GitHub and allow Render to build. The latest operational v5.0.1 can stay in production until this v1 is tested.
