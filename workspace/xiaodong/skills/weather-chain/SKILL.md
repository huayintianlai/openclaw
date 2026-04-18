---
name: weather-chain
---

# Weather Chain (Open-Meteo -> Baidu -> tianqi24 -> weather.com.cn)

## Description
Fetch weather for Lanzhou Qilihe with a deterministic fallback chain:
1) Open-Meteo JSON API (preferred)
2) Baidu search "兰州天气" (reliable, rich UI data)
3) tianqi24.com page scrape (fallback)
4) weather.com.cn page scrape (last fallback)
If all fail, return a clear error.

## When to use
When the user asks for Lanzhou/Qilihe weather, daily briefings, or when weather data is needed.

## Tools
- browser
- exec
- tavily_search (NOT preferred for weather - use browser + Baidu)

## Procedure
1. **Open-Meteo JSON API** (preferred, no key):
   - URL: `https://api.open-meteo.com/v1/forecast?latitude=36.06&longitude=103.87&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=Asia/Shanghai`
   - Parse JSON response

2. **Baidu Search** (reliable fallback):
   - Open: `https://www.baidu.com/s?wd=兰州天气`
   - Extract from the weather card:
     - Current temp, feels-like temp
     - Temperature range (min/max)
     - Wind direction and speed
     - Air quality (AQI)
     - Weather condition (sunny/cloudy/rain/snow/sand)
     - Forecast for next few days
   - This source is highly reliable and provides rich data including warnings.

3. **tianqi24.com** (fallback):
   - Open: `https://www.tianqi24.com/qilihe`
   - Extract current + forecast data

4. **weather.com.cn** (last fallback):
   - Open: `https://www.weather.com.cn/weather1d/101160101.shtml`

5. If all fail, report which step failed with error details.

## Output Format
Provide structured output including:
- Current temperature (real + feels-like)
- Temperature range (min ~ max)
- Wind (direction + speed)
- Air quality / AQI
- Weather condition
- Upcoming forecast (2-4 days)
- Any active warnings (sand/dust, cold wave, etc.)
