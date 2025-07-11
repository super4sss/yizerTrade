

row = df.iloc[0]
print(CoordinatesConverter.gcj02towgs84(row["纬度"], row["经度"]))
