from flask import Blueprint, request, jsonify
import geoip2.database
import requests
from geopy.geocoders import Nominatim

ip_bp = Blueprint('ip_bp', __name__)

# Load MaxMind DB
reader = geoip2.database.Reader('GeoLite2-City.mmdb')

# Geopy
geolocator = Nominatim(user_agent="cyber_system")


def get_ip_details(ip):
    result = {}
    confidence = "LOW"

    try:
        # 🔹 PRIMARY: MaxMind
        res = reader.city(ip)

        lat = res.location.latitude
        lon = res.location.longitude

        result.update({
            "ip": ip,
            "city": res.city.name,
            "region": res.subdivisions.most_specific.name,
            "country": res.country.name,
            "lat": lat,
            "lon": lon
        })

        confidence = "HIGH"

    except:
        # 🔹 FALLBACK: API
        data = requests.get(f"https://ipinfo.io/{ip}/json").json()
        loc = data.get("loc", "0,0").split(",")

        lat, lon = float(loc[0]), float(loc[1])

        result.update({
            "ip": ip,
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country"),
            "lat": lat,
            "lon": lon
        })

        confidence = "MEDIUM"

    # 🔹 Reverse Geocoding
    try:
        location = geolocator.reverse(f"{lat}, {lon}")
        result["address"] = location.address
    except:
        result["address"] = "Not Available"

    # 🔹 Risk Detection
    risk = "LOW"
    if result.get("country") != "India":
        risk = "HIGH"

    result["risk"] = risk
    result["confidence"] = confidence

    return result


# 🔍 API
@ip_bp.route('/ip', methods=['POST'])
def find_ip():
    data = request.get_json()
    ip = data.get("ip")

    if not ip:
        return jsonify({"error": "Enter IP"}), 400

    result = get_ip_details(ip)
    return jsonify(result)