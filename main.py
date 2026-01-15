from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import httpx
import math
from datetime import datetime
import json

app = FastAPI(title="India Disaster Prediction API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Regional data with coordinates
REGIONS = {
    "Manipur": {"lat": 24.6637, "lon": 93.9063, "disaster_history": {"flood": 8, "heatwave": 3, "earthquake": 2}},
    "Assam": {"lat": 26.2006, "lon": 92.9376, "disaster_history": {"flood": 12, "heatwave": 2, "earthquake": 1}},
    "Kerala": {"lat": 10.8505, "lon": 76.2711, "disaster_history": {"flood": 10, "heatwave": 1, "earthquake": 0}},
    "Uttarakhand": {"lat": 30.0668, "lon": 79.0193, "disaster_history": {"flood": 6, "heatwave": 4, "earthquake": 7}},
    "Bihar": {"lat": 25.5941, "lon": 85.1376, "disaster_history": {"flood": 15, "heatwave": 5, "earthquake": 1}},
    "Rajasthan": {"lat": 27.0238, "lon": 74.2179, "disaster_history": {"flood": 2, "heatwave": 10, "earthquake": 3}},
    "Maharashtra": {"lat": 19.7515, "lon": 75.7139, "disaster_history": {"flood": 5, "heatwave": 6, "earthquake": 2}},
    "Karnataka": {"lat": 15.3173, "lon": 75.7139, "disaster_history": {"flood": 4, "heatwave": 5, "earthquake": 1}},
    "Tamil Nadu": {"lat": 11.1271, "lon": 79.2787, "disaster_history": {"flood": 6, "heatwave": 7, "earthquake": 2}},
    "West Bengal": {"lat": 24.1552, "lon": 88.2195, "disaster_history": {"flood": 10, "heatwave": 3, "earthquake": 1}},
    "Odisha": {"lat": 20.9517, "lon": 85.0985, "disaster_history": {"flood": 8, "heatwave": 4, "earthquake": 1}},
    "Gujarat": {"lat": 22.2587, "lon": 71.1924, "disaster_history": {"flood": 3, "heatwave": 9, "earthquake": 5}},
    "Telangana": {"lat": 15.3173, "lon": 78.4740, "disaster_history": {"flood": 3, "heatwave": 8, "earthquake": 0}},
    "Andhra Pradesh": {"lat": 15.9129, "lon": 79.7400, "disaster_history": {"flood": 4, "heatwave": 8, "earthquake": 1}},
    "Punjab": {"lat": 31.1471, "lon": 75.3412, "disaster_history": {"flood": 2, "heatwave": 6, "earthquake": 1}},
    "Haryana": {"lat": 29.0588, "lon": 77.0745, "disaster_history": {"flood": 1, "heatwave": 8, "earthquake": 0}},
    "Delhi": {"lat": 28.7041, "lon": 77.1025, "disaster_history": {"flood": 1, "heatwave": 10, "earthquake": 0}},
    "Uttar Pradesh": {"lat": 26.8467, "lon": 80.9462, "disaster_history": {"flood": 4, "heatwave": 9, "earthquake": 1}},
    "Jharkhand": {"lat": 23.6102, "lon": 85.2799, "disaster_history": {"flood": 5, "heatwave": 4, "earthquake": 2}},
    "Chhattisgarh": {"lat": 21.2787, "lon": 81.8661, "disaster_history": {"flood": 6, "heatwave": 5, "earthquake": 1}},
}

# Recommendations by disaster type and risk level
RECOMMENDATIONS = {
    "flood": {
        "LOW": [
            "✓ Monitor weather updates regularly",
            "✓ Keep emergency supplies accessible",
            "✓ Know your evacuation routes",
            "✓ Stay informed via local alerts"
        ],
        "MODERATE": [
            "⚠️ Prepare evacuation plan with family",
            "⚠️ Stock food, water, medicines for 3 days",
            "⚠️ Keep documents in waterproof bags",
            "⚠️ Monitor rainfall intensity hourly",
            "⚠️ Avoid travelling to flood-prone areas"
        ],
        "HIGH": [
            "🚨 EVACUATE to higher ground immediately",
            "🚨 Take essential documents & valuables",
            "🚨 Move livestock to safe locations",
            "🚨 Cut off electricity at main switch",
            "🚨 Call emergency: 112",
            "🚨 Do NOT attempt to cross flooded areas"
        ],
        "CRITICAL": [
            "🚨🚨 IMMEDIATE EVACUATION REQUIRED",
            "🚨🚨 Follow official evacuation orders",
            "🚨🚨 Go to nearest shelter/higher ground",
            "🚨🚨 Emergency: 112 | Disaster Mgmt: 1078",
            "🚨🚨 Stay in contact with authorities"
        ]
    },
    "heatwave": {
        "LOW": [
            "✓ Stay hydrated (2-3 liters water daily)",
            "✓ Avoid peak sun hours (11 AM - 3 PM)",
            "✓ Wear light, loose clothing",
            "✓ Check on elderly and children regularly"
        ],
        "MODERATE": [
            "⚠️ Reduce outdoor activities",
            "⚠️ Use air conditioning or stay in cool places",
            "⚠️ Drink electrolyte solutions",
            "⚠️ Don't leave children/pets in vehicles",
            "⚠️ Apply sunscreen (SPF 30+)"
        ],
        "HIGH": [
            "🚨 Stay indoors in cool environment",
            "🚨 Avoid all outdoor activities",
            "🚨 Drink water every 15-20 minutes",
            "🚨 Seek medical help if: dizziness, nausea, weakness",
            "🚨 Help vulnerable people: elderly, homeless, animals"
        ],
        "CRITICAL": [
            "🚨🚨 EXTREME HEAT ALERT - LIFE THREATENING",
            "🚨🚨 Stay in air-conditioned rooms",
            "🚨🚨 Cold water baths/showers every 2-3 hours",
            "🚨🚨 Call 108 (ambulance) for heat stroke symptoms",
            "🚨🚨 Industrial/construction work HALTED"
        ]
    },
    "earthquake": {
        "LOW": [
            "✓ Know safe spots in your building",
            "✓ Keep emergency kit ready",
            "✓ Practice 'Drop, Cover, Hold' drill",
            "✓ Know how to turn off gas/electricity"
        ],
        "MODERATE": [
            "⚠️ Keep emergency kit accessible",
            "⚠️ Reinforce weak structures if possible",
            "⚠️ Have first aid supplies ready",
            "⚠️ Plan meeting point with family",
            "⚠️ Stay alert for aftershocks"
        ],
        "HIGH": [
            "🚨 DROP to hands and knees immediately",
            "🚨 COVER head with hands under sturdy table",
            "🚨 HOLD on until shaking stops",
            "🚨 Stay away from windows, mirrors, heavy objects",
            "🚨 Don't run outside (falling debris)"
        ],
        "CRITICAL": [
            "🚨🚨 MAJOR EARTHQUAKE - LIFE THREATENING",
            "🚨🚨 If inside: DROP-COVER-HOLD",
            "🚨🚨 If outside: Move away from buildings",
            "🚨🚨 If in vehicle: Stay inside with seatbelt",
            "🚨🚨 Emergency: 112 | Prepare for aftershocks"
        ]
    }
}

class PredictionResponse(BaseModel):
    region: str
    disaster_type: str
    risk_percentage: float
    risk_level: str  # LOW, MODERATE, HIGH, CRITICAL
    confidence: float
    temperature: float
    humidity: float
    rainfall: float
    timestamp: str
    recommendations: List[str]
    details: Dict

async def fetch_weather_data(lat: float, lon: float) -> Dict:
    """Fetch weather data from Open-Meteo API"""
    try:
        async with httpx.AsyncClient() as client:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,precipitation",
                "timezone": "Asia/Kolkata"
            }
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            current = data.get("current", {})
            return {
                "temperature": current.get("temperature_2m", 25.0),
                "humidity": current.get("relative_humidity_2m", 60),
                "rainfall": current.get("precipitation", 0),
            }
    except Exception as e:
        print(f"Weather API error: {e}")
        return {"temperature": 25.0, "humidity": 60, "rainfall": 0}

def calculate_risk(region: str, disaster_type: str, weather_data: Dict) -> tuple:
    """Calculate risk percentage based on weather and historical data"""
    
    region_info = REGIONS.get(region, {})
    history = region_info.get("disaster_history", {}).get(disaster_type.lower(), 0)
    
    # Base risk from historical frequency (0-30%)
    historical_risk = min(history * 3, 30)
    
    temp = weather_data.get("temperature", 25)
    humidity = weather_data.get("humidity", 60)
    rainfall = weather_data.get("rainfall", 0)
    
    weather_risk = 0
    
    if disaster_type.lower() == "flood":
        # Rainfall is primary factor (0-50%)
        if rainfall > 100:
            weather_risk = 50
        elif rainfall > 50:
            weather_risk = 35
        elif rainfall > 20:
            weather_risk = 20
        elif rainfall > 10:
            weather_risk = 10
        # Humidity factor (0-20%)
        if humidity > 80:
            weather_risk += min(10, (humidity - 80) / 2)
            
    elif disaster_type.lower() == "heatwave":
        # Temperature is primary factor (0-50%)
        if temp > 45:
            weather_risk = 50
        elif temp > 40:
            weather_risk = 35
        elif temp > 35:
            weather_risk = 20
        elif temp > 30:
            weather_risk = 10
        # Low humidity factor (0-20%)
        if humidity < 30:
            weather_risk += min(15, (30 - humidity) / 2)
    
    elif disaster_type.lower() == "earthquake":
        # Earthquakes less predictable, use historical data more
        weather_risk = 5  # Base seismic activity
    
    # Combined risk
    total_risk = (historical_risk * 0.4) + (weather_risk * 0.6)
    confidence = 0.75 + (history / 20)  # Confidence based on data history
    
    # Determine risk level
    if total_risk >= 75:
        risk_level = "CRITICAL"
    elif total_risk >= 50:
        risk_level = "HIGH"
    elif total_risk >= 25:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"
    
    return total_risk, risk_level, confidence

@app.get("/predict/{region}")
async def predict_single(region: str, disaster_type: str = "flood") -> PredictionResponse:
    """Get prediction for a single region"""
    
    if region not in REGIONS:
        raise HTTPException(status_code=404, detail=f"Region '{region}' not found")
    
    region_data = REGIONS[region]
    weather_data = await fetch_weather_data(region_data["lat"], region_data["lon"])
    risk_percent, risk_level, confidence = calculate_risk(region, disaster_type, weather_data)
    
    recommendations = RECOMMENDATIONS.get(disaster_type.lower(), {}).get(risk_level, [])
    
    return PredictionResponse(
        region=region,
        disaster_type=disaster_type.upper(),
        risk_percentage=round(risk_percent, 2),
        risk_level=risk_level,
        confidence=round(confidence, 3),
        temperature=round(weather_data.get("temperature", 25), 1),
        humidity=weather_data.get("humidity", 60),
        rainfall=round(weather_data.get("rainfall", 0), 2),
        timestamp=datetime.now().isoformat(),
        recommendations=recommendations,
        details={
            "recent_events_in_region": REGIONS[region]["disaster_history"],
            "primary_factors": {
                "flood": ["Rainfall", "Humidity", "Temperature"],
                "heatwave": ["Temperature", "Humidity"],
                "earthquake": ["Seismic Activity"]
            }[disaster_type.lower()]
        }
    )

@app.get("/all")
async def predict_all(disaster_type: str = "flood") -> List[PredictionResponse]:
    """Get predictions for all regions"""
    
    predictions = []
    for region in REGIONS.keys():
        try:
            pred = await predict_single(region, disaster_type)
            predictions.append(pred)
        except Exception as e:
            print(f"Error predicting for {region}: {e}")
    
    return sorted(predictions, key=lambda x: x.risk_percentage, reverse=True)

@app.get("/regions")
async def get_regions() -> Dict:
    """Get list of available regions"""
    return {"regions": list(REGIONS.keys())}

@app.get("/disasters")
async def get_disasters() -> Dict:
    """Get list of available disaster types"""
    return {"disasters": ["flood", "heatwave", "earthquake"]}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)