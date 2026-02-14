export interface Report {
  id: string;
  title: string;
  category: string;
  severity: number;
  status: 'Reported' | 'In Progress' | 'Fixed';
  description?: string;
  latitude: number;
  longitude: number;
  imageUrl: string;
  timestamp: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  topReporterScore?: number;
}
