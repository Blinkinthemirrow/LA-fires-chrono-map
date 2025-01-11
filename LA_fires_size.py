import pandas as pd
import folium
from folium.plugins import TimestampedGeoJson, FeatureGroupSubGroup
from folium import LayerControl

# Загрузка и подготовка данных
INPUT_FILE = r"C:\Users\Petercoldbeer\Desktop\LA_fires.xlsx"  # Укажите путь к вашему файлу
fires_data = pd.read_excel(INPUT_FILE)

# Оставляем нужные колонки
fires_cleaned = fires_data[['incident_date_created', 'incident_acres_burned', 'incident_longitude', 'incident_latitude']].copy()
fires_cleaned.rename(columns={
    'incident_date_created': 'date',
    'incident_acres_burned': 'acres_burned',
    'incident_longitude': 'longitude',
    'incident_latitude': 'latitude'
}, inplace=True)

# Преобразуем даты
fires_cleaned['date'] = pd.to_datetime(fires_cleaned['date'], errors='coerce')
fires_cleaned.dropna(subset=['longitude', 'latitude', 'acres_burned', 'date'], inplace=True)
fires_cleaned.sort_values(by='date', inplace=True)

# Создание базовой карты
fire_map = folium.Map(location=[fires_cleaned['latitude'].mean(), fires_cleaned['longitude'].mean()], zoom_start=6)

# Создаем группы для каждого года
years = sorted(fires_cleaned['date'].dt.year.unique())
year_layers = {}
for year in years:
    year_layers[year] = folium.FeatureGroup(name=str(year), show=False).add_to(fire_map)
# Функция для выбора цвета в зависимости от года
def get_color_by_year(year):
    color_map = {
        2013: 'blue',
        2014: 'green',
        2015: 'orange',
        2016: 'purple',
        2017: 'red',
        2018: 'brown',
        2019: 'pink',
        2020: 'yellow',
        2021: 'cyan',
        2022: 'magenta',
        2023: 'lime',
        2024: 'navy',
        2025: 'teal',
    }
    return color_map.get(year, 'gray')  # Серый цвет по умолчанию, если года нет в словаре

# Создание слоев по годам
for _, row in fires_cleaned.iterrows():
    year = row['date'].year
    popup_content = f"Date: {row['date'].strftime('%Y-%m-%d')}<br>Acres Burned: {row['acres_burned']}"
    radius = max(min(row['acres_burned'] ** 0.5 / 5, 20), 2)  # Радиус точки
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=radius,
        color=get_color_by_year(year),
        fill=True,
        fill_opacity=0.6,
        popup=popup_content,
    ).add_to(year_layers[year])

# Добавление контроллера слоев
for year in years:
    fire_map.add_child(year_layers[year])

folium.LayerControl(collapsed=False).add_to(fire_map)

# Подготовка данных для TimestampedGeoJson (ползунок)
geojson_features = []
for _, row in fires_cleaned.iterrows():
    start_date = row['date']
    end_date = min(pd.Timestamp(f"{start_date.year}-12-31"), pd.Timestamp("2025-01-10"))  # Устанавливаем последнюю дату
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [row['longitude'], row['latitude']],
        },
        "properties": {
            "times": [start_date.strftime("%Y-%m-%dT%H:%M:%SZ"), end_date.strftime("%Y-%m-%dT%H:%M:%SZ")],  # Интервал отображения
            "popup": f"Date: {start_date.strftime('%Y-%m-%d')}<br>Acres Burned: {row['acres_burned']}",  # Всплывающая подсказка
            "icon": "circle",
            "iconstyle": {
                "color": get_color_by_year(start_date.year),  # Цвет в зависимости от года
                "fillOpacity": 0.6,
                "radius": row['acres_burned']**0.5 / 5,  # Радиус пропорционален площади
            },
        },
    }
    geojson_features.append(feature)

# Добавление TimestampedGeoJson для ползунка
TimestampedGeoJson({
    "type": "FeatureCollection",
    "features": geojson_features,
}, period="P1D", add_last_point=False).add_to(fire_map)

# Сохранение карты
OUTPUT_FILE = "interactive_fire_map_with_years.html"
fire_map.save(OUTPUT_FILE)
print(f"Интерактивная карта создана: {OUTPUT_FILE}")
