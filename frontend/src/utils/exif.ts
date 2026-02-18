import EXIF from 'exif-js';

export const parseExifCoords = (
  file: File
): Promise<{ lat: number; lng: number } | null> => {
  return new Promise((resolve) => {
    const reader = new FileReader();

    reader.onload = function () {
      const img = new Image();
      img.src = reader.result as string;

      img.onload = function () {
        try {
          // NB:Explicitly type `this` as any for EXIF callbacks
          EXIF.getData(img as any, function (this: any) {
            try {
              const lat = EXIF.getTag(this, 'GPSLatitude');
              const lng = EXIF.getTag(this, 'GPSLongitude');
              const latRef = EXIF.getTag(this, 'GPSLatitudeRef');
              const lngRef = EXIF.getTag(this, 'GPSLongitudeRef');

              if (lat && lng && latRef && lngRef) {
                resolve({
                  lat: convertDMSToDD(lat, latRef),
                  lng: convertDMSToDD(lng, lngRef),
                });
              } else {
                resolve(null);
              }
            } catch (error) {
              console.warn('Error parsing EXIF GPS data:', error);
              resolve(null);
            }
          });
        } catch (error) {
          console.warn('Error reading EXIF data:', error);
          resolve(null);
        }
      };

      img.onerror = function () {
        console.warn('Error loading image for EXIF parsing');
        resolve(null);
      };
    };

    reader.onerror = function () {
      console.warn('Error reading file for EXIF parsing');
      resolve(null);
    };

    reader.readAsDataURL(file);
  });
};

const convertDMSToDD = (dms: number[], ref: string) => {
  let dd = dms[0] + dms[1] / 60 + dms[2] / 3600;
  if (ref === 'S' || ref === 'W') dd = -dd;
  return dd;
};
