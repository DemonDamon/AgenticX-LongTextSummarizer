// Register tsconfig paths at runtime for Node.js path alias resolution
const { register } = require('tsconfig-paths');
const { compilerOptions } = require('../../tsconfig.json');

register({
  baseUrl: compilerOptions.baseUrl || '.',
  paths: compilerOptions.paths || {},
});
