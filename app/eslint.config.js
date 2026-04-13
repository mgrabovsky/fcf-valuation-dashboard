import js from "@eslint/js";
import tseslint from "@typescript-eslint/eslint-plugin";
import tsparser from "@typescript-eslint/parser";
import svelte from "eslint-plugin-svelte";
import prettier from "eslint-config-prettier";
import svelteParser from "svelte-eslint-parser";

/** @type {import('eslint').Linter.FlatConfig[]} */
export default [
  {
    ignores: [
      ".svelte-kit/**",
      "build/**",
      "node_modules/**",
      "src/lib/types/dataset.d.ts",
    ],
  },
  js.configs.recommended,
  ...svelte.configs["flat/recommended"],
  {
    files: ["**/*.{js,ts,svelte}"],
    languageOptions: {
      globals: {
        console: "readonly",
        document: "readonly",
        MouseEvent: "readonly",
        process: "readonly",
        SVGSVGElement: "readonly",
        window: "readonly",
      },
    },
  },
  {
    files: ["**/*.ts"],
    languageOptions: {
      parser: tsparser,
    },
    plugins: {
      "@typescript-eslint": tseslint,
    },
    rules: {
      ...tseslint.configs.recommended.rules,
      "no-unused-vars": "off",
    },
  },
  {
    files: ["**/*.svelte"],
    languageOptions: {
      parser: svelteParser,
      parserOptions: {
        parser: tsparser,
      },
    },
    rules: {
      "no-unused-vars": "off",
    },
  },
  prettier,
];
