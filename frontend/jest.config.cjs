/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  moduleNameMapper: {
    "\\.(css|less|scss)$": "<rootDir>/src/__mocks__/styleMock.ts",
    "^leaflet$": "<rootDir>/src/__mocks__/leafletMock.ts",
    "^leaflet.markercluster$": "<rootDir>/src/__mocks__/leafletMock.ts",
  },
  transform: {
    "^.+\\.tsx?$": [
      "ts-jest",
      {
        tsconfig: "tsconfig.json",
        diagnostics: false,
      },
    ],
  },
  transformIgnorePatterns: ["/node_modules/(?!(idb|idb-keyval)/)"],
  globals: {
    "import.meta": {
      env: {
        VITE_API_URL: "http://localhost:8000",
      },
    },
  },
};
