module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: [
    'dist',
    '.eslintrc.cjs',
    'src/rest/*' // do not lint generated code
  ],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-explicit-any': "off", // No strict typing (annoying especially with React elements and events callbacks)
    "indent": ["error", 2, { "SwitchCase": 1 }],
    "curly": "error", // enforce braces for one-line blocks
    "no-tabs": "error", // enforce no tabs

    "no-console": ["warn", { allow: ["warn", "error", "debug"] }],
    "consistent-return": "warn", // https://eslint.org/docs/latest/rules/consistent-return
    "prefer-arrow-callback": ["warn"],
    "object-curly-spacing": ["warn", "always"], // enforce consistent spacing inside braces

    "func-style": "off", // function expressions or arrow functions are equally valid

    "no-unneeded-ternary": "warn", // disallow unnecessary ternary expressions
    // React rules: https://github.com/jsx-eslint/eslint-plugin-react/blob/master/docs/rules
    "react/prop-types": "off", // PropTypes are not forced
    "react/forbid-prop-types": "off", // all PropTypes are allowed
    "react-hooks/rules-of-hooks": "error", // https://react.dev/reference/rules/rules-of-hooks
    "react-hooks/exhaustive-deps": "warn", // Hooks dependency array, sometimes it's better to ignore
  }
}
