console.log(process.env)
module.exports = {
  testEnvironment: "node",
  roots: [".", process.env.APP],
  testMatch: ["**__tests__/**/*.[jt]s?(x)", "**/?(*.)+(spec|test).[tj]s?(x)"],
  testPathIgnorePatterns: ["/node_modules/"],
  setupFilesAfterEnv: ["./jest.setup.js"],
  transform: {
    "^.+\\.tsx?$": "ts-jest"
  }
};