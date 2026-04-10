module.exports = {
  preset: "react-native",
  setupFilesAfterEnv: ["@testing-library/jest-native/extend-expect"],
  transformIgnorePatterns: [
    "node_modules/(?!(" +
      "react-native" +
      "|@react-native" +
      "|@react-navigation" +
      "|react-native-vector-icons" +
      "|react-native-animatable" +
      "|react-native-linear-gradient" +
      "|react-native-reanimated" +
      "|react-native-gesture-handler" +
      "|react-native-screens" +
      "|react-native-safe-area-context" +
      "|react-native-chart-kit" +
      "|react-native-svg" +
      "|react-native-haptic-feedback" +
      "|react-native-fast-image" +
      "|react-native-skeleton-placeholder" +
      "|react-native-modal" +
      "|react-native-device-info" +
      "|react-native-keychain" +
      "|react-native-biometrics" +
      "|react-native-push-notification" +
      "|react-native-background-fetch" +
      "|@react-native-async-storage" +
      "|@react-native-community" +
      "|@react-native-firebase" +
      ")/)",
  ],
  moduleNameMapper: {
    "\\.(jpg|jpeg|png|gif|svg)$": "<rootDir>/__mocks__/fileMock.js",
  },
  collectCoverageFrom: [
    "src/**/*.{js,jsx,ts,tsx}",
    "!src/**/*.d.ts",
    "!src/types/**",
  ],
  coverageThreshold: {
    global: {
      branches: 50,
      functions: 50,
      lines: 50,
      statements: 50,
    },
  },
};
