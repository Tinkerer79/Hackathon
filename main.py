from fastapi import FastAPI
import httpx
from datetime import datetime
import os

app = FastAPI(title="🌍 India Disaster Prediction API")

REGIONS = {
    "Andhra Pradesh": {"lat": 15.9129, "lon": 79.7400},
    "Arunachal Pradesh": {"lat": 28.2180, "lon": 94.7278},
    "Assam": {"lat": 26.2006, "lon": 92.9376},
    "Bihar": {"lat": 25.0961, "lon": 85.3131},
    "Chhattisgarh": {"lat": 21.2787, "lon": 81.8661},
    "Goa": {"lat": 15.2993, "lon": 73.8243},
    "Gujarat": {"lat": 22.2587, "lon": 71.1924},
    "Haryana": {"lat": 29.0588, "lon": 77.0745},
    "Himachal Pradesh": {"lat": 31.7433, "lon": 77.1205},
    "Jharkhand": {"lat": 23.6102, "lon": 85.2799},
    "Karnataka": {"lat": 15.3173, "lon": 75.7139},
    "Kerala": {"lat": 10.8505, "lon": 76.2711},
    "Madhya Pradesh": {"lat": 22.9375, "lon": 78.6553},
    "Maharashtra": {"lat": 19.7515, "lon": 75.7139},
    "Manipur": {"lat": 24.6637, "lon": 93.9063},
    "Meghalaya": {"lat": 25.4670, "lon": 91.3662},
    "Mizoram": {"lat": 23.1815, "lon": 92.9789},
    "Nagaland": {"lat": 26.1584, "lon": 94.5624},
    "Odisha": {"lat": 20.9517, "lon": 85.0985},
    "Punjab": {"lat": 31.5497, "lon": 74.3436},
    "Rajasthan": {"lat": 27.0238, "lon": 74.2179},
    "Sikkim": {"lat": 27.5330, "lon": 88.5122},
    "Tamil Nadu": {"lat": 11.1271, "lon": 78.6569},
    "Telangana": {"lat": 18.1124, "lon": 79.0193},
    "Tripura": {"lat": 23.7957, "lon": 91.2868},
    "Uttar Pradesh": {"lat": 26.8467, "lon": 80.9462},
    "Uttarakhand": {"lat": 30.0668, "lon": 79.0193},
    "West Bengal": {"lat": 24.3745, "lon": 88.4631},
    "Andaman & Nicobar": {"lat": 11.7401, "lon": 92.6586},
    "Chandigarh": {"lat": 30.7333, "lon": 76.7794},
    "Dadra & Nagar Haveli": {"lat": 20.2840, "lon": 73.4054},
    "Daman & Diu": {"lat": 20.7276, "lon": 72.8479},
    "Delhi": {"lat": 28.7041, "lon": 77.1025},
    "Jammu & Kashmir": {"lat": 33.7782, "lon": 76.5769},
    "Ladakh": {"lat": 34.2268, "lon": 77.5619},
    "Lakshadweep": {"lat": 12.2381, "lon": 73.2383},
    "Puducherry": {"lat": 12.0657, "lon": 79.8711},
}

@app.get("/")
def root():
    return {"status": "✅ OPERATIONAL", "regions": len(REGIONS)}

@app.get("/health")
def health():
    return {"status": "✅ OPERATIONAL", "regions": len(REGIONS)}

@app.get("/predict/{region}")
async def predict(region: str):
    if region not in REGIONS:
        return {"error": f"Region {region} not found"}
    
    coords = REGIONS[region]
    
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": coords["lat"],
                    "longitude": coords["lon"],
                    "current": "temperature_2m,precipitation",
                    "daily": "precipitation_sum,temperature_2m_max",
                    "timezone": "IST",
                    "forecast_days": 3
                }
            )
            
            if response.status_code != 200:
                return {"error": "Weather API failed"}
            
            weather = response.json()
            current = weather.get("current", {})
            daily = weather.get("daily", {})
            
            temp = current.get("temperature_2m", 25)
            rainfall = sum(daily.get("precipitation_sum", [0,0,0])[:3])
            max_temp = max(daily.get("temperature_2m_max", [temp])[:3])
            
            flood_risk = min(rainfall / 150, 1.0)
            heat_risk = max(0, min((max_temp - 35) / 10, 1.0))
            
            primary = "FLOOD" if flood_risk > heat_risk else "HEATWAVE"
            max_risk = max(flood_risk, heat_risk)
            
            if max_risk > 0.8:
                level = "EXTREME"
            elif max_risk > 0.5:
                level = "HIGH"
            elif max_risk > 0.2:
                level = "MEDIUM"
            else:
                level = "LOW"
            
            return {
                "region": region,
                "timestamp": datetime.now().isoformat(),
                "primary_disaster": primary,
                "risk_level": level,
                "flood_risk": round(flood_risk, 2),
                "heat_risk": round(heat_risk, 2),
                "rainfall_72h_mm": round(rainfall, 1),
                "max_temperature": round(max_temp, 1)
            }
    
    except Exception as e:
        return {"error": str(e)}

@app.get("/all")
async def get_all():
    results = {}
    for region in list(REGIONS.keys())[:10]:
        try:
            result = await predict(region)
            results[region] = result
        except:
            results[region] = {"error": "failed"}
    return {"total": len(results), "predictions": results}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
