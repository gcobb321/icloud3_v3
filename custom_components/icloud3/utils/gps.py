


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#           GPS -- DECIMAL TO DEGREES-MINUTES-SECONDS 
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def dd_to_dms(latitude, longitude):
    '''
    Convert (latitude, longitude) from degrees to degree-minute-second

    Return:
        
    '''

    longitude_ew  = "E" if longitude >= 0 else "W"
    longitude_dms = dd_to_dms(longitude)
    latitude_ns   = "N" if latitude >= 0 else "S"
    latitude_dms  = dd_to_dms(latitude)

    return f"{latitude_dms} {latitude_ns}, {longitude_dms} {longitude_ew}"

def decimal_to_dms(decimal):
    degrees = int(decimal)
    minutes = int((decimal - degrees) * 60)
    seconds = (decimal - degrees - minutes / 60) * 3600
    return f"{degrees}°{minutes}'{seconds:.2f}\""


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#       CONVERT STANDARD GPS WGS-84 COORDINATES TO CHINESE GCJ-02 AND BD-08
#
#       XYCONVERT.PY
#       Can Yang, Nov 16, 2020, https://github.com/cyang-kth/xyconvert
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

import numpy as np
import pyproj

a = 6378245.0  # lngg axis
ee = 0.006693421883570923
# f = 0.00335233
# b = a * (1 - f)
# ee = (a*a - b*b)/(a*a)

def assert_xy(xy):
    np.testing.assert_equal(xy.ndim,2,"xy should be two dimension")
    np.testing.assert_equal(xy.shape[1],2,"xy should contain lng,lat only")

def proj(xy, from_srid, to_srid):
    """Project xy coordinates

    Args:
        xy: a 2D numpy array storing coordinates (lng,lat) in shape of (N,2)
        from_srid: an integer representing the input srid
        to_srid: an integer representing the output srid

    Returns:
        a 2D numpy array with projected coordinates (lng,lat) in shape of (N,2)

    """
    assert_xy(xy)
    f_proj = pyproj.Proj(init='epsg:{}'.format(from_srid))
    t_proj = pyproj.Proj(init='epsg:{}'.format(to_srid))
    fx, fy = pyproj.transform(f_proj, t_proj, xy[:,0], xy[:,1])
    return np.dstack([fx, fy])[0]

def __transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * np.sqrt(np.abs(lng))
    ret = ret + (20.0 * np.sin(6.0 * lng * np.pi) + 20.0 * np.sin(2.0 * lng * np.pi)) * 2.0 / 3.0
    ret = ret + (20.0 * np.sin(lat * np.pi) + 40.0 * np.sin(lat / 3.0 * np.pi)) * 2.0 / 3.0
    ret = ret + (160.0 * np.sin(lat / 12.0 * np.pi) + 320.0 * np.sin(lat * np.pi / 30.0)) * 2.0 / 3.0
    return ret

def __transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng +  0.1 * lng * lat + 0.1 * np.sqrt(abs(lng))
    ret = ret + (20.0 * np.sin(6.0 * lng * np.pi) + 20.0 * np.sin(2.0 * lng * np.pi)) * 2.0 / 3.0
    ret = ret + (20.0 * np.sin(lng * np.pi) + 40.0 * np.sin(lng / 3.0 * np.pi)) * 2.0 / 3.0
    ret = ret + (150.0 * np.sin(lng / 12.0 * np.pi) + 300.0 * np.sin(lng * np.pi / 30.0)) * 2.0 / 3.0
    return ret

def gcj_to_wgs(xy):
    """Convert xy coordinates in GCJ02 to WGS84

    Args:
        xy: a 2D numpy array storing GCJ02 coordinates (lng,lat) in shape of (N,2).

    Returns:
        a 2D numpy array storing WGS84 coordinates (lng,lat) in shape of (N,2)

    """
    assert_xy(xy)
    lng = xy[:,0]
    lat = xy[:,1]
    dlat = __transformlat(lng - 105.0, lat - 35.0)
    dlng = __transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * np.pi
    magic = np.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = np.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * np.pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * np.cos(radlat) * np.pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return np.vstack([lng * 2 - mglng, lat * 2 - mglat]).T

def wgs_to_gcj(xy):
    """Convert xy coordinates in wgs84 to GCJ02

    Args:
        xy: a 2D numpy array storing wgs84 coordinates (lng,lat) in shape of (N,2).

    Returns:
        a 2D numpy array storing GCJ02 coordinates (lng,lat) in shape of (N,2).

    """
    assert_xy(xy)
    wgslng = xy[:,0]
    wgslat = xy[:,1]
    dlat = __transformlat(wgslng - 105.0, wgslat - 35.0)
    dlng = __transformlng(wgslng - 105.0, wgslat - 35.0)
    radlat = wgslat/180.0 * np.pi
    magic =  np.sin(radlat)
    magic  = 1 - ee*magic*magic
    sqrtMagic = np.sqrt(magic)
    dlat = (dlat * 180.0)/((a * (1-ee)) / (magic*sqrtMagic) * np.pi)
    dlng = (dlng * 180.0)/(a/sqrtMagic * np.cos(radlat) * np.pi)
    gcjlat = wgslat + dlat
    gcjlng = wgslng + dlng
    return np.vstack([gcjlng, gcjlat]).T

def bd_to_gcj(xy):
    """Convert xy coordinates in BD09 to GCJ02

    Args:
        xy: a 2D numpy array storing BD09 coordinates (lng,lat) in shape of (N,2).

    Returns:
        a 2D numpy array storing GCJ02 coordinates (lng,lat) in shape of (N,2)

    """
    assert_xy(xy)
    bdLon = xy[:,0]
    bdLat = xy[:,1]
    x = bdLon - 0.0065
    y = bdLat - 0.006
    z = np.sqrt(np.power(x,2) + np.power(y,2)) - 0.00002 * np.sin(y * np.pi * 3000.0/180.0)
    theta = np.arctan2(y,x) - 0.000003 * np.cos(x * np.pi *3000.0/180.0)
    gcjLon = z * np.cos(theta)
    gcjLat = z * np.sin(theta)
    return np.vstack([gcjLon, gcjLat]).T

def gcj_to_bd(xy):
    """Convert xy coordinates in GCJ02 to BD09

    Args:
        xy: a 2D numpy array storing GCJ02 coordinates (lng,lat) in shape of (N,2).

    Returns:
        a 2D numpy array storing BD09 coordinates (lng,lat) in shape of (N,2)

    """
    assert_xy(xy)
    gcjLon = xy[:,0]
    gcjLat = xy[:,1]
    z = np.sqrt(np.power(gcjLat,2) + np.power(gcjLon,2)) + 0.00002 * np.sin(gcjLat * np.pi * 3000.0/180.0)
    theta = np.arctan2(gcjLat,gcjLon) + 0.000003 * np.cos(gcjLon * np.pi * 3000.0/180.0)
    bdLon = z * np.cos(theta) + 0.0065
    bdLat = z * np.sin(theta) + 0.006
    return np.vstack([bdLon, bdLat]).T

def bd_to_wgs(xy):
    """Convert xy coordinates in BD09 to WGS84

    Args:
        xy: a 2D numpy array storing BD09 coordinates (lng,lat) in shape of (N,2).

    Returns:
        a 2D numpy array storing WGS84 coordinates (lng,lat) in shape of (N,2)

    """
    assert_xy(xy)
    return gcj_to_wgs(bd_to_gcj(xy))
    
def wgs_to_bd(xy):
    """Convert xy coordinates in WGS84 to BD09

    Args:
        xy: a 2D numpy array storing WGS84 coordinates (lng,lat) in shape of (N,2).

    Returns:
        a 2D numpy array storing BD09 coordinates (lng,lat) in shape of (N,2)

    """
    assert_xy(xy)
    return gcj_to_bd(wgs_to_gcj(xy))
