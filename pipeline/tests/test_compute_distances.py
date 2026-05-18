import geopandas as gpd
from shapely.geometry import Point
from pipeline.compute_distances import nearest_distance_m


def test_nearest_distance_pythagoras():
    services = gpd.GeoDataFrame({"id": ["s1"]}, geometry=[Point(3000, 4000)], crs="EPSG:3844")
    origin = gpd.GeoSeries([Point(0, 0)], crs="EPSG:3844").iloc[0]
    d, sid = nearest_distance_m(origin, services)
    assert abs(d - 5000) < 1e-6
    assert sid == "s1"
