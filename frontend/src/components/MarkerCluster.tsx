import { useEffect } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";

import "leaflet.markercluster";

interface Props {
  markers: {
    id: string;
    lat: number;
    lng: number;
    icon: L.Icon;
    onClick: () => void;
  }[];
}

export const MarkerCluster = ({ markers }: Props) => {
  const map = useMap();

  useEffect(() => {
    const clusterGroup = L.markerClusterGroup();

    markers.forEach((m) => {
      const marker = L.marker([m.lat, m.lng], {
        icon: m.icon,
      });

      marker.on("click", m.onClick);
      clusterGroup.addLayer(marker);
    });

    map.addLayer(clusterGroup);

    return () => {
      map.removeLayer(clusterGroup);
    };
  }, [map, markers]);

  return null;
};
