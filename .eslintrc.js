export default [
  {
    files: ["static/js/**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        window: "readonly",
        document: "readonly",
        console: "readonly",
        jest: "readonly",
        fetch: "readonly"
      }
    },
    rules: {
      // Your custom rules, e.g.:
      "no-unused-vars": "warn",
      "no-console": "off"
    }
  }
];

