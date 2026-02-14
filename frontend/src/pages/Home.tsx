
import { PhotoCapture } from "../components/PhotoCapture";
import { AdminMap } from "../components/AdminMap"; //thhis helps  replace MapView with AdminMap or my actual map
import { OfflineBanner } from "../components/offlineBanner";

export const Home = () => {
  return (
    <div className="container mx-auto p-4">
      {/* Offline notification */}
      <OfflineBanner />

      <h1 className="text-2xl font-bold mb-4">Civic Pulse</h1>

      {/* Photo capture/upload component */}
      <PhotoCapture />

      {/* Map showing reports */}
      <AdminMap filters={{ category: "", status: "", date: "" }} />
    </div>
  );
};
