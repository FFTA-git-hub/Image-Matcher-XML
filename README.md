# FastAPI XML Feed Microservice

This microservice exposes an XML feed from SQL Server table `Indenting_Attr`.

## Endpoints

- `GET /health` - health check
- `GET /xml-feed` - returns XML feed built from `Indenting_Attr`

## XML Fields

`MaterialNumber, Plant, StorageLocation, Quantity, Category, VM, AGAssigned, MRP, Origin, Fabrics, Craft, Zari, BaseColor, BorderColor, BlouseColor, DesignStory, BorderSize, Collection, DiscountPercent, WeightInG, BodyPattern, BodyPatternType, BodyDesElement, ButaSize, BorderTechnique, BorderType, ColorType, BorderMatching, PalluMatching`

## Local run (without Docker)

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
set SQLSERVER_CONNECTION_STRING=DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost,1433;DATABASE=master;UID=sa;PWD=YourStrong!Passw0rd;TrustServerCertificate=yes;
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Run with Docker

```bash
docker build -t fastapi-xml-feed .
docker run --rm -p 8000:8000 --env-file .env.example fastapi-xml-feed
```

## Example XML Response

```xml
<?xml version='1.0' encoding='utf-8'?>
<IndentingFeed>
  <Items>
    <Item>
      <MaterialNumber>1234</MaterialNumber>
      <Plant>1000</Plant>
      <StorageLocation>0001</StorageLocation>
      <Quantity>10</Quantity>
      <!-- ... other fields ... -->
      <PalluMatching>Yes</PalluMatching>
    </Item>
  </Items>
</IndentingFeed>
```
