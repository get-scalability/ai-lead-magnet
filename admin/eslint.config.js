import eslint from '@eslint/js';
import importPlugin from 'eslint-plugin-import-x';
import noBarrelFiles from 'eslint-plugin-no-barrel-files';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import reactYouMightNotNeedAnEffect from 'eslint-plugin-react-you-might-not-need-an-effect';
import typescriptSortKeys from 'eslint-plugin-typescript-sort-keys';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  {
    ignores: ['dist/**', 'node_modules/**'],
  },
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      eslint.configs.recommended,
      ...tseslint.configs.recommendedTypeChecked,
      ...tseslint.configs.stylisticTypeChecked,
      reactYouMightNotNeedAnEffect.configs.recommended,
      importPlugin.flatConfigs.recommended,
      importPlugin.flatConfigs.react,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        project: ['./tsconfig.app.json', './tsconfig.node.json'],
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      'typescript-sort-keys': typescriptSortKeys,
      react,
      'no-barrel-files': noBarrelFiles,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      ...react.configs.recommended.rules,
      ...react.configs['jsx-runtime'].rules,
      'import-x/order': [
        'error',
        {
          alphabetize: { order: 'asc' },
          groups: ['external', 'builtin', 'internal', 'sibling', 'parent', 'index'],
          'newlines-between': 'always',
        },
      ],
      'react/prop-types': 'off',
      'no-console': ['warn', { allow: ['error'] }],
      '@typescript-eslint/no-unused-vars': ['error', { ignoreRestSiblings: true }],
      'object-shorthand': 'error',
      'no-nested-ternary': 'error',
      'react/display-name': 'off',
      'react-refresh/only-export-components': 'off',
      '@typescript-eslint/no-misused-promises': [
        'error',
        { checksVoidReturn: false },
      ],
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-unsafe-assignment': 'error',
      '@typescript-eslint/no-unsafe-member-access': 'error',
      '@typescript-eslint/no-unsafe-return': 'error',
      '@typescript-eslint/no-unsafe-call': 'error',
      '@typescript-eslint/no-unsafe-argument': 'error',
      'no-barrel-files/no-barrel-files': 'error',
      'import-x/no-useless-path-segments': ['error', { noUselessIndex: true }],
      'no-magic-numbers': ['error', { ignore: [0, 1, -1, 2] }],
      'max-depth': ['error', { max: 3 }],
      'max-params': ['error', { max: 3 }],
      'import-x/no-cycle': ['error', { maxDepth: 5 }],
      complexity: ['error', { max: 10 }],
      '@typescript-eslint/consistent-type-definitions': ['error', 'type'],
      '@typescript-eslint/consistent-type-imports': [
        'error',
        { prefer: 'type-imports', fixStyle: 'inline-type-imports' },
      ],
      'react-hooks/set-state-in-effect': 'off',
      'no-param-reassign': [
        'error',
        { props: true, ignorePropertyModificationsFor: ['acc', 'state', 'config'] },
      ],
      'max-lines-per-function': ['warn', { max: 100, skipBlankLines: true, skipComments: true }],
    },
    settings: {
      'import-x/extensions': ['.ts', '.tsx', '.js', '.jsx'],
      'import-x/resolver': 'oxc',
      react: { version: '19.1' },
    },
  },
);
