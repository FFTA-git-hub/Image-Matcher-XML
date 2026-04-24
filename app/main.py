import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
import xml.etree.ElementTree as ET

import pyodbc
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

load_dotenv()

app = FastAPI(title="Indenting XML Feed Service")

COLUMNS: List[str] = [
    "MaterialNumber",
    "Plant",
    "StorageLocation",
    "Quantity",
    "Category",
    "VM",
    "AGAssigned",
    "MRP",
    "Origin",
    "Fabrics",
    "Craft",
    "Zari",
    "BaseColor",
    "BorderColor",
    "BlouseColor",
    "DesignStory",
    "BorderSize",
    "Collection",
    "DiscountPercent",
    "WeightInG",
    "BodyPattern",
    "BodyPatternType",
    "BodyDesElement",
    "ButaSize",
    "BorderTechnique",
    "BorderType",
    "ColorType",
    "BorderMatching",
    "PalluMatching",
]

XML_CACHE_PATH = Path(os.getenv("XML_CACHE_PATH", "./data/indenting_feed.xml"))
REFRESH_INTERVAL_SECONDS = int(os.getenv("XML_REFRESH_INTERVAL_SECONDS", str(6 * 60 * 60)))


def get_connection() -> pyodbc.Connection:
    conn_str = os.getenv(
        "SQLSERVER_CONNECTION_STRING",
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=master;"
        "UID=sa;"
        "PWD=YourStrong!Passw0rd;"
        "TrustServerCertificate=yes;",
    )
    return pyodbc.connect(conn_str)


def fetch_rows() -> List[Dict[str, str]]:
    query = f"SELECT TOP 100 {', '.join(COLUMNS)} FROM Indenting_Attr"

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            records = cursor.fetchall()
            return [
                {
                    COLUMNS[idx]: "" if value is None else str(value)
                    for idx, value in enumerate(row)
                }
                for row in records
            ]
    except pyodbc.Error as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc


def build_xml(rows: List[Dict[str, str]], generated_at: str) -> str:
    root = ET.Element("IndentingFeed")
    root.set("generatedAt", generated_at)
    items = ET.SubElement(root, "Items")

    for row in rows:
        item = ET.SubElement(items, "Item")
        for column in COLUMNS:
            element = ET.SubElement(item, column)
            element.text = row.get(column, "")

    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")


def refresh_xml_cache() -> None:
    rows = fetch_rows()
    generated_at = datetime.now(timezone.utc).isoformat()
    xml_data = build_xml(rows, generated_at)

    XML_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    XML_CACHE_PATH.write_text(xml_data, encoding="utf-8")


async def refresh_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(refresh_xml_cache)
        except Exception as exc:
            # Keep service alive even if one refresh fails.
            print(f"XML refresh failed: {exc}")
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)


@app.on_event("startup")
async def startup_event() -> None:
    if not XML_CACHE_PATH.exists():
        await asyncio.to_thread(refresh_xml_cache)
    asyncio.create_task(refresh_loop())


@app.get("/health")
def health_check() -> Dict[str, str]:
    last_generated = None
    if XML_CACHE_PATH.exists():
        last_generated = datetime.fromtimestamp(
            XML_CACHE_PATH.stat().st_mtime, tz=timezone.utc
        ).isoformat()

    return {
        "status": "ok",
        "cache_file": str(XML_CACHE_PATH),
        "refresh_interval_seconds": str(REFRESH_INTERVAL_SECONDS),
        "last_cache_update_utc": last_generated or "not-generated-yet",
    }


@app.post("/refresh-cache")
def manual_refresh() -> Dict[str, str]:
    refresh_xml_cache()
    return {"status": "refreshed", "cache_file": str(XML_CACHE_PATH)}


@app.get("/xml-feed", response_class=Response)
def get_xml_feed() -> Response:
    if not XML_CACHE_PATH.exists():
        refresh_xml_cache()

    xml_data = XML_CACHE_PATH.read_text(encoding="utf-8")
    return Response(content=xml_data, media_type="application/xml")
