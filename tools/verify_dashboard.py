"""Pemeriksaan browser lokal dan bukti screenshot dashboard."""

import asyncio
import json
from pathlib import Path

import pandas as pd
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "screenshots"
CHROME = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
VIEWS = ["Ringkasan", "Tren", "Gerai", "Produk", "Waktu", "Keputusan", "Data & Audit"]
MARKERS = {
    "Ringkasan": "Perjalanan penjualan", "Tren": "Ukuran tren",
    "Gerai": "Ukuran perbandingan", "Produk": "Peringkat berdasarkan",
    "Waktu": "Rata-rata per hari kalender terpilih", "Keputusan": "Tujuan bisnis",
    "Data & Audit": "Transaksi pada cakupan terpilih",
}


async def ready(page, view="Ringkasan"):
    await page.get_by_text(MARKERS[view], exact=True).first.wait_for(timeout=45000)
    await page.locator('[data-testid="stMetricValue"]').first.wait_for(timeout=45000)
    await page.wait_for_timeout(1000)
    await page.locator('[data-testid="stStatusWidget"]').wait_for(state="hidden", timeout=45000)
    await page.wait_for_function("document.querySelectorAll('[data-stale=\"true\"]').length === 0", timeout=45000)
    assert await page.locator('[data-testid="stException"]').count() == 0


async def main():
    SHOTS.mkdir(exist_ok=True)
    results = {"desktop": {}, "mobile": {}, "downloads": {}}
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=str(CHROME), headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        await page.goto("http://localhost:8501", wait_until="domcontentloaded")
        await ready(page)
        assert "698.812,33" in await page.locator('[data-testid="stMetricValue"]').first.inner_text()
        for index, view in enumerate(VIEWS):
            if index:
                await page.locator('[data-testid="stMain"]').get_by_text(view, exact=True).first.click()
                await ready(page, view)
            await page.locator('[data-testid="stMain"]').evaluate("element => element.scrollTo(0, 0)")
            if view in VIEWS[:5]:
                await page.locator('[data-testid="stPlotlyChart"]').first.wait_for(timeout=45000)
                await page.locator('[data-testid="stPlotlyChart"] .main-svg').first.wait_for(timeout=15000)
            charts = await page.locator('[data-testid="stPlotlyChart"]').count()
            if view in VIEWS[:5]:
                assert charts > 0, f"Grafik kosong: {view}"
            overflow = await page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 2")
            assert not overflow, f"Horizontal overflow: {view}"
            await page.screenshot(path=str(SHOTS / f"dashboard_lengkap_{index + 1}.png"), full_page=True)
            results["desktop"][view] = {"charts": charts, "overflow": overflow}
            print(f"DESKTOP {view}: {charts} grafik", flush=True)
        await page.get_by_role("tab", name="Ekspor ringkasan", exact=True).click()
        async with page.expect_download() as event:
            await page.get_by_role("button", name="Unduh ringkasan Excel").click()
        download = await event.value
        workbook_path = await download.path()
        workbook = pd.ExcelFile(workbook_path)
        assert workbook.sheet_names == ["Indikator", "Bulanan", "Gerai", "Produk", "Kategori", "Jam"]
        indicator = pd.read_excel(workbook_path, sheet_name="Indikator")
        assert abs(indicator.iloc[0]["Total penjualan"] - 698812.33) < .01
        results["downloads"]["excel_sheets"] = workbook.sheet_names
        await page.get_by_role("tab", name="Transaksi", exact=True).click()
        async with page.expect_download() as event:
            await page.get_by_role("button", name="Unduh seluruh transaksi terfilter").click()
        download = await event.value
        csv_path = await download.path()
        exported = pd.read_csv(csv_path)
        assert len(exported) == 149116
        results["downloads"]["csv_rows"] = len(exported)
        await page.locator('[data-testid="stMain"]').get_by_text("Keputusan", exact=True).first.click()
        await ready(page, "Keputusan")
        async with page.expect_download() as event:
            await page.get_by_role("button", name="Unduh laporan keputusan").click()
        download = await event.value
        report_path = Path(await download.path())
        report = report_path.read_text(encoding="utf-8")
        assert "698.812,33" in report and "Simulasi target" in report
        results["downloads"]["decision_report"] = True

        mobile = await browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1,
                                        is_mobile=True, has_touch=True)
        await mobile.goto("http://localhost:8501", wait_until="domcontentloaded")
        await ready(mobile)
        for view in ["Ringkasan", "Produk", "Waktu", "Keputusan"]:
            await mobile.locator('[data-testid="stMain"]').get_by_text(view, exact=True).first.click()
            await ready(mobile, view)
            await mobile.locator('[data-testid="stMain"]').evaluate("element => element.scrollTo(0, 0)")
            overflow = await mobile.evaluate("document.documentElement.scrollWidth > window.innerWidth + 2")
            assert not overflow, f"Mobile horizontal overflow: {view}"
            clipped_metrics = await mobile.locator('[data-testid="stMetricValue"]').evaluate_all(
                "elements => elements.filter(e => e.scrollWidth > e.clientWidth + 2).length"
            )
            assert clipped_metrics == 0, f"Mobile clipped metrics: {view}"
            await mobile.screenshot(path=str(SHOTS / f"dashboard_mobile_{view.lower()}.png"), full_page=True)
            heading = await mobile.locator("h1").bounding_box()
            assert heading and heading["y"] >= 50, f"Mobile title overlaps header: {view}"
            chart = mobile.locator('[data-testid="stPlotlyChart"]').first
            if await chart.count():
                await chart.screenshot(path=str(SHOTS / f"dashboard_mobile_grafik_{view.lower()}.png"))
            results["mobile"][view] = {"overflow": overflow, "clipped_metrics": clipped_metrics}
            print(f"MOBILE {view}: OK", flush=True)
        results["browser_errors"] = errors
        assert not errors, errors
        await browser.close()
    (SHOTS / "verification.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
